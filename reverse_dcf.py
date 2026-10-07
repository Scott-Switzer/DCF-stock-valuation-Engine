"""Reverse DCF: what assumption does today's market price imply?

Holds every assumption fixed except one uniform driver (revenue growth
or EBIT margin) and bisects until intrinsic value equals the market
price. Reports unsolvable and boundary cases explicitly instead of a
precise-looking number.
"""

from copy import deepcopy
from dataclasses import replace

BOUNDS = {
    "revenue_growth": (-0.5, 1.0),
    "ebit_margin": (-1.0, 1.0),
}
LABELS = {
    "revenue_growth": "uniform annual revenue growth",
    "ebit_margin": "uniform EBIT margin",
}
ITERATIONS = 60


def _intrinsic(doc, assumptions):
    from dcf_code import DCFModel
    from dcf_loader import parse_document

    return DCFModel(parse_document(deepcopy(doc)), deepcopy(assumptions)).calculate()[
        "intrinsic_value"
    ]


def _with_driver(assumptions, driver, value):
    if driver == "revenue_growth":
        return replace(assumptions, revenue_growth_rates=[value] * 5)
    return replace(assumptions, ebit_margins=[value] * 5)


def solve(doc, assumptions, price, driver="revenue_growth"):
    if driver not in BOUNDS:
        raise ValueError("Solve for revenue_growth or ebit_margin.")
    if not isinstance(price, (int, float)) or price <= 0:
        raise ValueError("A positive market price is required.")
    lo, hi = BOUNDS[driver]

    def evaluable(value):
        try:
            return _intrinsic(doc, _with_driver(assumptions, driver, value))
        except ValueError:
            return None

    low_value, high_value = evaluable(lo), evaluable(hi)
    for _ in range(12):
        if low_value is None:
            lo += (hi - lo) / 4
            low_value = evaluable(lo)
        if high_value is None:
            hi -= (hi - lo) / 4
            high_value = evaluable(hi)
        if low_value is not None and high_value is not None:
            break
    if low_value is None or high_value is None:
        return {
            "driver": driver,
            "status": "unsolvable",
            "detail": (
                "The model cannot produce a valuation anywhere in the "
                f"{LABELS[driver]} range. Revise the fixed assumptions first."
            ),
        }
    if price < low_value:
        return {
            "driver": driver,
            "status": "below_range",
            "detail": (
                f"Even at the {LABELS[driver]} floor ({lo:.0%}), the model "
                f"values the share at ${low_value:,.2f} — above the ${price:,.2f} "
                "market price. The market implies deeper distress than this "
                "model range covers."
            ),
        }
    if price > high_value:
        return {
            "driver": driver,
            "status": "above_range",
            "detail": (
                f"Even at the {LABELS[driver]} ceiling ({hi:.0%}), the model "
                f"values the share at ${high_value:,.2f} — below the ${price:,.2f} "
                "market price. The market implies optimism beyond this "
                "model range."
            ),
        }
    for _ in range(ITERATIONS):
        mid = (lo + hi) / 2
        try:
            value = _intrinsic(doc, _with_driver(assumptions, driver, mid))
        except ValueError as exc:
            return {"driver": driver, "status": "unsolvable", "detail": str(exc)}
        if value < price:
            lo = mid
        else:
            hi = mid
    solved = (lo + hi) / 2
    rows = doc["historical"]
    if driver == "revenue_growth":
        history = [
            rows[i + 1]["revenue"] / rows[i]["revenue"] - 1 for i in range(len(rows) - 1)
        ]
    else:
        history = [r["ebit"] / r["revenue"] for r in rows]
    mean_history = sum(history) / len(history)
    return {
        "driver": driver,
        "status": "solved",
        "implied": solved,
        "market_price": price,
        "historical": history,
        "historical_mean": mean_history,
        "detail": (
            f"The ${price:,.2f} market price implies {solved:.1%} {LABELS[driver]}, "
            f"against a historical mean of {mean_history:.1%}."
        ),
    }
