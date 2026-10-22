"""Classify every wave-2 candidate issuer by annual-report form family.

The expansion proposal marks all 3,828 wave-2 listings as
`UNKNOWN_NOT_IN_CONTRACTS` for ADR status. ADR status is still not derivable
from SEC submissions, but the question that decides whether the financial
engine can ingest an issuer is: does it file domestic 10-K statements, or
foreign private issuer 20-F/40-F statements under IFRS?

This script answers that from SEC submissions for each candidate CIK:

* `DOMESTIC_10K` — files 10-K, so the us-gaap engine's taxonomy applies;
* `FOREIGN_PRIVATE_ISSUER_20F` / `_40F` — files a foreign annual report, so its
  statements are IFRS and are not covered by the current engine;
* `INVESTMENT_COMPANY_NCSR` — a registered fund filing N-CSR annual reports, whose
  statements the us-gaap engine does not model;
* `MIXED_ANNUAL_FORMS` — both families in the window, which needs review;
* `NO_ANNUAL_FORM_IN_WINDOW` — no annual report found in the bounded window.

Output is a review table. Nothing is ingested, no proposal row is rewritten, and
ADR status remains explicitly unknown rather than inferred from exchange or
ticker.

The crawl writes a resumable JSONL checkpoint so an interrupted run can continue
without re-fetching; the final artifacts carry each source object's sha256.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "wave2-foreign-status-v1"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SUBMISSIONS_PAGE_URL = "https://data.sec.gov/submissions/{name}"
MAX_ARCHIVE_PAGES = 2
ANNUAL_FORMS = ("10-K", "20-F", "40-F", "N-CSR")
COLUMNS = (
    "ticker",
    "cik",
    "company",
    "exchange",
    "annual_forms",
    "foreign_status",
    "engine_taxonomy",
    "adr_status",
)


class CrawlError(Exception):
    pass


def classify(forms: list[str]) -> tuple[str, str]:
    present = {form for form in ANNUAL_FORMS if form in forms}
    if not present:
        return "NO_ANNUAL_FORM_IN_WINDOW", "UNKNOWN_NO_ANNUAL_REPORT"
    operating = present & {"10-K", "20-F", "40-F"}
    if not operating:
        # Closed-end funds and other registered investment companies file annual
        # N-CSR reports instead of a 10-K; the engine has no schedule for them.
        return "INVESTMENT_COMPANY_NCSR", "INVESTMENT_COMPANY_NOT_MODELLED"
    if "10-K" in operating and operating & {"20-F", "40-F"}:
        return "MIXED_ANNUAL_FORMS", "REVIEW_MIXED_TAXONOMY"
    if "10-K" in operating:
        return "DOMESTIC_10K", "US_GAAP_COMPATIBLE"
    if "20-F" in operating and "40-F" in operating:
        return "FOREIGN_PRIVATE_ISSUER_MIXED", "IFRS_NOT_COVERED"
    if "20-F" in operating:
        return "FOREIGN_PRIVATE_ISSUER_20F", "IFRS_NOT_COVERED"
    return "FOREIGN_PRIVATE_ISSUER_40F", "IFRS_NOT_COVERED"


def form_counts(pages: list[dict], limit: int = 4000) -> dict:
    counts = {form: 0 for form in ANNUAL_FORMS}
    seen = 0
    for page in pages:
        recent = page.get("filings", {}).get("recent", {})
        forms = recent.get("form") or []
        for form in forms:
            seen += 1
            if form in counts:
                counts[form] += 1
            if seen >= limit:
                return counts
    return counts


def fetch(cik: str, user_agent: str, *, attempts: int = 4) -> tuple[list[dict], list[dict], str]:
    pages: list[dict] = []
    receipts: list[dict] = []
    url = SUBMISSIONS_URL.format(cik=cik)
    response = _get(url, user_agent, attempts)
    page = json.loads(response)
    pages.append(page)
    receipts.append({"url": url, "sha256": hashlib.sha256(response).hexdigest(), "bytes": len(response)})
    for entry in (page.get("filings", {}).get("files") or [])[:MAX_ARCHIVE_PAGES]:
        if any(counts for counts in form_counts(pages).values()):
            break
        name = entry.get("name")
        if not name:
            continue
        page_url = SUBMISSIONS_PAGE_URL.format(name=name)
        raw = _get(page_url, user_agent, attempts)
        pages.append(json.loads(raw))
        receipts.append({"url": page_url, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
    return pages, receipts, pages[0].get("name", "")


def _get(url: str, user_agent: str, attempts: int) -> bytes:
    delay = 1.0
    for attempt in range(attempts):
        request = urllib.request.Request(url, headers={"User-Agent": user_agent})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code in (403, 404):
                raise CrawlError(f"{url}: HTTP {error.code}") from error
            if error.code not in (429, 500, 502, 503, 504) or attempt == attempts - 1:
                raise CrawlError(f"{url}: HTTP {error.code}") from error
        except (urllib.error.URLError, TimeoutError) as error:
            if attempt == attempts - 1:
                raise CrawlError(f"{url}: {error}") from error
        time.sleep(delay)
        delay *= 2
    raise CrawlError(f"{url}: retries exhausted")


def read_checked(path: Path) -> dict[str, dict]:
    done: dict[str, dict] = {}
    if not path.exists():
        return done
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        done[row["cik"]] = row
    return done


def candidates(path: Path) -> list[dict]:
    rows = []
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["tier"] != "TIER_2_WAVE":
                continue
            rows.append(row)
    return rows


def crawl(rows: list[dict], *, checkpoint: Path, user_agent: str, sleep: float) -> list[dict]:
    done = read_checked(checkpoint)
    unique_ciks = sorted({row["cik"] for row in rows})
    pending = [cik for cik in unique_ciks if cik not in done]
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    with checkpoint.open("a") as handle:
        for index, cik in enumerate(pending, 1):
            try:
                pages, receipts, entity_name = fetch(cik, user_agent)
            except CrawlError as error:
                # One unreadable issuer must not discard the other 3,600.
                record = {
                    "cik": cik,
                    "entity_name": "",
                    "annual_forms": {form: 0 for form in ANNUAL_FORMS},
                    "foreign_status": "SOURCE_UNAVAILABLE",
                    "engine_taxonomy": "UNKNOWN",
                    "sources": [],
                    "error": str(error),
                    "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }
            else:
                counts = form_counts(pages)
                forms = [form for form, count in counts.items() if count]
                status, taxonomy = classify(forms)
                record = {
                    "cik": cik,
                    "entity_name": entity_name,
                    "annual_forms": counts,
                    "foreign_status": status,
                    "engine_taxonomy": taxonomy,
                    "sources": receipts,
                    "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }
            done[cik] = record
            handle.write(json.dumps(record) + "\n")
            handle.flush()
            if index % 100 == 0:
                print(json.dumps({"fetched": index, "pending": len(pending)}), flush=True)
            time.sleep(sleep)
    return [done[cik] for cik in unique_ciks]


def render_markdown(document: dict) -> str:
    summary = document["summary"]
    lines = [
        "# Wave-2 foreign-status classification — " + document["observed_at"],
        "",
        "Read-only classification of the wave-2 candidates by annual-report form family, "
        "from SEC submissions. ADR status remains unknown: a foreign private issuer can "
        "be an ADR or a direct listing, and submissions alone cannot tell them apart.",
        "",
        "| Foreign status | Listings | Engine taxonomy |",
        "| --- | --- | --- |",
    ]
    for status, count in sorted(summary["by_status"].items(), key=lambda item: -item[1]):
        taxonomy = summary["taxonomy_by_status"].get(status, "")
        lines.append(f"| {status} | {count} | {taxonomy} |")
    lines += [
        "",
        f"{summary['issuers']} issuers / {summary['listings']} listings classified; "
        f"{summary['errors']} could not be read.",
        "",
        "## What this changes for the wave",
        "",
        f"- {summary['by_status'].get('DOMESTIC_10K', 0)} listings file 10-K statements and are "
        "taxonomy-compatible with the current engine.",
        f"- {summary['ifrs_listings']} listings file 20-F/40-F statements under IFRS; ingesting "
        "them would produce no us-gaap facts, so they need a separate pipeline or exclusion.",
        f"- {summary['investment_company_listings']} listings are registered investment companies "
        "filing N-CSR reports; the engine models no fund schedule, so they are out of scope.",
        f"- {summary['by_status'].get('MIXED_ANNUAL_FORMS', 0)} listings show both families and "
        "need review before either branch is trusted.",
        f"- {summary['by_status'].get('NO_ANNUAL_FORM_IN_WINDOW', 0)} listings have no annual report "
        "in the window. The sample starts with " + ", ".join(summary["no_annual_examples"])
        + "; these are mostly recently listed SPACs and new registrants that should re-enter "
        "the wave after their first annual report.",
        "- ADR status is still `UNKNOWN_NOT_IN_CONTRACTS` for every row; this classification "
        "does not fill that column and must not be used as if it did.",
        "",
        "## Method and limits",
        "",
        "- Annual forms are counted in the newest 4,000 filings plus at most two older archive pages.",
        "- A listing is classified by its issuer CIK; two listings of one issuer share the result.",
        "- No exchange or ticker syntax is used to infer foreign status.",
        "- Each issuer row in the JSON carries the URL and sha256 of the submissions objects read.",
        "- No proposal row, release, packet, or pointer was modified.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal", required=True, type=Path, help="universe-expansion CSV")
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    parser.add_argument("--out-csv", required=True, type=Path)
    parser.add_argument("--limit", type=int, default=0, help="fetch at most N pending issuers")
    parser.add_argument("--sleep", type=float, default=0.13, help="delay between requests, seconds")
    parser.add_argument(
        "--user-agent", default="Financial System wave2 classification scott@example.com"
    )
    parser.add_argument("--observed-at", default=date.today().isoformat())
    args = parser.parse_args(argv)

    rows = candidates(args.proposal)
    if not rows:
        raise SystemExit("no TIER_2_WAVE rows in the proposal")
    if args.limit:
        unique = sorted({row["cik"] for row in rows})
        done = read_checked(args.checkpoint)
        allowed = set(unique[: args.limit])
        rows = [row for row in rows if row["cik"] in allowed or row["cik"] in done]

    records = crawl(rows, checkpoint=args.checkpoint, user_agent=args.user_agent, sleep=args.sleep)
    by_cik = {record["cik"]: record for record in records}

    listings = []
    errors = 0
    for row in rows:
        record = by_cik.get(row["cik"])
        if record is None:
            errors += 1
            continue
        if record.get("error"):
            errors += 1
        listings.append(
            {
                "ticker": row["ticker"],
                "cik": row["cik"],
                "company": row["company"],
                "exchange": row["exchange"],
                "annual_forms": record["annual_forms"],
                "foreign_status": record["foreign_status"],
                "engine_taxonomy": record["engine_taxonomy"],
                "adr_status": "UNKNOWN_NOT_IN_CONTRACTS",
                "sources": record["sources"],
            }
        )
    by_status: dict[str, int] = {}
    taxonomy_by_status: dict[str, str] = {}
    for listing in listings:
        by_status[listing["foreign_status"]] = by_status.get(listing["foreign_status"], 0) + 1
        taxonomy_by_status[listing["foreign_status"]] = listing["engine_taxonomy"]
    ifrs = sum(
        count
        for status, count in by_status.items()
        if status.startswith("FOREIGN_PRIVATE_ISSUER")
    )
    document = {
        "schema_version": SCHEMA_VERSION,
        "observed_at": args.observed_at,
        "summary": {
            "issuers": len(by_cik),
            "listings": len(listings),
            "errors": errors,
            "by_status": by_status,
            "taxonomy_by_status": taxonomy_by_status,
            "ifrs_listings": ifrs,
            "investment_company_listings": by_status.get("INVESTMENT_COMPANY_NCSR", 0),
            "no_annual_examples": [
                listing["ticker"]
                for listing in listings
                if listing["foreign_status"] == "NO_ANNUAL_FORM_IN_WINDOW"
            ][:5],
        },
        "listings": listings,
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(document, indent=2) + "\n")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(render_markdown(document))
    with args.out_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(COLUMNS))
        writer.writeheader()
        for listing in listings:
            writer.writerow({column: listing[column] for column in COLUMNS})
    print(json.dumps(document["summary"], sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
