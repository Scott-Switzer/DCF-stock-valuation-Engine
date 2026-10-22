"""Build an identity-checked proposal for expanding the stored price universe.

Inputs (all read-only, none fetched here):

* the stored Alpaca stock-history manifest, whose ``catalog`` is the frozen
  2,629-symbol universe;
* the SEC company ticker file with exchange and company name
  (``company_tickers_exchange.json``).

The script does not append symbols to any release. It emits a reviewable
candidate table and a summary, and it deliberately marks what it cannot know:
ADR status is not in either input, and ranking beyond the named high-impact
omissions needs a market-cap or index-membership source that the current data
contracts do not carry.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

SCHEMA_VERSION = "universe-expansion-proposal-v1"
NAMED_OMISSIONS = (
    "XOM",
    "GOOGL",
    "GOOG",
    "AMZN",
    "TSLA",
    "META",
    "ORCL",
    "COST",
    "IBM",
    "ADBE",
    "MO",
    "BRK-A",
    "BRK-B",
    "V",
)
EXCLUDED_EXCHANGES = {"OTC"}
DERIVATIVE_SUFFIX = re.compile(r"-(WT|WS|U|UN|R|RT|CL)$")
PREFERRED_SUFFIX = re.compile(r"-P[A-Z]?$")
SHARE_CLASS = re.compile(r"(?:\.|-)([A-Z])$")
SUSPECT_FIVE_LETTER = re.compile(r"^[A-Z]{4}[WUR]$")
COLUMNS = (
    "tier",
    "status",
    "ticker",
    "cik",
    "company",
    "exchange",
    "instrument",
    "share_class",
    "adr_status",
    "other_listings",
    "provenance",
)


def load_universe(path: Path) -> set[str]:
    document = json.loads(path.read_text())
    catalog = document.get("catalog")
    if not isinstance(catalog, list) or not catalog:
        raise ValueError("stock manifest has no catalog")
    symbols = {row["symbol"] for row in catalog if isinstance(row.get("symbol"), str)}
    declared = document.get("symbol_count")
    if isinstance(declared, int) and declared != len(symbols):
        raise ValueError(f"catalog size {len(symbols)} disagrees with symbol_count {declared}")
    return symbols


def load_sec_tickers(path: Path) -> list[dict]:
    document = json.loads(path.read_text())
    fields = document.get("fields")
    rows = document.get("data")
    if fields != ["cik", "name", "ticker", "exchange"] or not isinstance(rows, list):
        raise ValueError("unexpected SEC ticker file shape")
    out = []
    for cik, name, ticker, exchange in rows:
        out.append(
            {
                "cik": str(cik).zfill(10),
                "company": str(name).strip(),
                "ticker": str(ticker).strip(),
                "exchange": exchange or "",
            }
        )
    return out


def classify_instrument(ticker: str) -> tuple[str, str]:
    """Return (instrument, share_class) without guessing beyond the ticker syntax."""
    if DERIVATIVE_SUFFIX.search(ticker):
        return "DERIVATIVE", "NONE"
    if PREFERRED_SUFFIX.search(ticker):
        return "PREFERRED", "NONE"
    match = SHARE_CLASS.search(ticker)
    if match:
        return "COMMON_EQUITY", match.group(1)
    if SUSPECT_FIVE_LETTER.match(ticker):
        return "SUSPECT_DERIVATIVE", "NONE"
    if "-" in ticker:
        return "DERIVATIVE", "NONE"
    return "COMMON_EQUITY", "NONE"


def build_candidates(
    universe: set[str],
    sec_rows: list[dict],
    *,
    named_omissions: tuple[str, ...] = NAMED_OMISSIONS,
) -> tuple[list[dict], dict]:
    """Return (in-scope candidate rows, exclusion counts)."""
    by_ticker: dict[str, dict] = {}
    for row in sec_rows:
        existing = by_ticker.get(row["ticker"])
        if existing and existing["cik"] != row["cik"]:
            raise ValueError("conflicting issuer identities for ticker " + row["ticker"])
        by_ticker.setdefault(row["ticker"], row)
    covered_ciks = {row["cik"] for row in sec_rows if row["ticker"] in universe}
    cik_listings: dict[str, list[str]] = {}
    for row in sec_rows:
        cik_listings.setdefault(row["cik"], []).append(row["ticker"])
    named = set(named_omissions)
    candidates: list[dict] = []
    excluded = Counter()
    for ticker in sorted(by_ticker):
        if ticker in universe:
            continue
        row = by_ticker[ticker]
        instrument, share_class = classify_instrument(ticker)
        if instrument in {"DERIVATIVE", "PREFERRED"}:
            excluded[instrument] += 1
            continue
        if row["exchange"] in EXCLUDED_EXCHANGES:
            excluded["OTC_LISTING"] += 1
            continue
        if instrument == "SUSPECT_DERIVATIVE":
            excluded["SUSPECT_DERIVATIVE"] += 1
            continue
        already = row["cik"] in covered_ciks
        if already:
            status, tier = "ISSUER_ALREADY_COVERED_OTHER_LISTING", "TIER_3_REVIEW"
        elif ticker in named:
            status, tier = "NAMED_HIGH_IMPACT_OMISSION", "TIER_1_NAMED"
        else:
            status, tier = "NEW_EXCHANGE_LISTED_COMMON", "TIER_2_WAVE"
        candidates.append(
            {
                "tier": tier,
                "status": status,
                "ticker": ticker,
                "cik": row["cik"],
                "company": row["company"],
                "exchange": row["exchange"],
                "instrument": instrument,
                "share_class": share_class,
                "adr_status": "UNKNOWN_NOT_IN_CONTRACTS",
                "other_listings": "|".join(sorted(t for t in cik_listings[row["cik"]] if t != ticker)),
                "provenance": "sec-company-tickers-exchange.json;stock-manifest.catalog",
            }
        )
    tier_order = {"TIER_1_NAMED": 0, "TIER_2_WAVE": 1, "TIER_3_REVIEW": 2}
    candidates.sort(key=lambda row: (tier_order[row["tier"]], row["ticker"]))
    summary = {
        "schema_version": SCHEMA_VERSION,
        "universe_symbols": len(universe),
        "universe_issuers_resolved": len(covered_ciks),
        "sec_listed_tickers": len(by_ticker),
        "missing_tickers": len(by_ticker) - len(universe & set(by_ticker)),
        "in_scope_candidates": len(candidates),
        "by_tier": dict(Counter(row["tier"] for row in candidates)),
        "by_status": dict(Counter(row["status"] for row in candidates)),
        "new_issuers": len({row["cik"] for row in candidates if row["status"] != "ISSUER_ALREADY_COVERED_OTHER_LISTING"}),
        "by_exchange": dict(Counter(row["exchange"] for row in candidates)),
        "excluded": dict(sorted(excluded.items())),
        "named_omissions_found": sorted(
            row["ticker"] for row in candidates if row["tier"] == "TIER_1_NAMED"
        ),
        "named_omissions_missing_from_candidates": sorted(named - {row["ticker"] for row in candidates}),
        "identity_limits": [
            "ADR status is not present in either input; every row says UNKNOWN_NOT_IN_CONTRACTS.",
            "Tier 2 is not ranked by size or liquidity; that needs a market-cap or index-membership source.",
            "Share-class and derivative classification uses ticker syntax only.",
            "An issuer already represented by one listing is never proposed as a new issuer.",
        ],
    }
    return candidates, summary


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(COLUMNS))
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in COLUMNS})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stock-manifest", required=True, type=Path)
    parser.add_argument("--sec-tickers", required=True, type=Path)
    parser.add_argument("--out-csv", required=True, type=Path)
    parser.add_argument("--out-summary", required=True, type=Path)
    args = parser.parse_args(argv)
    universe = load_universe(args.stock_manifest)
    candidates, summary = build_candidates(universe, load_sec_tickers(args.sec_tickers))
    write_csv(candidates, args.out_csv)
    args.out_summary.parent.mkdir(parents=True, exist_ok=True)
    args.out_summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: summary[k] for k in ("in_scope_candidates", "by_tier", "excluded")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
