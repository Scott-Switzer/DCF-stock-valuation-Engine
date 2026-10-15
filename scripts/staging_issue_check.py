"""Paced live-staging check: CAT/PEP/T/PAYX SEC-first loads, ORCL honest block."""

import json
import sys
import time
import urllib.request

BASE = "https://dcf-valuation-engine-staging.scswitzer.workers.dev"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


def one(ticker):
    req = urllib.request.Request(
        f"{BASE}/api/load/dcf",
        data=json.dumps({"ticker": ticker}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": UA},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            status, payload = r.status, json.load(r)
    except Exception as exc:  # noqa: BLE001 - integration must report, not raise
        return {"ticker": ticker, "ok": False, "error": str(exc)[:200]}
    fin = payload.get("financials", {})
    prev = payload.get("preview", {})
    return {
        "ticker": ticker,
        "ok": True,
        "http": status,
        "source": (fin.get("source") or {}).get("statement_source"),
        "intrinsic": prev.get("intrinsic_value"),
        "preferred": (fin.get("bridge") or {}).get("preferred_equity"),
        "minority": (fin.get("bridge") or {}).get("minority_interest"),
    }


def main(tickers):
    rows = []
    for i, ticker in enumerate(tickers):
        rows.append(one(ticker))
        if i < len(tickers) - 1:
            time.sleep(6)
    print(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:] or ["CAT", "PEP", "T", "PAYX", "ORCL"])
