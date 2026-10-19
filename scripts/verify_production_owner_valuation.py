"""Read-only production acceptance; prints counts/hashes and no private source values."""

import sys, json, hashlib, argparse, os
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, localcontext

ROOT = Path(__file__).resolve().parents[1]
ZION = Path(os.environ.get("ZION_SOURCE_ROOT", str(ROOT.parents[1] / "zion-valuation-service")))
sys.path.insert(0, str(ZION / "scripts"))
import sec_engine_acceptance as t

sys.path.insert(0, str(ROOT))
p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--output", type=Path, required=True)
args = p.parse_args()
if args.output.exists():
    raise ValueError("Output must be new")
from dcf_loader import demo_document

base = "https://dcf-valuation-engine.scswitzer.workers.dev"
t.BASE = base
checks = {}


def check(k, v):
    checks[k] = bool(v)
    if not v:
        raise RuntimeError("Check failed: " + k)


for path in ("/health", "/ready", "/api/providers", "/api/equity-claims/status"):
    b, m = t.request(path)
    check(path, m["http_status"] == 200)
    if path == "/health":
        revision = (b.get("release") or {}).get("commit")
manual = {
    "financials": demo_document(),
    "assumptions": {
        "revenue_growth_rates": [0.05] * 5,
        "terminal_growth_rate": 0.02,
        "wacc_override": 0.1,
    },
}
b, m = t.request("/api/calculate", body=manual, auth=False)
check("public_manual_calculation", m["http_status"] == 200)
_, m = t.request(
    "/api/assumptions/damodaran/" + "a" * 64, {"subject": "x", "measure": "wacc"}, auth=False
)
check("anonymous_private_benchmark_refused", m["http_status"] == 401)
b, m = t.request(
    "/api/financials",
    body={
        "provider": "zion_history",
        "ticker": "AAPL",
        "cik": "0000320193",
        "valuation_date": "2026-09-24",
    },
)
check("production_native_financials", m["http_status"] == 200)
doc = b["financials"]
today = datetime.now(timezone.utc).date().isoformat()
selections = {
    k: {
        "release_id": rid,
        "subject": "Computers/Peripherals",
        "measure": measure,
        "mode": "current",
        "source": "zion",
    }
    for k, rid, measure in [
        ("wacc", "11c1e6bb76d9db12feeec3e3949a9ffe370d0ace87f3047aaac66f431270ccc9", "wacc"),
        (
            "tax_rate",
            "11c1e6bb76d9db12feeec3e3949a9ffe370d0ace87f3047aaac66f431270ccc9",
            "tax_rate",
        ),
        (
            "sales_capital",
            "bcd291a646f52393ae5e6b539cfd3936e08aba566f7e34fc39448d81ca7f816c",
            "sales_to_invested_capital",
        ),
    ]
}
payload = {
    "financials": doc,
    "valuation_date": today,
    "benchmark_selections": selections,
    "revenue_growth_rates": [0.03] * 5,
    "terminal_growth": 0.02,
    "terminal_roic": 0.15,
    "suitable": True,
}
r, m = t.request("/api/calculate/enterprise", body=payload)

check("production_owner_native_enterprise", m["http_status"] == 200)
with localcontext() as c:
    c.prec = 40
    actual = doc["historical"][-1]
    rev = Decimal(str(actual["revenue"]))
    margin = Decimal(str(actual["ebit"])) / rev
    chosen = r["benchmark_assumptions"]
    wacc = Decimal(chosen["wacc"]["value_decimal"])
    tax = Decimal(chosen["tax_rate"]["value_decimal"])
    eff = Decimal(chosen["sales_capital"]["value_decimal"])
    stage = Decimal(0)
    for year in range(1, 6):
        prev = rev
        rev *= Decimal("1.03")
        nopat = rev * margin * (1 - tax)
        fcff = nopat - (rev - prev) / eff
        stage += fcff / (1 + wacc) ** year
    terminal = (
        nopat * Decimal("1.02") * (1 - Decimal(".02") / Decimal(".15")) / (wacc - Decimal(".02"))
    )
    independent = stage + terminal / (1 + wacc) ** 5
    error = abs(Decimal(str(r["enterprise_value"])) - independent)
check("independent_decimal_reconciliation_under_one_cent", error < Decimal(".01"))
check(
    "missing_equity_bridge_not_zero_filled",
    r["equity_value"] is None and r["intrinsic_value"] is None,
)
receipt = {
    "status": "PASS",
    "origin": base,
    "deployed_commit": revision,
    "checks": checks,
    "financial_history_rows": len(doc["historical"]),
    "scenario": "Explicit 3 percent growth, 2 percent terminal growth, 15 percent terminal ROIC; source-backed industry benchmarks",
    "source_financial_release": doc["source"].get("release_id"),
    "independent_absolute_error_decimal": str(error),
    "private_source_values_printed": 0,
    "production_research_records_written": 0,
    "valuation_result_sha256": hashlib.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest(),
}
p = args.output
p.write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt))
