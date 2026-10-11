#!/usr/bin/env python3
"""Non-saving 25-company audit, with offline replay and independent DCF math.

Run from the repository root with `uv run python scripts/validate_universe.py`.
Live calls use only company loading and non-persisting previews. Snapshot files
are local evidence, not automatically published fixtures or licensed datasets.
"""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import assumptions_from_json, evaluate  # noqa: E402
from financial_qa import QA_UNIVERSE, audit_snapshot, capital_cost_check  # noqa: E402
from reconciliation.reference_dcf import compare_result, reference_dcf  # noqa: E402

DEFAULT_BASE = "https://dcf-valuation-engine.scswitzer.workers.dev"
# Controlled QA assumptions, never advertised as recommended company forecasts.
ASSUMPTIONS = {"revenue_growth_rates": [0.05] * 5, "terminal_growth_rate": 0.02,
               "wacc_override": 0.10, "terminal_mode": "template"}
LOCAL_RESULT = object()


class ScenarioBlocked(ValueError):
    """The independent reference cannot support the controlled QA scenario."""


def post(base, path, payload, timeout):
    request = Request(base.rstrip("/") + path, data=json.dumps(payload, allow_nan=False).encode(),
                      headers={"Content-Type": "application/json", "Accept": "application/json",
                               "User-Agent": "Mozilla/5.0"})
    start = time.monotonic()
    try:
        response = urlopen(request, timeout=timeout)
    except HTTPError as exc:
        response = exc
    with response:
        body = response.read(2_000_001)
        if len(body) > 2_000_000:
            raise ValueError("Response exceeds audit size limit.")
        value = json.loads(body)
        return response.code, value, round(time.monotonic() - start, 3)


def reconcile(doc, actual=LOCAL_RESULT):
    """Use explicit QA assumptions; never infer an independently verified WACC."""
    try:
        reference = reference_dcf(doc, ASSUMPTIONS)
    except ValueError as exc:
        raise ScenarioBlocked(str(exc)) from exc
    if actual is LOCAL_RESULT:
        actual = evaluate(deepcopy(doc), assumptions_from_json(ASSUMPTIONS))
    if not isinstance(actual, dict):
        return {"status": "FAIL", "differences": [{"field": "response", "expected": "valuation object", "actual": actual}],
                "reference": reference, "assumptions": deepcopy(ASSUMPTIONS)}
    differences = compare_result(reference, actual)
    return {"status": "FAIL" if differences else "PASS", "differences": differences,
            "reference": reference, "assumptions": deepcopy(ASSUMPTIONS),
            "scope": "Independent arithmetic with shared inputs and controlled assumptions, not economic or source validation."}


def audit_entry(entry, *, base=None, timeout=45):
    ticker = entry["ticker"]
    if "error" in entry:
        return {"ticker": ticker, "status": "BLOCKED", "issues": [{"code": "load_unavailable",
                "field": "financials", "severity": "warning", "reason": entry["error"]}],
                "methods": {m: {"status": "BLOCKED", "calculation_check": "NOT_RUN",
                                  "reasons": [entry["error"]]}
                            for m in ("dcf", "ddm", "relative", "residual")}}
    doc = entry["bundle"]["financials"]
    result = audit_snapshot(doc)
    result["load_seconds"] = entry.get("seconds")
    result["capital_cost_check"] = capital_cost_check(doc)
    if result["capital_cost_check"]["status"] == "FAIL":
        result["status"] = "FAIL"
    if result["status"] == "FAIL":
        return result
    dcf = result["methods"]["dcf"]
    if dcf["status"] == "BLOCKED":
        if base:
            status, _, seconds = post(base, "/api/preview/dcf", {"financials": doc, "assumptions": ASSUMPTIONS}, timeout)
            result["blocked_api_check"] = {"status": "PASS" if status == 400 else "FAIL",
                                           "http_status": status, "seconds": seconds}
            if status != 400:
                result["status"] = "FAIL"
        return result
    try:
        check = reconcile(doc)
        dcf["calculation_check"] = check["status"]
        dcf["reconciled_fields"] = list(check["reference"])
        result["independent_dcf"] = check
        if check["status"] == "FAIL":
            result["status"] = dcf["status"] = "FAIL"
    except ScenarioBlocked as exc:
        # A controlled assumption set can be unsuitable (e.g. nonpositive FCFF).
        # This is an explicit scenario block, never a fabricated zero target.
        dcf["status"] = "BLOCKED"
        dcf["reasons"].append(str(exc))
        return result
    except (ValueError, TypeError, KeyError) as exc:
        result["status"] = dcf["status"] = "FAIL"
        dcf["reasons"].append(f"Engine failed a supported reference scenario: {exc}")
        return result
    if base:
        try:
            status, actual, seconds = post(base, "/api/preview/dcf", {"financials": doc, "assumptions": ASSUMPTIONS}, timeout)
            api = reconcile(doc, actual) if status == 200 else {"status": "FAIL", "http_status": status}
            api["seconds"] = seconds
        except (ValueError, OSError, URLError, TypeError, KeyError) as exc:
            api = {"status": "FAIL", "reason": str(exc)}
        result["api_reconciliation"] = api
        if api["status"] == "FAIL":
            result["status"] = dcf["status"] = "FAIL"
    return result


