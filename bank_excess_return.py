"""Bank / financial-institution valuation: equity excess-return model.

Damodaran's eqexret.xls framework for financial service firms, implemented
independently (the workbook is cataloged but not extracted, so this lane is
INDEPENDENTLY_VERIFIED_NOT_WORKBOOK_CONFORMED):

    Book_t        = Book_{t-1} + NI_t - Dividends_t        (clean surplus)
    NI_t          = Book_{t-1} * ROE_t                      (earnings on opening capital)
    ExcessRet_t   = NI_t - k_e * Book_{t-1} = Book_{t-1} * (ROE_t - k_e)
    TV            = ExcessRet_n * (1 + g) / (k_e - g)       (terminal excess return)
    Equity        = Book_0 + sum ExcessRet_t / (1+k_e)^t + TV / (1+k_e)^n

Industrial-company FCFF/WACC machinery is deliberately NOT applied to banks:
debt is raw material, not financing, so an enterprise-value DCF is meaningless
here. The value basis is equity from the first line.

Bank-specific discipline (validated, never assumed):

* **Tangible common book equity** is the capital base. Preferred claims and
  goodwill/intangibles must be stripped explicitly; the basis is labeled in the
  output (`TANGIBLE_COMMON` vs `TOTAL_BOOK`), never silently mixed.
* **Clean surplus** book roll-forward with an explicit payout ratio; stock
  issuance and buybacks are out of scope and labeled as such.
* **Terminal excess returns** must satisfy a sustainability check:
  terminal growth cannot exceed sustainable growth (retention x ROE) without an
  explicit ``allow_unsustainable_terminal_growth`` override, which is recorded
  in the warnings. ``k_e > g`` is always required.
* **Regulatory capital constraints** (CET1, total risk-based capital) enter as
  explicit metadata and an optional minimum-retention constraint supplied by
  the caller or the FDIC pilot; they are never inferred from ratios whose
  denominators (RWA) are not in the verified field set.
* **Credit quality / loan-loss provisions** are an explicit optional earnings
  drag supplied per year. The FDIC pilot quarantines the provision field
  (SOURCE_FIELD_UNAVAILABLE); nothing is imputed here either.
"""

import math

SCHEMA_VERSION = "bank-excess-return-v1"
FORECAST_YEARS = 5
TANGIBLE = "TANGIBLE_COMMON"
TOTAL_BOOK = "TOTAL_BOOK"


