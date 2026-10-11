"""Independent CUIG arithmetic reference, not a production valuation engine.

Only stdlib imports are allowed here. Callers supply validated observations and
explicit assumptions. Agreement establishes arithmetic parity under shared
inputs, not the accuracy of financial observations or an investment conclusion.
"""

import math


def reference_dcf(doc, assumptions):
    rows = doc["historical"]
    bridge = doc["bridge"]
    wacc = assumptions["wacc_override"]
    growth = assumptions["terminal_growth_rate"]
    if wacc is None or wacc <= growth:
        raise ValueError("Reference requires explicit WACC greater than terminal growth.")
    if len(assumptions["revenue_growth_rates"]) != 5:
        raise ValueError("Reference requires five forecast years.")

    def driver(name, field):
        explicit = assumptions.get(name)
        if explicit is not None:
            if len(explicit) != 5:
                raise ValueError(f"{name} requires five values.")
            return explicit
        return [sum(r[field] / r["revenue"] for r in rows) / len(rows)] * 5

    margins = driver("ebit_margins", "ebit")
    da = driver("da_margins", "d_and_a")
    capex = driver("capex_margins", "capex")
    nwc = driver("nwc_margins", "nwc")
    taxes = assumptions.get("tax_rates") or [rows[-1]["tax_rate"]] * 5
    revenue, previous_nwc = rows[-1]["revenue"], rows[-1]["nwc"]
    flows, nopats = [], []
    for i, rate in enumerate(assumptions["revenue_growth_rates"]):
        revenue *= 1 + rate
        nopat = revenue * margins[i] * (1 - taxes[i])
        current_nwc = revenue * nwc[i]
        flows.append(nopat + revenue * (da[i] - capex[i]) - current_nwc + previous_nwc)
        nopats.append(nopat)
        previous_nwc = current_nwc
    if assumptions.get("terminal_mode", "template") == "normalized":
        roic = assumptions["terminal_roic"]
        if growth < 0 or growth > roic:
            raise ValueError("Normalized terminal growth must be between zero and ROIC.")
        terminal_flow = nopats[-1] * (1 + growth) * (1 - growth / roic)
    else:
        terminal_flow = flows[-1] * (1 + growth)
    if terminal_flow <= 0:
        raise ValueError("Terminal cash flow is nonpositive under the explicit assumptions.")
    terminal = terminal_flow / (wacc - growth)
    ev = sum(flow / (1 + wacc) ** (i + 1) for i, flow in enumerate(flows))
    ev += terminal / (1 + wacc) ** 5
    ev12 = sum(flow / (1 + wacc) ** i for i, flow in enumerate(flows[1:], 1))
    ev12 += terminal / (1 + wacc) ** 4
    debt = bridge["short_term_debt"] + bridge["long_term_debt"]
    equity = (ev - debt + bridge["cash"] - bridge["preferred_equity"]
              - bridge["minority_interest"] + bridge["other_nonoperating_assets"])

    def future(key, default):
        value = assumptions.get(key)
        return default if value is None else value

    equity12 = (ev12 - future("future_debt", debt) + future("future_cash", bridge["cash"])
                - future("future_preferred", bridge["preferred_equity"])
                - future("future_minority", bridge["minority_interest"])
                + future("future_other_assets", bridge["other_nonoperating_assets"]))
    result = {
        "ufcf": flows,
        "terminal_fcff": terminal_flow,
        "terminal_value": terminal,
        "enterprise_value": ev,
        "equity_value": equity,
        "intrinsic_value": max(0, equity) / doc["market"]["diluted_shares"],
        "enterprise_value_12m": ev12,
        "equity_value_12m": equity12,
        "target_price_12m": max(0, equity12) / future("future_shares", doc["market"]["diluted_shares"]),
    }
    if not all(math.isfinite(v) for key, value in result.items()
               for v in (value if isinstance(value, list) else [value])):
        raise ValueError("Nonfinite reference valuation.")
    return result


def compare_result(reference, actual, rel_tol=1e-9, abs_tol=1e-6):
    """Return all missing, nonfinite or mismatched outputs, including each FCFF."""
    differences = []
    pairs = [(key, value, actual.get(key)) for key, value in reference.items() if key != "ufcf"]
    projections = actual.get("projections") or []
    pairs += [(f"ufcf.{i + 1}", value,
               projections[i].get("UFCF") if i < len(projections) else None)
              for i, value in enumerate(reference["ufcf"])]
    for field, expected, observed in pairs:
        valid = (isinstance(observed, (int, float)) and not isinstance(observed, bool)
                 and math.isfinite(observed))
        if not valid or not math.isclose(expected, observed, rel_tol=rel_tol, abs_tol=abs_tol):
            safe_observed = observed
            if isinstance(observed, float) and not math.isfinite(observed):
                safe_observed = str(observed)
            elif not valid and observed is not None and not isinstance(observed, (str, bool)):
                safe_observed = repr(observed)
            differences.append({"field": field, "expected": expected, "actual": safe_observed})
    return differences