def markdown_report(report):
    lines = ["# Real-company financial QA", "", f"Captured: {report['captured_at']}", "",
             "Controlled DCF assumptions: 5% annual revenue growth, 10% WACC, 2% terminal growth, CUIG terminal convention.",
             "These are test assumptions, not company forecasts. Arithmetic PASS does not certify source observations or economic credibility.",
             "", "| Ticker | Overall | DCF readiness / arithmetic | DDM | Relative | Residual |",
             "| --- | --- | --- | --- | --- | --- |"]
    for row in report["companies"]:
        methods = row.get("methods", {})
        dcf = methods.get("dcf", {})
        lines.append(f"| {row['ticker']} | {row['status']} | {dcf.get('status', 'BLOCKED')} / {dcf.get('calculation_check', 'NOT_RUN')} | "
                     + " | ".join(methods.get(m, {}).get("status", "BLOCKED") for m in ("ddm", "relative", "residual")) + " |")
    lines += ["", "## Findings and evidence boundaries", ""]
    for row in report["companies"]:
        lines.append(f"### {row['ticker']}")
        lines.append(f"Source: {row.get('source', 'unavailable')}; price date: {row.get('price_as_of', 'unavailable')}.")
        for finding in row.get("issues", []):
            lines.append(f"- {finding['severity']}: `{finding['code']}` ({finding['field']}): {finding['reason']}")
        for method, state in row.get("methods", {}).items():
            if state["status"] in {"BLOCKED", "FAIL"}:
                lines.append(f"- {method}: {'; '.join(state.get('reasons', []))}")
        lines.append("")
    lines += ["Full JSON retains field values, provider provenance, periods, dates, readiness codes and numerical differences.",
              "No method is promoted to overall PASS until its financial observations and calculation have both been independently validated."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--snapshots", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--offline", action="store_true", help="Replay saved snapshots without network calls")
    parser.add_argument("--api", action="store_true", help="Also compare non-saving live API previews")
    parser.add_argument("--timeout", type=float, default=45)
    args = parser.parse_args(argv)
    if not args.base.startswith("https://") or not 0 < args.timeout <= 120 or (args.offline and args.api):
        parser.error("Use HTTPS and a 0–120 second timeout; --offline cannot use --api")
    args.snapshots.mkdir(parents=True, exist_ok=True)
    rows = []
    for ticker in QA_UNIVERSE:
        path = args.snapshots / f"{ticker}.json"
        try:
            if args.offline:
                entry = json.loads(path.read_text())
            else:
                status, bundle, elapsed = post(args.base, "/api/load/dcf", {"ticker": ticker}, args.timeout)
                entry = {"ticker": ticker, "seconds": elapsed}
                entry.update(bundle=bundle) if status == 200 else entry.update(error=f"HTTP {status}: {bundle.get('error', 'load unavailable')}")
                path.write_text(json.dumps(entry, indent=2, allow_nan=False))
            if entry.get("ticker") != ticker or ("bundle" in entry and entry["bundle"]["financials"]["company"]["ticker"] != ticker):
                raise ValueError("Snapshot identity mismatch")
            row = audit_entry(entry, base=args.base if args.api else None, timeout=args.timeout)
        except (OSError, URLError, ValueError, KeyError, TypeError) as exc:
            row = {"ticker": ticker, "status": "FAIL", "issues": [{"code": "audit_error", "field": "audit",
                    "severity": "error", "reason": str(exc)}], "methods": {}}
        rows.append(row)
        print(f"{ticker:6} {row['status']:7} {row.get('methods', {}).get('dcf', {}).get('calculation_check', 'NOT_RUN')}", flush=True)
    report = {"captured_at": datetime.now(timezone.utc).isoformat(), "base": args.base,
              "mode": "offline" if args.offline else "live", "api_checked": args.api, "companies": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False))
    args.output.with_suffix(".md").write_text(markdown_report(report))
    return 1 if any(row["status"] == "FAIL" for row in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