def _finite(value, name, lo=None, hi=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number.")
    value = float(value)
    if lo is not None and value < lo:
        raise ValueError(f"{name} must be at least {lo}.")
    if hi is not None and value > hi:
        raise ValueError(f"{name} must be at most {hi}.")
    return value


def bank_excess_return_value(
    net_income,
    *,
    opening_book,
    cost_of_equity,
    terminal_growth,
    shares,
    payout_ratio=0.0,
    equity_basis=TANGIBLE,
    preferred_equity=0.0,
    intangible_assets=None,
    credit_provision_drag=None,
    minimum_retention=None,
    regulatory_capital=None,
    allow_unsustainable_terminal_growth=False,
):
    """Equity value from forecast excess returns over book capital.

    ``net_income``: five forecast net-income values (or None per year when that
    year cannot be forecast — such a year fails explicitly rather than
    defaulting to zero).
    ``credit_provision_drag``: optional five-year explicit provision amounts
    subtracted from net income; None means unmodeled, which is reported.
    ``regulatory_capital``: optional metadata dict (e.g. cet1_ratio,
    total_risk_based_capital_ratio, brokered_deposit_share) carried into the
    output for constraint review; never used to impute values.
    """
    if equity_basis not in (TANGIBLE, TOTAL_BOOK):
        raise ValueError("equity_basis must be TANGIBLE_COMMON or TOTAL_BOOK.")
    if not isinstance(net_income, (list, tuple)) or len(net_income) != FORECAST_YEARS:
        raise ValueError("Bank excess-return valuation needs exactly five forecast years.")
    if any(v is None for v in net_income):
        raise ValueError(
            "A forecast year is missing net income; banks need explicit earnings forecasts, "
            "never a substituted zero."
        )
    ni = [_finite(v, "Net income") for v in net_income]

    if equity_basis == TANGIBLE and intangible_assets is not None:
        intang = _finite(intangible_assets, "Intangible assets", 0.0)
    elif equity_basis == TANGIBLE and intangible_assets is None:
        raise ValueError(
            "TANGIBLE_COMMON basis requires explicit intangible_assets (use 0.0 when the "
            "issuer reports none); total book equity must not be silently used as tangible."
        )
    else:
        intang = 0.0
    book = _finite(opening_book, "Opening book equity")
    if equity_basis == TANGIBLE:
        book -= intang
    if book <= 0:
        raise ValueError(
            "Opening common book equity must be positive after the tangible adjustment; "
            "negative equity is a distress case outside this model's domain."
        )
    pref = _finite(preferred_equity, "Preferred equity", 0.0)
    if pref > 0:
        raise ValueError(
            "Preferred claims are not part of common excess returns; strip preferred equity "
            "before calling this model."
        )

    ke = _finite(cost_of_equity, "Cost of equity", 0.001, 1.0)
    g = _finite(terminal_growth, "Terminal growth", -0.5, 0.5)
    shares = _finite(shares, "Diluted shares", 0.0000001)
    payout = _finite(payout_ratio, "Payout ratio", 0.0, 1.0)
    retention = 1.0 - payout
    if ke <= g:
        raise ValueError(
            "TERMINAL_GROWTH_NOT_FEASIBLE: cost of equity must exceed terminal growth."
        )

    drag = None
    if credit_provision_drag is not None:
        if not isinstance(credit_provision_drag, (list, tuple)) or len(credit_provision_drag) != FORECAST_YEARS:
            raise ValueError("credit_provision_drag must be five annual amounts or None.")
        drag = [_finite(v, "Credit provision drag", 0.0) for v in credit_provision_drag]

    min_retention = None
    if minimum_retention is not None:
        min_retention = _finite(minimum_retention, "Minimum retention", 0.0, 1.0)
        if retention < min_retention:
            raise ValueError(
                "CAPITAL_CONSTRAINT_VIOLATION: the payout ratio leaves retention "
                f"{retention:.1%} below the required minimum {min_retention:.1%} to hold "
                "regulatory capital ratios."
            )

    rows = []
    pv_excess = 0.0
    book_t = book
    for year in range(1, FORECAST_YEARS + 1):
        earnings = ni[year - 1]
        if drag is not None:
            earnings -= drag[year - 1]
        roe = earnings / book_t
        excess = earnings - ke * book_t
        dividends = earnings * payout
        closing = book_t + earnings - dividends
        df = 1.0 / (1.0 + ke) ** year
        pv_excess += excess * df
        rows.append({
            "year": year,
            "opening_book": book_t,
            "net_income": earnings,
            "roe": roe,
            "excess_return": excess,
            "dividends": dividends,
            "closing_book": closing,
            "discount_factor": df,
            "pv_excess_return": excess * df,
        })
        book_t = closing

    last = rows[-1]
    terminal_excess = last["excess_return"] * (1.0 + g)
    terminal_value = terminal_excess / (ke - g)
    pv_terminal = terminal_value * last["discount_factor"]

    # Sustainability: perpetual excess-return growth cannot exceed retention x ROE.
    sustainable_growth = retention * last["roe"]
    warnings = [
        "Banks are valued on equity excess returns over book capital; debt is operating "
        "funding, so no enterprise-value bridge or WACC discounting is applied.",
        f"Book-equity basis is {equity_basis}; the basis is part of the answer.",
    ]
    if g > sustainable_growth:
        if not allow_unsustainable_terminal_growth:
            raise ValueError(
                "TERMINAL_GROWTH_NOT_SUSTAINABLE: terminal growth "
                f"{g:.1%} exceeds sustainable growth {sustainable_growth:.1%} "
                "(retention x ROE). Pass allow_unsustainable_terminal_growth=True to "
                "override explicitly, or lower the terminal growth."
            )
        warnings.append(
            f"Terminal growth {g:.1%} exceeds sustainable growth {sustainable_growth:.1%} "
            "(retention x ROE); the override is explicit and the terminal value is "
            "correspondingly optimistic."
        )
    if drag is None:
        warnings.append(
            "Credit provision / loan-loss costs are NOT modeled (the FDIC provision field is "
            "unavailable in the verified pilot); earnings are pre-credit-cost as forecast."
        )
    else:
        warnings.append(
            "Credit provision drag is an explicit user-supplied schedule; the FDIC pilot "
            "quarantines provision data and nothing is imputed from aggregates."
        )
    if min_retention is not None:
        warnings.append(
            f"Regulatory capital constraint enforced: retention {retention:.1%} >= "
            f"minimum {min_retention:.1%}."
        )
    warnings.append(
        "Clean surplus assumes no stock issuance or buybacks in the forecast horizon."
    )

    equity_value = book + pv_excess + pv_terminal
    return {
        "schema_version": SCHEMA_VERSION,
        "method": "bank_excess_return",
        "valuation_basis": "equity",
        "company_type": "financial_institution",
        "equity_basis": equity_basis,
        "opening_tangible_book": book,
        "equity_value": equity_value,
        "intrinsic_value": equity_value / shares,
        "pv_explicit_excess_returns": pv_excess,
        "pv_terminal_excess_return": pv_terminal,
        "terminal_excess_return": terminal_excess,
        "terminal_value": terminal_value,
        "cost_of_equity": ke,
        "terminal_growth": g,
        "payout_ratio": payout,
        "retention_ratio": retention,
        "sustainable_growth": sustainable_growth,
        "diluted_shares": shares,
        "credit_provision_mode": "EXPLICIT_SCHEDULE" if drag is not None else "NOT_MODELED",
        "regulatory_capital_metadata": dict(regulatory_capital or {}),
        "rows": rows,
        "warnings": warnings,
    }
