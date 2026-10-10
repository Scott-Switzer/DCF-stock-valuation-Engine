#!/usr/bin/env python3
"""Read-only production Worker acceptance smoke test.

Preview/export POST endpoints used here do not persist valuation records.
Green source-code tests alone do not prove the public Worker is current.
"""
import argparse
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

DEFAULT_BASE = "https://dcf-valuation-engine.scswitzer.workers.dev"
ASSUMPTIONS = {
    "revenue_growth_rates": [0.05] * 5,
    "terminal_growth_rate": 0.02,
    "wacc_override": 0.065,
}


def fetch(base, path, *, timeout, payload=None, maximum=2_000_000):
    url = urljoin(base.rstrip("/") + "/", path.lstrip("/"))
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
        method="POST" if data is not None else "GET",
    )
    start = time.monotonic()
    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
            body = response.read(maximum + 1)
    except HTTPError as exc:
        diagnostics = {
            "server": exc.headers.get("Server", ""),
            "cf-mitigated": exc.headers.get("Cf-Mitigated", ""),
            "content-type": exc.headers.get("Content-Type", ""),
        }
        raise RuntimeError(f"HTTP {exc.code} at {path}; {diagnostics}") from None
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Network failure at {path}: {type(exc).__name__}") from None
    if len(body) > maximum:
        raise RuntimeError(f"Oversized response at {path}")
    if status != 200:
        raise RuntimeError(f"HTTP {status} at {path}")
    return body, round(time.monotonic() - start, 3)


def decode(body, label):
    try:
        return json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise RuntimeError(f"Invalid JSON: {label}") from None


def assert_true(predicate, label):
    if not predicate:
        raise RuntimeError(f"Unexpected response: {label}")


def run(base, timeout, require_ppe=False):
    results = []

    def check(label, path, condition, *, payload=None):
        try:
            body, elapsed = fetch(base, path, timeout=timeout, payload=payload)
            response = decode(body, label)
            assert_true(condition(response), label)
        except (RuntimeError, AttributeError, TypeError, ValueError) as exc:
            results.append({"check": label, "status": "FAIL", "detail": str(exc)})
            return None
        results.append({"check": label, "status": "PASS", "seconds": elapsed})
        return response

    check("health", "/health", lambda x: x.get("status") == "healthy")
    check(
        "readiness", "/ready",
        lambda x: x.get("status") == "ready"
        and (not require_ppe or x.get("ppe_binding_configured") is True),
    )
    check("providers", "/api/providers", lambda x: "auto" in x.get("providers", {}))
    check(
        "ticker_search", "/api/search?q=AAPL",
        lambda x: any(r.get("symbol") == "AAPL" for r in x if isinstance(r, dict)),
    )
    sample = check(
        "sample", "/api/sample",
        lambda x: x.get("source", {}).get("kind") == "synthetic"
        and x.get("company", {}).get("ticker") == "DEMO",
    )
    if sample is not None:
        payload = {"financials": sample, "assumptions": ASSUMPTIONS}
        check(
            "non_saving_preview", "/api/preview/dcf",
            lambda x: isinstance(x.get("intrinsic_value"), (int, float))
            and isinstance(x.get("target_price_12m"), (int, float))
            and "saved_record_id" not in x,
            payload=payload,
        )
        check(
            "json_export", "/export/json",
            lambda x: x.get("financials", {}).get("company", {}).get("ticker") == "DEMO"
            and isinstance(x.get("result", {}).get("intrinsic_value"), (int, float)),
            payload=payload,
        )
    else:
        results.append({"check": "non_saving_preview", "status": "SKIP", "detail": "Sample failed"})
        results.append({"check": "json_export", "status": "SKIP", "detail": "Sample failed"})
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument("--require-ppe", action="store_true")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args(argv)
    if not args.base.startswith("https://") or not 0 < args.timeout <= 120:
        parser.error("Use an HTTPS base and a 0–120 second timeout")
    results = run(args.base, args.timeout, args.require_ppe)
    for item in results:
        print(f"{item['status']:4} {item['check']:20} {item.get('seconds', '-')}s {item.get('detail', '')}")
    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            json.dump({"base": args.base, "results": results}, file, indent=2)
    failed = any(x["status"] != "PASS" for x in results)
    print(f"Public smoke: {'FAIL' if failed else 'PASS'} ({sum(x['status']=='PASS' for x in results)}/{len(results)})")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
