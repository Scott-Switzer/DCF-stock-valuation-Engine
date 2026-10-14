"""Instant Investment Research Brief: one compact, deterministic summary per load.

Reuses the workspace's own valuation machinery (``evaluate`` for the DCF,
scenarios and sensitivity; ``reverse_dcf.solve`` for market-implied drivers;
``coerce_dcf_assumptions`` for the baseline forecast). Nothing here is a new
calculator and no language model invents financial facts: every number comes
from the loaded snapshot plus explicit baseline assumptions, and failures
(bank DCF blocks, unsolvable reverse solves) are reported, not hidden.
"""

from copy import deepcopy


def _drivers_from_sensitivity(sensitivity):
    """Which input moves intrinsic value more: WACC or terminal growth?

    Reads the evaluate() sensitivity grid (5 WACC rows x 5 growth columns,
    centered on the base case) and compares the value spread across each
    axis. Returns spreads and a plain-language top-driver label.
    """
    rows = (sensitivity or {}).get("rows") or []
    growths = (sensitivity or {}).get("growth_rates") or []
    if len(rows) < 5 or len(growths) < 5:
        return {"top": None, "wacc_spread": None, "growth_spread": None,
                "note": "Sensitivity grid unavailable."}
    mid = 2
    base_row = [v for v in (rows[mid].get("values") or []) if v is not None]
    wacc_col = [r.get("values", [])[mid] for r in rows
                if len(r.get("values", [])) > mid and r["values"][mid] is not None]
    growth_spread = (max(base_row) - min(base_row)) if len(base_row) > 1 else 0
    wacc_spread = (max(wacc_col) - min(wacc_col)) if len(wacc_col) > 1 else 0
    top = None
    if wacc_spread > 0 or growth_spread > 0:
        top = ("discount rate (WACC)" if wacc_spread >= growth_spread
               else "terminal growth")
    return {
        "top": top,
        "wacc_spread": round(wacc_spread, 2),
        "growth_spread": round(growth_spread, 2),
        "note": (
            f"Across ±1pp, the discount rate moves intrinsic value by "
            f"${wacc_spread:,.2f} and terminal growth by ${growth_spread:,.2f}."
            if top else "Sensitivity grid has no usable range."
        ),
    }


def build_brief(doc, raw_assumptions=None):
    """Assemble the brief from a validated dcf-financials-v1 snapshot."""
    from dcf_loader import parse_document
    from issuer_classification import financial_block_reason
    from compare import coerce_dcf_assumptions
    from reverse_dcf import solve

    parse_document(deepcopy(doc))  # validation only; field access uses the raw snapshot
    d = deepcopy(doc)
    ticker = d["company"]["ticker"]
    blocked = financial_block_reason(d)
    if blocked:
        return {
            "ticker": ticker,
            "company": d["company"].get("name", ticker),
            "valuation_date": d.get("valuation_date"),
            "blocked": blocked,
        }
    costs = (d.get("source") or {}).get("capital_costs", {}) or {}
    wacc = costs.get("wacc") or 0.065
    assumptions, custom = coerce_dcf_assumptions(d, raw_assumptions, wacc)

    from app import evaluate

    result = evaluate(deepcopy(d), deepcopy(assumptions))
    price = d["market"]["price"]
    implied = {}
    for driver in ("revenue_growth", "ebit_margin"):
        try:
            solved = solve(deepcopy(d), deepcopy(assumptions), price, driver)
        except ValueError as exc:
            solved = {"driver": driver, "status": "error", "detail": str(exc)}
        implied[driver] = solved

    source = d.get("source", {}) or {}
    classification = source.get("classification", {}) or {}
    warnings = source.get("warnings", []) or []
    historical = d.get("historical", []) or []
    growth_rates = list(assumptions.revenue_growth_rates or [])
    margins = list(assumptions.ebit_margins or [])
    return {
        "ticker": ticker,
        "company": d["company"].get("name", ticker),
        "valuation_date": d.get("valuation_date"),
        "basis": "custom" if custom else "baseline",
        "basis_note": (
            "Custom assumptions supplied with the snapshot."
            if custom
            else "Baseline assumptions at load; not updated when you edit assumptions."
        ),
        "price": {"value": price, "as_of": d["market"].get("price_as_of")},
        "dcf": {
            "intrinsic_value": result["intrinsic_value"],
            "target_price_12m": result["target_price_12m"],
            "upside": result["upside"],
            "upside_12m": result["upside_12m"],
            "wacc": result["wacc"],
            "terminal_growth": result["terminal_growth"],
        },
        "assumptions": {
            "revenue_growth_rates": growth_rates,
            "revenue_growth_mean": sum(growth_rates) / len(growth_rates) if growth_rates else None,
            "ebit_margins": margins,
            "ebit_margin_mean": sum(margins) / len(margins) if margins else None,
            "wacc": result["wacc"],
            "terminal_growth_rate": assumptions.terminal_growth_rate,
            "custom": custom,
        },
        "market_implied": implied,
        "scenarios": [
            {"name": s["name"], "intrinsic_value": s["intrinsic_value"],
             "target_price_12m": s["target_price_12m"]}
            for s in result.get("scenarios", [])
        ],
        "drivers": _drivers_from_sensitivity(result.get("sensitivity")),
        "freshness": {
            "period_ends": [r.get("period_end") for r in historical],
            "available_at": [r.get("available_at") for r in historical],
            "statement_source": source.get("statement_source"),
            "ppe_release": source.get("ppe_release"),
            "classification_status": classification.get("status"),
            "snapshot_warnings": warnings[:6],
            "warning_count": len(warnings),
        },
        "evidence": {
            "guidance_api": f"/api/guidance/{ticker}",
            "references_api": f"/api/references/{ticker}",
            "coverage_page": f"/coverage/{ticker}",
        },
    }
