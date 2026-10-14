"""Warm-path staging benchmark: 20 loads per ticker, paced for rate limits.

Records client-observed latency, assembly-cache state, stage timings,
statement source, embedded-brief presence, and Server-Timing. Prints
nearest-rank p50/p95. Small-sample MISS rows are labeled exploratory.
Usage: PYTHONPATH=. .venv/bin/python scripts/bench_warm.py [TICKERS...]
"""

import json
import sys
import time
import urllib.request

BASE = "https://dcf-valuation-engine-staging.scswitzer.workers.dev"
N = 20
DELAY = 8


def one(ticker):
    body = json.dumps({"ticker": ticker}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/load/dcf", data=body, headers={"Content-Type": "application/json"}
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            payload = json.load(r)
            server_timing = r.headers.get("Server-Timing", "")
    except Exception as exc:  # noqa: BLE001 - benchmark must record, not raise
        return {"ticker": ticker, "ok": False, "error": str(exc)[:120]}
    elapsed = time.monotonic() - started
    summary = payload.get("load_summary", {})
    return {
        "ticker": ticker,
        "ok": True,
        "elapsed": round(elapsed, 3),
        "cache": (summary.get("assembly_cache") or {}).get("state"),
        "stages": summary.get("stage_seconds", {}),
        "source": (payload.get("financials", {}).get("source") or {}).get("statement_source"),
        "brief": "brief" in payload,
        "server_timing": server_timing,
    }


def pct(values, q):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))]


def main(tickers):
    all_rows = []
    for ticker in tickers:
        rows = []
        for i in range(N):
            rows.append(one(ticker))
            all_rows.append(rows[-1])
            if i < N - 1:
                time.sleep(DELAY)
        ok = [r["elapsed"] for r in rows if r.get("ok")]
        print(
            f"{ticker}: n={len(ok)}/{N} p50={pct(ok, .5)} p95={pct(ok, .95)} "
            f"cache={sorted({r.get('cache') for r in rows if r.get('ok')})} "
            f"source={sorted({r.get('source') for r in rows if r.get('ok')})} "
            f"brief={all(r.get('brief') for r in rows if r.get('ok'))}"
        )
    json.dump(all_rows, open("find/outputs/staging-final/warm20.json", "w"), indent=1)
    print("wrote find/outputs/staging-final/warm20.json")


if __name__ == "__main__":
    main(sys.argv[1:] or ["AAPL", "MSFT", "PEP"])
