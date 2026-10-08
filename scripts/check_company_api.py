"""Read-only acceptance probe for the custom company API (Zion-compatible).

    ZION_API_BASE_URL=https://... [ZION_API_TOKEN=...] \\
        python scripts/check_company_api.py AAPL 2026-10-06

Makes one GET to /v1/company/{ticker} with the production adapter's point-in-time
cutoff, maps the packet with the same code the Worker uses, and prints a JSON
coverage summary. Secrets, the base URL and raw packet bodies are never printed.
Exit status 0 means three annual revenue periods mapped at the valuation date.
"""

import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dcf_loader import (  # noqa: E402
    HISTORY_FIELDS,
    ZION_METRICS,
    ProviderError,
    iso_date,
    ticker_symbol,
    zion_document,
)


def summarize(packet, ticker, asof):
    """Map a packet with the production adapter and report gaps; raises ProviderError."""
    doc = zion_document(packet, ticker, asof)
    mapped = set(ZION_METRICS.values())
    seen = {
        obs.get("metric_id")
        for obs in packet.get("fundamentals", {}).get("annual", [])
        if isinstance(obs, dict)
    }
    blank = sorted(
        {
            name
            for row in doc["historical"]
            for name in HISTORY_FIELDS
            if row.get(name) is None
        }
    )
    return {
        "ticker": ticker,
        "valuation_date": asof,
        "periods": [row["period_end"] for row in doc["historical"]],
        "price_mapped": doc["market"]["price"] is not None,
        "diluted_shares_mapped": doc["market"]["diluted_shares"] is not None,
        "unmapped_metric_ids": sorted(m for m in seen if m and m not in mapped),
        "blank_history_fields": blank,
        "warnings": doc["source"]["warnings"],
    }


def probe(argv):
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    ticker = ticker_symbol(argv[1])
    asof = iso_date(argv[2], "Valuation date").isoformat()
    base = os.getenv("ZION_API_BASE_URL", "").rstrip("/")
    if not base.startswith("https://"):
        print("Set ZION_API_BASE_URL to an HTTPS base URL.", file=sys.stderr)
        return 2
    token = os.getenv("ZION_API_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = requests.get(
            f"{base}/v1/company/{ticker}",
            headers=headers,
            params={"as_of": f"{asof}T23:59:59Z", "limit": 1000},
            timeout=(3, 10),
            allow_redirects=False,
        )
        if response.status_code != 200:
            print(f"Provider returned HTTP {response.status_code}.", file=sys.stderr)
            return 1
        summary = summarize(response.json(), ticker, asof)
    except (requests.RequestException, ValueError, ProviderError) as exc:
        print(f"Probe failed: {type(exc).__name__}. Check the endpoint contract.", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2))
    return 0 if len(summary["periods"]) == 3 else 1


if __name__ == "__main__":
    sys.exit(probe(sys.argv))
