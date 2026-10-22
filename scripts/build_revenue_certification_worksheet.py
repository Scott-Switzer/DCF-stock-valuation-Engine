"""Build a review worksheet for certifying bank and insurer revenue definitions.

The engine quarantines revenue for any issuer whose taxonomy shows insurance or
lending evidence, so GE, ALL, C, GS and JPM currently report no revenue. Lifting
that gate is an accounting decision, not an engineering one. This script assembles
the evidence that decision needs:

* every candidate revenue concept's 10-K value for the last three fiscal years,
  with the accession and filing date that reported it;
* conflicts where two concepts or two filings disagree for the same period;
* the lending/insurance evidence tags that are present in each period, so a
  historical tag cannot silently certify a present statement family;
* a proposed mapping per issuer, marked uncertified, and the exact statement the
  accounting owner would need to sign.

It changes no policy, release, or dataset. Raw companyfacts payloads are not
stored: each issuer's compact extract carries the sha256 of the source object it
came from.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SCHEMA_VERSION = "revenue-certification-worksheet-v1"
COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
ISSUERS = (
    ("0000040545", "GE", "GENERAL ELECTRIC COMPANY"),
    ("0000899051", "ALL", "ALLSTATE CORP"),
    ("0000831001", "C", "CITIGROUP INC"),
    ("0000886982", "GS", "THE GOLDMAN SACHS GROUP, INC."),
    ("0000019617", "JPM", "JPMORGAN CHASE & CO"),
)
REVENUE_CONCEPTS = (
    "Revenues",
    "RevenuesNetOfInterestExpense",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "SalesRevenueNet",
)
COMPONENT_TAGS = (
    "PremiumsEarnedNet",
    "InterestAndDividendIncomeOperating",
    "PolicyholderBenefitsAndClaimsIncurredNet",
    "LoansAndLeasesReceivableNetReportedAmount",
)
EVIDENCE_TAGS = (
    "PremiumsEarnedNet",
    "InterestAndDividendIncomeOperating",
    "PolicyholderBenefitsAndClaimsIncurredNet",
    "LoansAndLeasesReceivableNetReportedAmount",
)
MIN_DURATION_DAYS = 330
MAX_DURATION_DAYS = 400
YEAR_WINDOW = 10


class WorksheetError(Exception):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def duration_days(fact: dict) -> int | None:
    start, end = fact.get("start"), fact.get("end")
    if not start or not end:
        return None
    return (date.fromisoformat(end) - date.fromisoformat(start)).days


def annual_facts(payload: dict, tag: str, *, since: str) -> list[dict]:
    """Return 10-K facts for a tag with a fiscal-year duration, deduplicated."""
    units = payload.get("facts", {}).get("us-gaap", {}).get(tag, {}).get("units", {})
    rows = []
    for fact in units.get("USD", []):
        if fact.get("form") != "10-K" or fact.get("fp") != "FY":
            continue
        days = duration_days(fact)
        if days is None or not (MIN_DURATION_DAYS <= days <= MAX_DURATION_DAYS):
            continue
        if str(fact.get("end", "")) < since:
            continue
        rows.append(
            {
                "end": fact["end"],
                "start": fact.get("start", ""),
                "value": str(fact.get("val")),
                "accession": fact.get("accn", ""),
                "filed": fact.get("filed", ""),
                "fy": fact.get("fy"),
                "fp": fact.get("fp"),
                "form": fact.get("form", ""),
                "frame": fact.get("frame", ""),
            }
        )
    return rows


def reduce_years(facts: list[dict]) -> dict[str, list[dict]]:
    by_end: dict[str, list[dict]] = {}
    for fact in facts:
        by_end.setdefault(fact["end"], []).append(fact)
    return by_end


def pick_year_variants(facts: list[dict]) -> tuple[dict | None, list[dict], list[str]]:
    """Return (latest-filed fact, all variants, conflict descriptions) for one period."""
    if not facts:
        return None, [], []
    ordered = sorted(facts, key=lambda row: (row["filed"], row["accession"]))
    latest = ordered[-1]
    variants = []
    seen = set()
    for row in ordered:
        key = (row["value"], row["accession"])
        if key in seen:
            continue
        seen.add(key)
        variants.append(row)
    distinct = {row["value"] for row in ordered}
    conflicts = []
    if len(distinct) > 1:
        reported = "; ".join(
            "{} filed {} ({} {})".format(
                row["value"], row["filed"], row.get("form", "10-K"), row["accession"]
            )
            for row in ordered
        )
        conflicts.append(
            "same period end {} has {} distinct values: {}".format(
                latest["end"], len(distinct), reported
            )
        )
    return latest, variants, conflicts


def build_extract(cik: str, payload: dict) -> dict:
    entity = payload.get("entityName", "")
    since = (date.today() - timedelta(days=365 * YEAR_WINDOW)).isoformat()
    concepts = {}
    for tag in REVENUE_CONCEPTS + COMPONENT_TAGS:
        concepts[tag] = annual_facts(payload, tag, since=since)
    return {"cik": cik, "entity_name": entity, "concepts": concepts}


def propose_mapping(extract: dict, years: list[str], current_evidence: list[str]) -> dict:
    """Propose a family mapping from the latest period's reported concepts.

    The proposal is deliberately mechanical: it names a primary concept and a
    component, records which alternative concepts also carry a value, and stays
    uncertified. It never decides that a historical tag describes today's
    statement family.
    """
    latest = years[-1] if years else None
    values = {}
    if latest:
        for tag in REVENUE_CONCEPTS + COMPONENT_TAGS:
            latest_fact, _, _ = pick_year_variants(
                [row for row in extract["concepts"][tag] if row["end"] == latest]
            )
            if latest_fact:
                values[tag] = latest_fact["value"]
    if "RevenuesNetOfInterestExpense" in values:
        family = "BANK_NET_REVENUE"
        primary = "RevenuesNetOfInterestExpense"
        component = "InterestAndDividendIncomeOperating"
        rationale = (
            "The issuer reports revenue net of interest expense, which is the total "
            "its income statement presents for a bank."
        )
    elif "PremiumsEarnedNet" in values and "Revenues" in values:
        family = "INSURER_TOTAL_REVENUE"
        primary = "Revenues"
        component = "PremiumsEarnedNet"
        rationale = (
            "The issuer reports both total Revenues and premiums earned; the total is "
            "the income-statement revenue line, premiums are a component."
        )
    elif "InterestAndDividendIncomeOperating" in current_evidence and "Revenues" in values:
        family = "BANK_TOTAL_REVENUE"
        primary = "Revenues"
        component = "InterestAndDividendIncomeOperating"
        rationale = (
            "The issuer shows current lending evidence but files total Revenues rather "
            "than revenue net of interest expense; the total is the income-statement line."
        )
    else:
        family = "GENERAL_TOTAL_REVENUE"
        primary = "Revenues"
        component = None
        rationale = "Only the total Revenues concept carries an annual 10-K value."
    candidates = sorted(tag for tag in values if tag in REVENUE_CONCEPTS)
    return {
        "statement_family": family,
        "primary_concept": primary,
        "component_concept": component,
        "rationale": rationale,
        "candidate_concepts_with_values": candidates,
        "candidate_values": values,
        "latest_period": latest,
        "latest_primary_value": values.get(primary),
        "status": "PROPOSED_NOT_CERTIFIED",
        "certification_required": (
            "Accounting owner must confirm that {} is the total revenue line the "
            "issuer's income statement presents for {}, and whether {} remains a "
            "component only.".format(primary, latest, component or "any component tag")
        ),
        "single_candidate": len(candidates) == 1,
    }


def build_issuer(ticker: str, cik: str, expected_name: str, extract: dict) -> dict:
    per_period = []
    all_ends = sorted(
        {row["end"] for tag in REVENUE_CONCEPTS for row in extract["concepts"][tag]}
    )
    for end in all_ends[-3:]:
        row = {"period_end": end, "concepts": {}, "conflicts": []}
        for tag in REVENUE_CONCEPTS:
            latest, variants, conflicts = pick_year_variants(
                [item for item in extract["concepts"][tag] if item["end"] == end]
            )
            row["conflicts"].extend(conflicts)
            if latest:
                row["concepts"][tag] = {
                    "value": latest["value"],
                    "accession": latest["accession"],
                    "filed": latest["filed"],
                    "variants": len(variants),
                }
        row["candidate_count"] = len(row["concepts"])
        per_period.append(row)

    evidence = {}
    for tag in EVIDENCE_TAGS:
        facts = extract["concepts"][tag]
        if not facts:
            evidence[tag] = {"present": False}
            continue
        latest = max(facts, key=lambda item: (item["end"], item["filed"]))
        evidence[tag] = {
            "present": True,
            "latest_period_end": latest["end"],
            "latest_accession": latest["accession"],
            "latest_filed": latest["filed"],
            "periods": sorted({item["end"] for item in facts})[-3:],
        }

    years = [row["period_end"] for row in per_period]
    current_evidence = [
        tag
        for tag, detail in evidence.items()
        if detail.get("present") and detail.get("latest_period_end") == (years[-1] if years else None)
    ]
    mapping = propose_mapping(extract, years, current_evidence)
    historical_only = [
        tag
        for tag, detail in evidence.items()
        if detail.get("present") and detail.get("latest_period_end") != (years[-1] if years else None)
    ]
    return {
        "ticker": ticker,
        "cik": cik,
        "entity_name": extract["entity_name"],
        "expected_name": expected_name,
        "name_matches": extract["entity_name"].strip().lower() == expected_name.strip().lower(),
        "per_period": per_period,
        "evidence_tags": evidence,
        "evidence_in_latest_period": current_evidence,
        "evidence_historical_only": historical_only,
        "proposed_mapping": mapping,
        "open_questions": open_questions(
            mapping,
            current_evidence,
            historical_only,
            has_conflicts=any(row["conflicts"] for row in per_period),
        ),
    }


def open_questions(
    mapping: dict, current: list[str], historical: list[str], *, has_conflicts: bool
) -> list[str]:
    questions = []
    if has_conflicts:
        questions.append(
            "Two filings report different values for the same fiscal period (restatement "
            "or reclassification); confirm which value is the income-statement total as "
            "presented, and whether the engine should use the latest filing."
        )
    if not mapping["single_candidate"]:
        questions.append(
            "Several revenue concepts carry a value for {}; confirm which is the "
            "income-statement total.".format(mapping["latest_period"])
        )
    if (
        mapping["statement_family"] == "BANK_NET_REVENUE"
        and "Revenues" in mapping["candidate_concepts_with_values"]
        and mapping["candidate_values"].get("Revenues")
        != mapping["candidate_values"].get("RevenuesNetOfInterestExpense")
    ):
        questions.append(
            "The issuer files both Revenues and RevenuesNetOfInterestExpense and the "
            "values differ; the income-statement total must be identified explicitly "
            "rather than defaulted to either concept."
        )
    if historical and not current:
        questions.append(
            "Financial-statement evidence exists only in earlier periods ({}); confirm "
            "whether the issuer's present statement family is still financial.".format(
                ", ".join(historical)
            )
        )
    if not current:
        questions.append(
            "No insurance or lending tag appears in the latest 10-K fact set; the "
            "blanket quarantine may be stale for this issuer."
        )
    return questions


class FactsCache:
    def __init__(self, root: Path, *, refresh: bool, user_agent: str) -> None:
        self.root = root
        self.refresh = refresh
        self.user_agent = user_agent
        self._last = 0.0

    def _fetch(self, url: str) -> bytes:
        wait = 0.25 - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read()
        self._last = time.monotonic()
        return body

    def extract(self, cik: str) -> dict:
        path = self.root / "companyfacts" / f"CIK{cik}.json"
        if path.exists() and not self.refresh:
            stored = json.loads(path.read_text())
            if not stored.get("receipt", {}).get("sha256"):
                raise WorksheetError(f"cached extract for {cik} has no source receipt")
            return stored
        url = COMPANY_FACTS_URL.format(cik=cik)
        body = self._fetch(url)
        payload = json.loads(body)
        extract = build_extract(cik, payload)
        extract["receipt"] = {
            "url": url,
            "sha256": sha256_bytes(body),
            "bytes": len(body),
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source_entity_name": payload.get("entityName", ""),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(extract, indent=2) + "\n")
        return extract


def render_markdown(document: dict) -> str:
    lines = [
        "# Bank and insurer revenue certification worksheet — " + document["observed_at"],
        "",
        "Read-only evidence for the R2 decision. No policy, release or dataset changed; "
        "revenue stays quarantined for these issuers until an accounting owner signs the mapping.",
        "",
        "Source: SEC XBRL `companyfacts` per issuer, 10-K annual facts only. Each issuer's "
        "source sha256 is in the JSON worksheet.",
        "",
    ]
    for issuer in document["issuers"]:
        mapping = issuer["proposed_mapping"]
        lines += [
            f"## {issuer['ticker']} — {issuer['entity_name']} (CIK {issuer['cik']})",
            "",
            f"Proposed family: **{mapping['statement_family']}** — primary "
            f"`{mapping['primary_concept']}`"
            + (f", component `{mapping['component_concept']}`" if mapping["component_concept"] else "")
            + f". Status: **{mapping['status']}**.",
            "",
            "| Period end | " + " | ".join(REVENUE_CONCEPTS) + " |",
            "| --- | " + " | ".join("---" for _ in REVENUE_CONCEPTS) + " |",
        ]
        for row in issuer["per_period"]:
            cells = []
            for tag in REVENUE_CONCEPTS:
                fact = row["concepts"].get(tag)
                cells.append(fact["value"] if fact else "—")
            lines.append(f"| {row['period_end']} | " + " | ".join(cells) + " |")
        lines.append("")
        if mapping["latest_primary_value"]:
            lines.append(
                f"Latest {mapping['latest_period']} {mapping['primary_concept']} value: "
                f"{mapping['latest_primary_value']} (as filed)."
            )
            lines.append("")
        if issuer["per_period"] and any(row["conflicts"] for row in issuer["per_period"]):
            lines.append("Conflicts in the source facts:")
            for row in issuer["per_period"]:
                for conflict in row["conflicts"]:
                    lines.append(f"- {conflict}")
            lines.append("")
        lines.append("Evidence tags by period:")
        for tag, detail in issuer["evidence_tags"].items():
            if detail.get("present"):
                lines.append(
                    f"- `{tag}` — periods {', '.join(detail['periods'])}; latest "
                    f"{detail['latest_period_end']} (accession {detail['latest_accession']}, "
                    f"filed {detail['latest_filed']})."
                )
            else:
                lines.append(f"- `{tag}` — not present in the 10-K window.")
        lines.append("")
        if issuer["open_questions"]:
            lines.append("Open questions:")
            for question in issuer["open_questions"]:
                lines.append(f"- {question}")
            lines.append("")
        lines += ["", f"Sign-off needed: {mapping['certification_required']}", ""]
    lines += ["## Limits", ""]
    for limit in document["limits"]:
        lines.append(f"- {limit}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument(
        "--user-agent", default="Financial System revenue worksheet scott@example.com"
    )
    parser.add_argument("--observed-at", default=date.today().isoformat())
    args = parser.parse_args(argv)

    cache = FactsCache(args.cache_dir, refresh=args.refresh, user_agent=args.user_agent)
    issuers = []
    for cik, ticker, expected_name in ISSUERS:
        extract = cache.extract(cik)
        issuers.append(build_issuer(ticker, cik, expected_name, extract))

    document = {
        "schema_version": SCHEMA_VERSION,
        "observed_at": args.observed_at,
        "issuers": issuers,
        "limits": [
            "Only 10-K annual facts with a 330-400 day duration are read; quarterly and TTM figures are out of scope.",
            "A tag whose only facts are quarterly or older than the ten-year window reads as absent here, even when the engine's taxonomy scan still sees it.",
            "A concept value here is what the filing reported, not a restated or normalised figure.",
            "The proposed mapping is mechanical and uncertified; it does not change the engine's quarantine.",
            "Historical insurance or lending tags are evidence pointers, not proof that the issuer's present statement family is financial.",
            "No packet, release, source pointer, or deployed bundle was modified.",
        ],
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(document, indent=2) + "\n")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(render_markdown(document))
    print(
        json.dumps(
            {
                "issuers": [
                    {
                        "ticker": issuer["ticker"],
                        "family": issuer["proposed_mapping"]["statement_family"],
                        "primary": issuer["proposed_mapping"]["primary_concept"],
                        "value": issuer["proposed_mapping"]["latest_primary_value"],
                        "questions": len(issuer["open_questions"]),
                    }
                    for issuer in issuers
                ]
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
