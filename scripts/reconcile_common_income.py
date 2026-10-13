"""Reconcile the direct common-income SEC tag against its statement components.

Read-only evidence tool. For each issuer it fetches SEC companyfacts (cached under
--cache-dir), selects annual 10-K observations per fiscal period end, and reports:

* the direct tag NetIncomeLossAvailableToCommonStockholdersBasic (basic EPS numerator),
* NetIncomeLoss (income attributable to the parent),
* PreferredStockDividendsIncomeStatementImpact,
* NetIncomeLossAttributableToNoncontrollingInterest and ProfitLoss (consolidated),

with the accession, filing date and period start of each observation.

The verdict is computed by ppe_packets.common_income_evidence, the same function the packet
publisher gate uses. Parent income and components are read only from the direct observation's
own 10-K accession, so an item from another filing never explains the residual. The result is
evidence only; nothing here is written back to packets.

Usage:
    python scripts/reconcile_common_income.py --out find/outputs/common-income-reconciliation/summary.json
"""

import argparse
import datetime
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dcf_loader import ProviderError  # noqa: E402
from ppe_packets import common_income_evidence  # noqa: E402

USER_AGENT = "Buffy valuation research contact@example.com"
COMPANYFACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

# name -> CIK (10-digit)
ISSUERS = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "KO": "0000021344",
    "XOM": "0000034088",
    "JPM": "0000019617",
    "BAC": "0000070858",
    "C": "0000831001",
    "GS": "0000886982",
}

TAGS = {
    "net_income_parent": "NetIncomeLoss",
    "profit_consolidated": "ProfitLoss",
    "nci_income": "NetIncomeLossAttributableToNoncontrollingInterest",
    "preferred_dividends": "PreferredStockDividendsIncomeStatementImpact",
    "preferred_cash": "DividendsPreferredStockCash",
    "preferred_stock": "DividendsPreferredStock",
    "preferred_and_adjustments": "PreferredStockDividendsAndOtherAdjustments",
    "participating_securities": "ParticipatingSecuritiesDistributedAndUndistributedEarningsLossBasic",
    "participating_securities_alt": "ParticipatingSecuritiesDistributedAndUndistributedEarnings",
    "preferred_dividends_alt": "PreferredStockDividends",
    "common_basic": "NetIncomeLossAvailableToCommonStockholdersBasic",
    "common_diluted": "NetIncomeLossAvailableToCommonStockholdersDiluted",
}


def fetch(cik, cache_dir):
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"CIK{cik}.json"
    if not path.exists():
        request = urllib.request.Request(
            COMPANYFACTS.format(cik=cik), headers={"User-Agent": USER_AGENT}
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            path.write_bytes(response.read())
        time.sleep(0.2)  # stay well under the SEC fair-access limit
    return json.loads(path.read_text())


def annual_observations(doc, tag):
    """Return {end: observation} from each period's ORIGINAL 10-K.

    A companyfacts row carries the fiscal year (`fy`) of the filing that reported it. Later
    filings repeat prior years as comparatives, so only rows whose `fy` equals the period's own
    year (fp=FY) are kept, and the earliest such filing wins. Later comparatives are restatements
    and are reported separately via `restated_observations`.
    """
    out = {}
    for row in _annual_rows(doc, tag):
        end = row["end"]
        if row.get("fy") != int(end[:4]) or row.get("fp") != "FY":
            continue
        current = out.get(end)
        if current is None or row["filed"] < current["filed"]:
            out[end] = _observation(row)
    return out


def restated_observations(doc, tag):
    """Return {end: observation} from the latest 10-K that repeats the period (comparatives)."""
    out = {}
    for row in _annual_rows(doc, tag):
        end = row["end"]
        current = out.get(end)
        if current is None or row["filed"] > current["filed"]:
            out[end] = _observation(row)
    return out


def _annual_rows(doc, tag):
    units = doc.get("facts", {}).get("us-gaap", {}).get(tag, {}).get("units", {}).get("USD", [])
    for row in units:
        if row.get("form") not in {"10-K", "10-K/A"} or not row.get("start") or not row.get("end"):
            continue
        days = (
            datetime.date.fromisoformat(row["end"]) - datetime.date.fromisoformat(row["start"])
        ).days
        if 330 <= days <= 400:
            yield row


def _observation(row):
    return {
        "value": row["val"],
        "accession": row.get("accn"),
        "filed": row["filed"],
        "period_start": row["start"],
        "form": row.get("form"),
    }


def reconcile_verdict(doc, end, direct):
    """Shared packet-gate verdict for one direct observation, with same-filing evidence."""
    if direct is None:
        return {"verdict": "no_direct_tag"}
    observation = {
        "value": direct["value"],
        "provenance": {"accession": direct["accession"]},
    }
    try:
        return common_income_evidence(doc, end, observation)
    except ProviderError as error:
        return {"verdict": "conflicting_filing_facts", "error": str(error)}


def reconcile(ticker, cik, cache_dir):
    doc = fetch(cik, cache_dir)
    series = {name: annual_observations(doc, tag) for name, tag in TAGS.items()}
    ends = sorted(set(series["common_basic"]) | set(series["net_income_parent"]))
    rows = []
    for end in ends:
        row = {"ticker": ticker, "cik": cik, "period_end": end, "observations": {}}
        for name in TAGS:
            if end in series[name]:
                row["observations"][name] = series[name][end]
        row.update(reconcile_verdict(doc, end, series["common_basic"].get(end)))
        rows.append(row)
    return rows


FIXTURE_TAGS = sorted(set(TAGS.values()))


def write_fixture(doc, out_dir, ticker):
    """Write the 10-K-only rows for the reconciliation tags, unchanged, for offline tests."""
    kept = {}
    for tag in FIXTURE_TAGS:
        block = doc.get("facts", {}).get("us-gaap", {}).get(tag)
        if not block:
            continue
        rows = [r for r in block.get("units", {}).get("USD", []) if r.get("form") in {"10-K", "10-K/A"}]
        kept[tag] = {"units": {"USD": rows}}
    subset = {"cik": doc.get("cik"), "entityName": doc.get("entityName"), "facts": {"us-gaap": kept}}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{ticker}.json").write_text(json.dumps(subset, indent=2, sort_keys=True) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True)
    parser.add_argument("--cache-dir", default="/tmp/sec-companyfacts")
    parser.add_argument("--tickers", nargs="*", default=list(ISSUERS))
    parser.add_argument("--fixture-dir", help="also write 10-K-only companyfacts subsets here")
    args = parser.parse_args(argv)
    cache_dir = Path(args.cache_dir)
    result = []
    for ticker in args.tickers:
        if ticker not in ISSUERS:
            print(f"unknown ticker {ticker}", file=sys.stderr)
            return 2
        result.extend(reconcile(ticker, ISSUERS[ticker], cache_dir))
    if args.fixture_dir:
        for ticker in args.tickers:
            write_fixture(fetch(ISSUERS[ticker], cache_dir), Path(args.fixture_dir), ticker)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    counts = {}
    for row in result:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    print(json.dumps(counts, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
