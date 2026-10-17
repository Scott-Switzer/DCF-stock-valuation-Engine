"""FCFE valuation: equity cash flow discounted at the cost of equity.

    FCFE_t = Net Income_t + D&A_t - CapEx_t - dNWC_t + Net Borrowing_t

Forecast rows come from the same DCFModel.forecast_cash_flows() drivers as the
FCFF lane, so FCFF and FCFE share revenue, margin, reinvestment and tax
assumptions. Differences in value are then attributable only to the financing
line and the discount rate.

Financial rules enforced here:

* FCFE is an EQUITY cash flow: it is discounted at the cost of equity, never at
  WACC, and the resulting value is an equity value. Net debt is NOT subtracted
  again.
* Net borrowing is explicit per year. ``net_borrowing=None`` (the default)
  means an all-internal financing policy of zero net borrowing and is reported
  as such; it is never inferred from historical debt flows.
* Terminal value is Gordon on the final-year FCFE and requires
  ``cost_of_equity > terminal_growth`` and positive terminal FCFE. Unstable
  terminal inputs fail explicitly instead of returning a precise-looking number.
* The output never overwrites company-reported fundamentals or other model
  results; it is one lane among several.
"""

import math

SCHEMA_VERSION = "fcfe-equity-v1"
FORECAST_YEARS = 5


def _finite(value, name, lo=None, hi=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number.")
    value = float(value)
    if lo is not None and value < lo:
        raise ValueError(f"{name} must be at least {lo}.")
    if hi is not None and value > hi:
        raise ValueError(f"{name} must be at most {hi}.")
    return value


def fcfe_value(
    projections,
    *,
    cost_of_equity,
    terminal_growth,
    shares,
    net_borrowing=None,
    market_price=None,
):
    """Equity value from forecast FCFE.

    ``projections`` are the five DCFModel forecast rows (each with Net Income,
    D&A, CapEx and Change NWC). ``net_borrowing`` is a single annual amount
    applied to every year, or a list of five annual amounts; None means zero net
    borrowing with an explicit policy label.
    """
    if not isinstance(projections, (list, tuple)) or len(projections) != FORECAST_YEARS:
        raise ValueError("FCFE needs exactly five forecast years.")
    ke = _finite(cost_of_equity, "Cost of equity", 0.001, 1.0)
    g = _finite(terminal_growth, "Terminal growth", -0.5, 0.5)
    shares = _finite(shares, "Diluted shares", 0.0000001)
    if ke <= g:
        raise ValueError(
            "TERMINAL_GROWTH_NOT_FEASIBLE: cost of equity must exceed terminal growth."
        )

    if net_borrowing is None:
        borrowing = [0.0] * FORECAST_YEARS
        borrowing_policy = "ZERO_NET_BORROWING_ASSUMED"
    elif isinstance(net_borrowing, (int, float)) and not isinstance(net_borrowing, bool):
        borrowing = [_finite(net_borrowing, "Net borrowing", -1e12, 1e12)] * FORECAST_YEARS
        borrowing_policy = "CONSTANT_NET_BORROWING"
    elif isinstance(net_borrowing, (list, tuple)) and len(net_borrowing) == FORECAST_YEARS:
        borrowing = [_finite(v, "Net borrowing", -1e12, 1e12) for v in net_borrowing]
        borrowing_policy = "EXPLICIT_ANNUAL_NET_BORROWING"
    else:
        raise ValueError("Net borrowing must be None, one annual amount, or five annual amounts.")

    rows = []
    pv_explicit = 0.0
    for i, proj in enumerate(projections):
        year = i + 1
        if not isinstance(proj, dict):
            raise ValueError("Each forecast row must be an object.")
        net_income = _finite(proj.get("Net Income"), "Net income")
        da = _finite(proj.get("D&A"), "D&A", 0.0)
        capex = _finite(proj.get("CapEx"), "CapEx", 0.0)
        change_nwc = _finite(proj.get("Change NWC"), "Change in NWC")
        nb = borrowing[i]
        fcfe = net_income + da - capex - change_nwc + nb
        discount = 1.0 / (1.0 + ke) ** year
        pv = fcfe * discount
        pv_explicit += pv
        rows.append(
            {
                "year": year,
                "net_income": net_income,
                "d_and_a": da,
                "capex": capex,
                "change_nwc": change_nwc,
                "net_borrowing": nb,
                "fcfe": fcfe,
                "discount_factor": discount,
                "pv_fcfe": pv,
            }
        )

    terminal_fcfe = rows[-1]["fcfe"] * (1.0 + g)
    if terminal_fcfe <= 0:
        raise ValueError(
            "TERMINAL_FCFE_NOT_POSITIVE: the terminal-year FCFE is not positive, so a "
            "Gordon terminal value is not meaningful. Revise the financing or "
            "reinvestment policy first."
        )
    terminal_value = terminal_fcfe / (ke - g)
    pv_terminal = terminal_value * rows[-1]["discount_factor"]
    equity_value = pv_explicit + pv_terminal
    intrinsic = equity_value / shares

    warnings = [
        "FCFE is discounted at the cost of equity and the result is an equity value; "
        "net debt is not subtracted again.",
        "Net borrowing is an explicit financing-policy assumption, not a forecast of "
        "historical borrowing behavior.",
    ]
    if borrowing_policy == "ZERO_NET_BORROWING_ASSUMED":
        warnings.append(
            "No net borrowing information was provided: the forecast assumes zero net "
            "borrowing in every year."
        )
    if any(b > 0 for b in borrowing) and borrowing_policy != "ZERO_NET_BORROWING_ASSUMED":
        warnings.append(
            "Positive net borrowing raises FCFE now at the cost of higher leverage later; "
            "the terminal value does not model an eventual debt repayment."
        )
    if any(r["fcfe"] < 0 for r in rows):
        warnings.append(
            "At least one forecast year has negative FCFE; the equity value reflects "
            "financing needs in those years."
        )

    result = {
        "schema_version": SCHEMA_VERSION,
        "method": "fcfe",
        "valuation_basis": "equity",
        "equity_value": equity_value,
        "intrinsic_value": intrinsic,
        "pv_explicit_forecast": pv_explicit,
        "pv_terminal": pv_terminal,
        "terminal_value": terminal_value,
        "terminal_fcfe": terminal_fcfe,
        "cost_of_equity": ke,
        "terminal_growth": g,
        "diluted_shares": shares,
        "net_borrowing_policy": borrowing_policy,
        "rows": rows,
        "warnings": warnings,
    }
    if market_price is not None:
        price = _finite(market_price, "Market price", 0.0000001)
        result["current_price"] = price
        result["upside"] = intrinsic / price - 1
    return result
