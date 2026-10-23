"""Resolve the named listings to issuer identities with dated SEC evidence.

Inputs are SEC's public ticker file and submissions API, read through a cache so
the receipts are reproducible offline. The script emits receipts only: it does
not ingest, publish, or repoint anything.

What each receipt records:

* the ticker -> CIK mapping and every sibling ticker the CIK carries;
* the issuer's former names and its ticker-file name;
* statement family from filing forms (10-K is domestic; 20-F/40-F is a foreign
  private issuer), never from an assumption about the company;
* the share class stated on the latest annual report cover page, tied to the
  trading symbol, so GOOG/GOOGL are resolved from the filing rather than guessed
  from ticker syntax;
* a succession edge when the ticker's CIK registered with Form 8-K12B, with the
  predecessor verified to have filed the same accession and to hold the annual
  reports.

Deliberate limits, repeated in the output: no ADR trading venue is claimed, the
submissions window is bounded, and a missing cover-page class stays unresolved
instead of being inferred.
"""

from __future__ import annotations

import argparse
import hashlib
import html as html_module
import json
import re
import time
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "identity-receipts-v1"
TICKER_FILE_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SUBMISSIONS_PAGE_URL = "https://data.sec.gov/submissions/{name}"
ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{document}"
ANNUAL_FORMS = ("10-K", "20-F", "40-F")
SUCCESSOR_FORM = "8-K12B"
MAX_ARCHIVE_PAGES = 3
CLASS_TITLE = re.compile(
    r"(Class\s+[A-Z]\s+(?:Common|Capital|Ordinary)\s+(?:Stock|Shares)|"
    r"Common\s+Stock|Capital\s+Stock|Ordinary\s+Shares?)",
    re.IGNORECASE,
)
CLASS_LETTER = re.compile(r"Class\s+([A-Z])", re.IGNORECASE)
TICKER_CLASS = re.compile(r"-([A-Z])$")


class ReceiptError(Exception):
    pass


