"""Football-field comparison: DCF, DDM and relative targets side by side.

Loads one DCF snapshot per ticker, then derives the DDM and relative
documents from that snapshot so all three methods share identical market
inputs. Methods that cannot be computed (no dividends, no peers) are
reported as unavailable with the underlying reason instead of failing
the whole page.
"""

from copy import deepcopy
from dataclasses import asdict

from dcf_code import DCFAssumptions
from dcf_loader import ProviderError, ticker_symbol
from suite_views import suite_assumptions, suite_evaluate


def baseline_dcf_assumptions(doc, wacc):
    rows = doc["historical"]

    def average(key):
        values = [r[key] / r["revenue"] for r in rows]
        return sum(values) / len(values)

    return DCFAssumptions(
        revenue_growth_rates=[0.05] * 5,
        terminal_growth_rate=0.02,
        wacc_override=wacc,
        terminal_mode="template",
        ebit_margins=[average("ebit")] * 5,
        da_margins=[average("d_and_a")] * 5,
        capex_margins=[average("capex")] * 5,
        nwc_margins=[average("nwc")] * 5,
        tax_rates=[rows[-1]["tax_rate"]] * 5,
        net_income_margins=[average("net_income")] * 5,
        book_value_margins=[average("book_value")] * 5,
    )


def football_field(ticker, asof=None):
    from auto_loading import load_method
    from app import evaluate

    symbol = ticker_symbol(ticker)
    bundle = load_method("dcf", symbol, asof)
    doc = bundle["financials"]
    costs = bundle["load_summary"].get("capital_costs", {})
    wacc = costs.get("wacc") or 0.065
    dcf_assumptions = baseline_dcf_assumptions(doc, wacc)
    lanes = []
    try:
        result = evaluate(deepcopy(doc), deepcopy(dcf_assumptions))
        lanes.append(
            {
                "method": "dcf",
                "label": "DCF intrinsic (today)",
                "value": result["intrinsic_value"],
                "detail": f"WACC {result['wacc']:.1%}, g {result['terminal_growth']:.1%}",
                "warnings": result["warnings"][:2],
            }
        )
        lanes.append(
            {
                "method": "dcf",
                "label": "DCF 12-month target",
                "value": result["target_price_12m"],
                "detail": "Scenario with year-one overrides",
                "warnings": [],
            }
        )
    except ValueError as exc:
        lanes.append({"method": "dcf", "label": "DCF", "value": None,
                      "detail": str(exc), "warnings": []})
        return _packet(doc, lanes, bundle)
    try:
        ddm_bundle = load_method("ddm", symbol, doc["valuation_date"], snapshot=doc)
        ddm_doc = ddm_bundle["financials"]
        ddm_a = suite_assumptions(
            "ddm",
            {
                "dividend_growth_rates": [0.05] * 5,
                "required_return": costs.get("cost_of_equity", 0.07),
                "terminal_growth_rate": 0.02,
            },
        )
        ddm_result = suite_evaluate("ddm", ddm_doc, ddm_a)
        lanes.append(
            {
                "method": "ddm",
                "label": "DDM intrinsic (today)",
                "value": ddm_result["intrinsic_value"],
                "detail": "Common dividends only",
                "warnings": [],
            }
        )
        lanes.append(
            {
                "method": "ddm",
                "label": "DDM 12-month (ex-div)",
                "value": ddm_result["target_price_12m"],
                "detail": "Excludes the first dividend",
                "warnings": [],
            }
        )
    except (ProviderError, ValueError) as exc:
        lanes.append(
            {
                "method": "ddm",
                "label": "DDM",
                "value": None,
                "detail": str(exc),
                "warnings": [],
            }
        )
    try:
        rel_bundle = load_method(
            "relative",
            symbol,
            doc["valuation_date"],
            snapshot=doc,
            forecast_assumptions=deepcopy(dcf_assumptions),
        )
        rel_doc = rel_bundle["financials"]
        included = [
            k
            for k in ["ev_revenue", "ev_ebitda", "pe"]
            if rel_doc["target"]["forward"][
                {"ev_revenue": "revenue", "ev_ebitda": "ebitda", "pe": "net_income"}[k]
            ]
            > 0
            and any(
                p["multiples"][k] is not None and p["multiples"][k] > 0
                for p in rel_doc["comparables"]
            )
        ]
        if not included:
            raise ValueError("No usable peer multiples for this ticker.")
        rel_result = suite_evaluate(
            "relative", rel_doc,
            suite_assumptions("relative", {"included_methods": included}),
        )
        lanes.append(
            {
                "method": "relative",
                "label": f"Relative 12-month ({len(included)} methods)",
                "value": rel_result["target_price_12m"],
                "detail": "Equal-weighted peer means",
                "warnings": [],
            }
        )
    except (ProviderError, ValueError) as exc:
        lanes.append(
            {
                "method": "relative",
                "label": "Relative",
                "value": None,
                "detail": str(exc),
                "warnings": [],
            }
        )
    return _packet(doc, lanes, bundle)


def _packet(doc, lanes, bundle):
    values = [lane["value"] for lane in lanes
              if isinstance(lane["value"], (int, float))]
    peak = max(values + [doc["market"]["price"], 0.01])
    for lane in lanes:
        lane["share"] = lane["value"] / peak if isinstance(lane["value"], (int, float)) else 0
        if isinstance(lane["value"], (int, float)):
            lane["upside"] = lane["value"] / doc["market"]["price"] - 1
        else:
            lane["upside"] = None
    return {
        "ticker": doc["company"]["ticker"],
        "company_name": doc["company"]["name"],
        "valuation_date": doc["valuation_date"],
        "market_price": doc["market"]["price"],
        "price_as_of": doc["market"]["price_as_of"],
        "source": doc["source"]["name"],
        "is_demo": doc["source"]["kind"] == "synthetic"
        or doc["source"].get("origin_kind") == "synthetic",
        "lanes": lanes,
        "load_summary": bundle["load_summary"],
        "assumptions": asdict(baseline_dcf_assumptions(
            doc, bundle["load_summary"].get("capital_costs", {}).get("wacc") or 0.065)),
    }
