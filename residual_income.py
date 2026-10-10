"""Residual income valuation (per-share equity value).

Value = opening book + PV(NI_t - ke x opening book_t) + PV(terminal residual).

Book value rolls forward under clean surplus: closing book = opening book +
net income - dividends, where dividends = payout ratio x net income. The
terminal residual grows at the terminal rate. Preferred and noncontrolling
claims are not modeled here; the readiness check blocks those cases.
"""

import math

FORECAST_YEARS = 5


def _finite(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number.")
    return float(value)


def residual_income_value(
    net_income,
    opening_book,
    cost_of_equity,
    terminal_growth,
    shares,
    payout_ratio=0.0,
):
    if not isinstance(net_income, (list, tuple)) or len(net_income) != FORECAST_YEARS:
        raise ValueError("Residual income needs exactly five forecast years of net income.")
    net_income = [_finite(v, "Net income") for v in net_income]
    opening_book = _finite(opening_book, "Opening book value")
    ke = _finite(cost_of_equity, "Cost of equity")
    g = _finite(terminal_growth, "Terminal growth")
    shares = _finite(shares, "Diluted shares")
    payout = _finite(payout_ratio, "Payout ratio")
    if shares <= 0:
        raise ValueError("Diluted shares must be positive.")
    if not 0 <= payout <= 1:
        raise ValueError("Payout ratio must be between 0 and 1.")
    if not 0 < ke < 1:
        raise ValueError("Cost of equity must be between 0% and 100%.")
    if ke <= g:
        raise ValueError("Cost of equity must exceed terminal growth.")

    rows = []
    book = opening_book
    pv_residuals = 0.0
    for year, ni in enumerate(net_income, start=1):
        residual = ni - ke * book
        pv_residuals += residual / (1 + ke) ** year
        book = book + ni * (1 - payout)
        rows.append(
            {
                "year": year,
                "net_income": ni,
                "residual_income": residual,
                "book_value": book,
            }
        )

    terminal_residual = rows[-1]["residual_income"] * (1 + g) / (ke - g)
    pv_terminal = terminal_residual / (1 + ke) ** FORECAST_YEARS
    equity_value = opening_book + pv_residuals + pv_terminal
    return {
        "intrinsic_value": equity_value / shares,
        "equity_value": equity_value,
        "pv_residuals": pv_residuals,
        "pv_terminal": pv_terminal,
        "cost_of_equity": ke,
        "terminal_growth": g,
        "payout_ratio": payout,
        "rows": rows,
        "warnings": [
            "Residual income assumes clean surplus: book value rolls forward with net "
            "income less dividends, not the DCF book-value margin.",
            "Preferred and noncontrolling claims are not modeled by residual income.",
        ],
    }