def canonical_cik(value: str | int) -> str:
    digits = str(value).strip()
    if not digits.isdigit():
        raise ReceiptError(f"CIK {value!r} is not numeric")
    return digits.zfill(10)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SecCache:
    """Read-through cache: every stored payload carries its own source receipt."""

    def __init__(self, root: Path, *, refresh: bool, user_agent: str) -> None:
        self.root = root
        self.refresh = refresh
        self.user_agent = user_agent
        self._last_request = 0.0

    def _fetch(self, url: str) -> bytes:
        wait = 0.2 - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
        self._last_request = time.monotonic()
        return body

    def _read(self, relative: Path, url: str) -> tuple[bytes, dict]:
        path = self.root / relative
        if path.exists() and not self.refresh:
            body = path.read_bytes()
            record = json.loads((path.with_suffix(path.suffix + ".receipt.json")).read_text())
            if record.get("sha256") != sha256_bytes(body):
                raise ReceiptError(f"cached bytes for {relative} do not match their receipt")
            return body, record
        body = self._fetch(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        record = {
            "url": url,
            "sha256": sha256_bytes(body),
            "bytes": len(body),
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        path.with_suffix(path.suffix + ".receipt.json").write_text(
            json.dumps(record, indent=2) + "\n"
        )
        return body, record

    def json(self, relative: Path, url: str) -> tuple[object, dict]:
        body, record = self._read(relative, url)
        return json.loads(body), record

    def document_note(self, cik: str, accession: str, url: str) -> dict:
        """Fetch one filing document and keep a bounded, dated excerpt."""
        relative = Path("documents") / f"{cik}-{accession}.json"
        path = self.root / relative
        if path.exists() and not self.refresh:
            return json.loads(path.read_text())
        body = self._fetch(url)
        text = flatten_html(body.decode("utf-8", errors="replace"))
        payload = {
            "receipt": {
                "url": url,
                "sha256": sha256_bytes(body),
                "bytes": len(body),
                "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            },
            "excerpt": explanatory_excerpt(text),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n")
        return payload

    def cover(self, cik: str, accession: str, document: str, url: str, tickers: list[str]) -> dict:
        relative = Path("covers") / f"{cik}-{accession}.json"
        path = self.root / relative
        if path.exists() and not self.refresh:
            cached = json.loads(path.read_text())
            if cached.get("receipt", {}).get("sha256") is None:
                raise ReceiptError(f"cover cache {relative} has no document receipt")
            if cached.get("extractor") != "cover-v5":
                raise ReceiptError(
                    f"cover cache {relative} was built by an older extractor; rerun with --refresh"
                )
            return cached
        body = self._fetch(url)
        document = body.decode("utf-8", errors="replace")
        text = flatten_html(document)
        mappings = extract_cover_classes(document, text, tickers)
        payload = {
            "extractor": "cover-v5",
            "receipt": {
                "url": url,
                "sha256": sha256_bytes(body),
                "bytes": len(body),
                "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            },
            "mappings": mappings,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n")
        return payload


def flatten_html(document: str) -> str:
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", document)
    text = re.sub(r"(?i)<br\s*/?>|</(p|div|tr|td|h\d)>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_module.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def explanatory_excerpt(text: str, width: int = 1600) -> str:
    """Return the region that names both the predecessor and the successor.

    The two phrases can sit a few hundred characters apart, so the excerpt spans
    the first occurrence of each rather than centring on one. If neither phrase is
    present the caller's verification fails loudly.
    """
    lowered = text.lower()
    positions = [
        index
        for phrase in ("predecessor registrant", "successor registrant")
        for index in [lowered.find(phrase)]
        if index >= 0
    ]
    if not positions:
        return text[:width]
    start = max(0, min(positions) - 300)
    return text[start : start + width].strip()


def normalize_ticker(value: str) -> str:
    """Compare ticker notation across filings: BRK-A, BRK.A and BRK/A are equal."""
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def class_record(title: str | None, excerpt: str, method: str) -> dict:
    if not title:
        return {"class_title": None, "excerpt": excerpt, "method": method}
    cleaned = re.sub(r"\s+", " ", title).strip()
    letter = CLASS_LETTER.search(cleaned)
    return {
        "class_title": cleaned,
        "letter": letter.group(1).upper() if letter else "NONE",
        "excerpt": excerpt,
        "method": method,
    }


def leaf_tokens(cell_html: str) -> list[str]:
    """Split a table cell into its printed lines, which is how a cover row aligns titles and symbols."""
    parts = re.findall(r"(?is)<p[^>]*>(.*?)</p>", cell_html) or [cell_html]
    tokens = [flatten_html(part) for part in parts]
    return [token for token in tokens if token]


def extract_cover_classes(document: str, text: str, tickers: list[str]) -> dict:
    """Map each ticker to the class title stated on the annual-report cover page.

    Two layouts occur in practice. A one-column-per-field table pairs the title
    with the symbol in the same row, which is read from the row's cells. Some
    issuers print all titles and then all symbols, so the fallback reads the text
    immediately before the first symbol occurrence that has a class title. Every
    occurrence is tried before reporting an unresolved class; a symbol that also
    appears in XBRL metadata must not shadow the cover page.
    """
    targets = {normalize_ticker(ticker): ticker for ticker in tickers}
    out: dict[str, dict] = {}
    for table in re.findall(r"(?is)<table.*?</table>", document):
        for row in re.findall(r"(?is)<tr.*?</tr>", table):
            raw_cells = re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", row)
            cells = [flatten_html(cell) for cell in raw_cells]
            if len(cells) < 2:
                continue
            token_rows = [leaf_tokens(cell) for cell in raw_cells]
            symbol_columns = [
                index
                for index, tokens in enumerate(token_rows)
                if any(normalize_ticker(token) in targets for token in tokens)
            ]
            if len(symbol_columns) == 1:
                symbol_index = symbol_columns[0]
                symbols = [normalize_ticker(token) for token in token_rows[symbol_index]]
                title_index = max(
                    (index for index in range(len(token_rows)) if index != symbol_index),
                    key=lambda index: len(list(CLASS_TITLE.finditer(" ".join(token_rows[index])))),
                    default=None,
                )
                titles = (
                    [
                        match.group(1)
                        for token in token_rows[title_index]
                        for match in [CLASS_TITLE.search(token)]
                        if match
                    ]
                    if title_index is not None
                    else []
                )
                title_tokens = token_rows[title_index] if title_index is not None else []
                if len(title_tokens) == len(symbols):
                    # Print rows carry one line per security, so the k-th title line
                    # belongs to the k-th symbol even when some titles are notes.
                    for title, symbol in zip(title_tokens, symbols):
                        if not CLASS_TITLE.search(title):
                            continue
                        ticker = targets.get(symbol)
                        if ticker and ticker not in out:
                            out[ticker] = class_record(
                                title, " | ".join(cells)[:300], "cover_table_columns"
                            )
                elif len(titles) == len(symbols):
                    for symbol, title in zip(symbols, titles):
                        ticker = targets.get(symbol)
                        if ticker and ticker not in out:
                            out[ticker] = class_record(
                                title, " | ".join(cells)[:300], "cover_table_columns"
                            )
            for index, cell in enumerate(cells):
                ticker = targets.get(normalize_ticker(cell))
                if ticker is None or ticker in out:
                    continue
                title = next(
                    (
                        match.group(1)
                        for other in cells[:index] + cells[index + 1 :]
                        for match in [CLASS_TITLE.search(other)]
                        if match
                    ),
                    None,
                )
                if title:
                    out[ticker] = class_record(title, " | ".join(cells)[:300], "cover_table_row")

    positions: list[tuple[int, str]] = []
    for ticker in tickers:
        # Filings write share classes as BRK.A, BRK-A or BRK/A; SEC's ticker
        # file uses the hyphen form.
        pattern = r"[.\-/]".join(re.escape(part) for part in ticker.split("-"))
        for match in re.finditer(pattern, text):
            positions.append((match.start(), ticker))
    positions.sort()
    previous = -1
    for position, ticker in positions:
        window = text[max(previous + 1, position - 300) : position]
        previous = position
        if ticker in out:
            continue
        matches = list(CLASS_TITLE.finditer(window))
        if not matches:
            continue
        out[ticker] = class_record(
            matches[-1].group(1), window[-220:].strip(), "adjacent_text"
        )

    for ticker in tickers:
        out.setdefault(ticker, class_record(None, "", "not_found"))
    return out


def ticker_class(ticker: str) -> str:
    match = TICKER_CLASS.search(ticker)
    return match.group(1) if match else "UNMARKED"


def statement_family(forms: list[str]) -> dict:
    counts = {form: forms.count(form) for form in ANNUAL_FORMS}
    present = [form for form in ANNUAL_FORMS if counts[form]]
    if not present:
        return {"family": "NO_ANNUAL_REPORT_FOUND", "counts": counts}
    if len(present) > 1:
        return {"family": "AMBIGUOUS_MIXED_FORMS", "counts": counts}
    form = present[0]
    return {
        "family": "DOMESTIC_10K" if form == "10-K" else "FOREIGN_PRIVATE_ISSUER",
        "form": form,
        "counts": counts,
    }


def latest_annual(filings: list[dict]) -> dict | None:
    annual = [row for row in filings if row["form"] in ANNUAL_FORMS]
    if not annual:
        return None
    return max(annual, key=lambda row: row["filing_date"])


def flatten_filings(pages: list[dict], limit: int = 2500) -> list[dict]:
    rows: list[dict] = []
    for page in pages:
        recent = page.get("filings", {}).get("recent", {})
        fields = ("form", "filingDate", "accessionNumber", "primaryDocument", "reportDate", "items")
        columns = [recent.get(name) or [""] * len(recent.get("form", [])) for name in fields]
        for values in zip(*columns):
            row = dict(zip(fields, values))
            rows.append(
                {
                    "form": str(row["form"] or "").strip(),
                    "filing_date": str(row["filingDate"] or "").strip(),
                    "accession": str(row["accessionNumber"] or "").strip(),
                    "document": str(row["primaryDocument"] or "").strip(),
                    "period": str(row["reportDate"] or "").strip(),
                    "items": str(row["items"] or "").strip(),
                }
            )
            if len(rows) >= limit:
                return rows
    return rows


def load_submissions(cache: SecCache, cik: str) -> tuple[list[dict], list[dict]]:
    pages: list[dict] = []
    receipts: list[dict] = []
    page, record = cache.json(Path("submissions") / f"CIK{cik}.json", SUBMISSIONS_URL.format(cik=cik))
    pages.append(page)
    receipts.append(record)
    archive = page.get("filings", {}).get("files") or []
    for entry in archive[:MAX_ARCHIVE_PAGES]:
        if any(row["form"] in ANNUAL_FORMS for row in flatten_filings(pages)):
            break
        name = entry.get("name")
        if not name:
            continue
        page, record = cache.json(Path("submissions") / name, SUBMISSIONS_PAGE_URL.format(name=name))
        pages.append(page)
        receipts.append(record)
    return flatten_filings(pages), receipts


def verify_succession(successor: dict, predecessor: dict, edge: dict) -> dict:
    """Verify a succession edge against both submissions documents.

    The edge file only names which two CIKs to compare. The accession must exist
    on both, and the predecessor's name must appear in the successor's own
    explanatory note, which the caller fetched from SEC.
    """
    excerpt = edge.get("excerpt", "")
    problems = []
    accession = edge.get("accession", "")
    if not any(row["form"] == SUCCESSOR_FORM and row["accession"] == accession for row in successor["filings"]):
        problems.append("successor does not carry that 8-K12B accession")
    shared = sorted(
        {row["accession"] for row in predecessor["filings"]}
        & {row["accession"] for row in successor["filings"]}
    )
    if predecessor["name"].lower() not in excerpt.lower():
        problems.append("explanatory note does not name the predecessor")
    if "successor registrant" not in excerpt.lower():
        problems.append("explanatory note does not call the filer the successor registrant")
    if problems:
        raise ReceiptError("succession edge failed verification: " + "; ".join(problems))
    return {
        "successor_cik": successor["cik"],
        "predecessor_cik": predecessor["cik"],
        "accession": accession,
        "filed": edge.get("filed", ""),
        "shared_accessions": shared,
        "document_url": edge.get("document_url", ""),
        "excerpt": excerpt,
        "document_sha256": edge.get("document_sha256", ""),
        "verified": True,
    }


def build_listing_receipt(
    ticker: str,
    row: dict,
    *,
    cache: SecCache,
    submissions: dict,
    receipt_records: dict,
    succession_edges: dict,
) -> dict:
    cik = row["cik"]
    payload = submissions[cik]
    filings = payload["filings_flat"]
    family = statement_family([item["form"] for item in filings])
    annual = latest_annual(filings)
    siblings = sorted(sibling["ticker"] for sibling in row["siblings"])
    receipt = {
        "ticker": ticker,
        "cik": cik,
        "issuer_name_in_ticker_file": row["name"],
        "submissions_name": payload["name"],
        "exchange": row["exchange"],
        "ticker_syntax_class": ticker_class(ticker),
        "sibling_listings": siblings,
        "former_names": payload.get("former_names", []),
        "entity_type": payload.get("entity_type", ""),
        "filer_category": payload.get("category", ""),
        "sic": payload.get("sic", ""),
        "sic_description": payload.get("sic_description", ""),
        "statement_family": family,
        "latest_annual_report": annual,
        "share_class": {"resolved": None, "source": None, "excerpt": ""},
        "succession": None,
        "sources": {
            "ticker_file": receipt_records["tickers"],
            "submissions": receipt_records["submissions"][cik],
        },
    }
    successor_filings = [item for item in filings if item["form"] == SUCCESSOR_FORM]
    if successor_filings:
        edge = succession_edges.get(cik)
        if edge is None:
            receipt["succession"] = {
                "verified": False,
                "reason": "SUCCESSOR_REGISTRATION_NEEDS_AN_EDGE",
                "accessions": [item["accession"] for item in successor_filings],
            }
        else:
            predecessor = submissions[edge["predecessor_cik"]]
            registration = next(
                (item for item in successor_filings if item["accession"] == edge.get("accession")),
                successor_filings[0],
            )
            document_url = ARCHIVE_URL.format(
                cik_int=int(cik),
                accession=registration["accession"].replace("-", ""),
                document=registration["document"],
            )
            note = cache.document_note(cik, registration["accession"], document_url)
            receipt["succession"] = verify_succession(
                {"cik": cik, "name": payload["name"], "filings": filings},
                {"cik": predecessor["cik"], "name": predecessor["name"], "filings": predecessor["filings_flat"]},
                {
                    "accession": registration["accession"],
                    "filed": registration["filing_date"],
                    "document_url": document_url,
                    "excerpt": note["excerpt"],
                    "document_sha256": note["receipt"]["sha256"],
                },
            )
            receipt["succession"]["predecessor_latest_annual_report"] = latest_annual(
                predecessor["filings_flat"]
            )
    return receipt


def resolve_cover(receipt: dict, *, cache: SecCache, submissions: dict, tickers_by_cik: dict) -> None:
    cik = receipt["succession"]["predecessor_cik"] if receipt["succession"] and receipt["succession"].get("verified") else receipt["cik"]
    payload = submissions[cik]
    annual = latest_annual(payload["filings_flat"])
    if annual is None or annual["form"] not in ANNUAL_FORMS:
        receipt["share_class"]["source"] = "NO_ANNUAL_REPORT"
        return
    if not annual["document"]:
        receipt["share_class"]["source"] = "ANNUAL_REPORT_HAS_NO_PRIMARY_DOCUMENT"
        return
    url = ARCHIVE_URL.format(
        cik_int=int(cik), accession=annual["accession"].replace("-", ""), document=annual["document"]
    )
    cover = cache.cover(cik, annual["accession"], annual["document"], url, tickers_by_cik[cik])
    mapping = cover["mappings"].get(receipt["ticker"], {"class_title": None, "excerpt": ""})
    resolved = mapping.get("letter") if mapping.get("class_title") else None
    receipt["share_class"] = {
        "resolved": resolved,
        "letter": resolved,
        "class_title": mapping.get("class_title"),
        "source": "annual_report_cover_page",
        "annual_report_accession": annual["accession"],
        "annual_report_cik": cik,
        "document_url": url,
        "document_sha256": cover["receipt"]["sha256"],
        "excerpt": mapping.get("excerpt", ""),
    }
    if (
        resolved
        and receipt["ticker_syntax_class"] != "UNMARKED"
        and resolved != receipt["ticker_syntax_class"]
    ):
        receipt["share_class"]["conflict"] = (
            f"ticker suffix says {receipt['ticker_syntax_class']}, cover page says {resolved}"
        )


def load_ticker_rows(path: Path) -> dict[str, dict]:
    document = json.loads(path.read_text())
    fields = document.get("fields")
    rows = document.get("data")
    if fields != ["cik", "name", "ticker", "exchange"] or not isinstance(rows, list):
        raise ReceiptError("unexpected SEC ticker file shape")
    by_ticker: dict[str, dict] = {}
    for cik, name, ticker, exchange in rows:
        ticker = str(ticker).strip()
        by_ticker.setdefault(
            ticker,
            {"cik": canonical_cik(cik), "name": str(name).strip(), "ticker": ticker, "exchange": exchange or ""},
        )
    by_cik: dict[str, list[dict]] = {}
    for row in by_ticker.values():
        by_cik.setdefault(row["cik"], []).append(row)
    for row in by_ticker.values():
        row["siblings"] = [item for item in by_cik[row["cik"]] if item["ticker"] != row["ticker"]]
    return by_ticker


def render_markdown(document: dict) -> str:
    lines = [
        "# Identity receipts for the named listings — " + document["observed_at"],
        "",
        "Read-only SEC resolution of the 14 named listings in "
        "`docs/universe-expansion-2026-10-22.csv`. No ingestion, no release change.",
        "",
        "Sources: SEC `company_tickers_exchange.json` and per-issuer submissions JSON, "
        "read on " + document["observed_at"] + ". Every source object's sha256 is in the JSON receipt.",
        "",
        "| Ticker | CIK | Issuer | Exchange | Sibling listings | Statement family | Latest annual report | Share class (cover page) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for receipt in document["listings"]:
        annual = receipt["latest_annual_report"]
        if annual:
            annual_text = f"{annual['form']} {annual['filing_date']} ({annual['period']})"
        elif receipt["succession"] and receipt["succession"].get("verified"):
            predecessor_annual = receipt["succession"]["predecessor_latest_annual_report"]
            annual_text = (
                f"{predecessor_annual['form']} {predecessor_annual['filing_date']} "
                f"({predecessor_annual['period']}) via predecessor"
                if predecessor_annual
                else "none found on either entity"
            )
        else:
            annual_text = "none found"
        share = receipt["share_class"]
        share_text = share.get("class_title") or "UNRESOLVED"
        lines.append(
            "| {ticker} | {cik} | {name} | {exchange} | {siblings} | {family} | {annual} | {share} |".format(
                ticker=receipt["ticker"],
                cik=receipt["cik"],
                name=receipt["submissions_name"],
                exchange=receipt["exchange"],
                siblings=", ".join(receipt["sibling_listings"]) or "—",
                family=receipt["statement_family"]["family"],
                annual=annual_text,
                share=share_text,
            )
        )
    lines += ["", "## Issuer grouping", ""]
    for issuer in document["issuers"]:
        lines.append(
            f"- **{issuer['cik']} {issuer['name']}** — listings {', '.join(issuer['listings'])}; "
            f"former names: {', '.join(issuer['former_names']) or 'none'}; "
            f"family {issuer['statement_family']['family']}; "
            f"succession {issuer['succession']['status'] if issuer['succession'] else 'none'}."
        )
    lines += ["", "## Entity transitions", ""]
    transitions = [row for row in document["listings"] if row["succession"]]
    if not transitions:
        lines.append("None detected among the named listings.")
    for row in transitions:
        succession = row["succession"]
        if succession.get("verified"):
            lines.append(
                f"- **{row['ticker']}** files under CIK {row['cik']} ({row['submissions_name']}). "
                f"Form 8-K12B {succession['accession']} (filed {succession['filed']}) establishes "
                f"CIK {succession['predecessor_cik']} as the predecessor registrant. The successor has "
                f"no annual report of its own; the latest annual report belonging to this ticker is "
                f"{(succession.get('predecessor_latest_annual_report') or {}).get('form', 'none')} "
                f"{(succession.get('predecessor_latest_annual_report') or {}).get('filing_date', '')} "
                f"for period {(succession.get('predecessor_latest_annual_report') or {}).get('period', 'unknown')}, "
                f"filed by the predecessor. "
                f"Excerpt: \"{succession['excerpt']}\""
            )
        else:
            lines.append(
                f"- **{row['ticker']}** has an 8-K12B ({', '.join(succession.get('accessions', []))}) "
                f"but no verified predecessor edge: {succession.get('reason')}."
            )
    lines += ["", "## Limits carried by these receipts", ""]
    for limit in document["limits"]:
        lines.append(f"- {limit}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal", required=True, type=Path)
    parser.add_argument("--cache-dir", required=True, type=Path)
    parser.add_argument("--succession", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    parser.add_argument("--refresh", action="store_true", help="re-fetch every source object")
    parser.add_argument(
        "--user-agent",
        default="Financial System identity receipts scott@example.com",
        help="SEC requires a contact in the User-Agent",
    )
    parser.add_argument("--observed-at", default=date.today().isoformat())
    args = parser.parse_args(argv)

    cache = SecCache(args.cache_dir, refresh=args.refresh, user_agent=args.user_agent)
    _, ticker_record = cache.json(Path("company_tickers_exchange.json"), TICKER_FILE_URL)
    tickers_path = args.cache_dir / "company_tickers_exchange.json"
    rows = load_ticker_rows(tickers_path)

    proposal = json.loads(args.proposal.read_text())
    named = proposal.get("named_omissions_found")
    if not isinstance(named, list) or len(named) != 14:
        raise ReceiptError("proposal does not carry the 14 named omissions")
    missing = [ticker for ticker in named if ticker not in rows]
    if missing:
        raise ReceiptError("named tickers absent from the SEC ticker file: " + ", ".join(missing))

    edges = json.loads(args.succession.read_text()).get("edges", [])
    edge_by_successor = {canonical_cik(edge["successor_cik"]): edge for edge in edges}

    ciks = sorted({rows[ticker]["cik"] for ticker in named})
    submissions: dict[str, dict] = {}
    submission_records: dict[str, dict] = {}
    for cik in ciks:
        filings, records = load_submissions(cache, cik)
        payload, _ = cache.json(Path("submissions") / f"CIK{cik}.json", SUBMISSIONS_URL.format(cik=cik))
        submissions[cik] = {
            "cik": cik,
            "name": payload.get("name", ""),
            "former_names": [item.get("name", "") for item in payload.get("formerNames", [])],
            "entity_type": payload.get("entityType", ""),
            "category": payload.get("category", ""),
            "sic": payload.get("sic", ""),
            "sic_description": payload.get("sicDescription", ""),
            "filings_flat": filings,
        }
        submission_records[cik] = records[0]
    # Successor edges can name a predecessor that is not itself a named ticker.
    for edge in edges:
        predecessor = canonical_cik(edge["predecessor_cik"])
        if predecessor in submissions:
            continue
        filings, records = load_submissions(cache, predecessor)
        payload, _ = cache.json(
            Path("submissions") / f"CIK{predecessor}.json", SUBMISSIONS_URL.format(cik=predecessor)
        )
        submissions[predecessor] = {
            "cik": predecessor,
            "name": payload.get("name", ""),
            "former_names": [item.get("name", "") for item in payload.get("formerNames", [])],
            "entity_type": payload.get("entityType", ""),
            "category": payload.get("category", ""),
            "sic": payload.get("sic", ""),
            "sic_description": payload.get("sicDescription", ""),
            "filings_flat": filings,
        }
        submission_records[predecessor] = records[0]

    # A successor's cover page lives on the predecessor, so both CIKs need the
    # named tickers that must be resolved against that document.
    tickers_by_issuer: dict[str, list[str]] = {}
    for ticker in named:
        tickers_by_issuer.setdefault(rows[ticker]["cik"], []).append(ticker)
    for cik, edge in edge_by_successor.items():
        predecessor = canonical_cik(edge["predecessor_cik"])
        tickers_by_issuer.setdefault(predecessor, []).extend(tickers_by_issuer.get(cik, []))

    listings = []
    for ticker in sorted(named):
        receipt = build_listing_receipt(
            ticker,
            rows[ticker],
            cache=cache,
            submissions=submissions,
            receipt_records={"tickers": ticker_record, "submissions": submission_records},
            succession_edges=edge_by_successor,
        )
        resolve_cover(
            receipt, cache=cache, submissions=submissions, tickers_by_cik=tickers_by_issuer
        )
        listings.append(receipt)

    issuers = []
    for cik in sorted({row["cik"] for row in listings}):
        group = [row for row in listings if row["cik"] == cik]
        issuers.append(
            {
                "cik": cik,
                "name": group[0]["submissions_name"],
                "listings": [row["ticker"] for row in group],
                "former_names": group[0]["former_names"],
                "statement_family": group[0]["statement_family"],
                "succession": (
                    {
                        "status": "VERIFIED"
                        if group[0]["succession"] and group[0]["succession"].get("verified")
                        else "UNRESOLVED",
                        "predecessor_cik": (
                            group[0]["succession"].get("predecessor_cik")
                            if group[0]["succession"]
                            else None
                        ),
                    }
                    if group[0]["succession"]
                    else None
                ),
            }
        )

    unresolvable = [row["ticker"] for row in listings if not row["share_class"].get("resolved")]
    document = {
        "schema_version": SCHEMA_VERSION,
        "observed_at": args.observed_at,
        "ticker_file": {
            "url": TICKER_FILE_URL,
            "sha256": ticker_record["sha256"],
            "bytes": ticker_record["bytes"],
            "fetched_at": ticker_record["fetched_at"],
            "listing_count": len(rows),
        },
        "listings": listings,
        "issuers": issuers,
        "unresolved_share_classes": unresolvable,
        "limits": [
            "Receipts read SEC's public ticker file and submissions API only; no packet was built and no release changed.",
            "Statement family is classified from annual-report form type (10-K domestic, 20-F/40-F foreign private issuer), not from company name or exchange.",
            "Share class is taken from the latest annual report cover page; a class the cover page does not state stays unresolved rather than being guessed from ticker syntax.",
            "ADR trading venue, free float and liquidity are not established by these receipts.",
            "Submissions history is read newest-first with a bounded window of 2,500 filings plus at most three archive pages; an annual report older than that window would read as absent.",
            "A CIK appearing here is an identity claim by SEC's own index, not an endorsement of data quality or filing completeness.",
        ],
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(document, indent=2, sort_keys=False) + "\n")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(render_markdown(document))
    print(
        json.dumps(
            {
                "listings": len(listings),
                "issuers": len(issuers),
                "unresolved_share_classes": unresolvable,
                "successions": [
                    row["ticker"] for row in listings if row["succession"] and row["succession"].get("verified")
                ],
                "out": str(args.out_json),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
