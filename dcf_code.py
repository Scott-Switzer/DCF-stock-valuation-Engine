"""Deterministic five-period FCFF model, aligned with CUIG DCF - GGM.

All amounts and shares use absolute units. Rates are decimals. No network I/O.
"""

from dataclasses import dataclass, field
import math
from statistics import mean
from typing import List, Optional


def number(value, label, minimum=None, maximum=None):
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite number.")
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError):
        raise ValueError(f"{label} must be a finite number.") from None
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number.")
    if minimum is not None and result < minimum or maximum is not None and result > maximum:
        if minimum is not None and maximum is not None:
            raise ValueError(f"{label} must be between {minimum} and {maximum}.")
        if minimum is not None:
            raise ValueError(f"{label} must be at least {minimum}.")
        raise ValueError(f"{label} must be at most {maximum}.")
    return result


@dataclass
class DCFAssumptions:
    revenue_growth_rates: List[float]
    terminal_growth_rate: float
    projection_years: int = 5
    wacc_override: Optional[float] = None
    ebit_margins: Optional[List[float]] = None
    da_margins: Optional[List[float]] = None
    capex_margins: Optional[List[float]] = None
    nwc_margins: Optional[List[float]] = None
    tax_rates: Optional[List[float]] = None
    net_income_margins: Optional[List[float]] = None
    book_value_margins: Optional[List[float]] = None
    terminal_mode: str = "template"
    terminal_roic: Optional[float] = None
    future_debt: Optional[float] = None
    future_cash: Optional[float] = None
    future_shares: Optional[float] = None
    future_preferred: Optional[float] = None
    future_minority: Optional[float] = None
    future_other_assets: Optional[float] = None

    def validate(self):
        if self.projection_years != 5:
            raise ValueError("This CUIG model requires exactly five projection years.")
        self.terminal_growth_rate = number(self.terminal_growth_rate, "Terminal growth", -0.1, 0.15)
        limits = {
            "revenue_growth_rates": (-0.5, 1),
            "ebit_margins": (-1, 1),
            "da_margins": (0, 1),
            "capex_margins": (0, 1),
            "nwc_margins": (-2, 2),
            "tax_rates": (0, 1),
            "net_income_margins": (-1, 1),
            "book_value_margins": (-10, 10),
        }
        for name, (lo, hi) in limits.items():
            values = getattr(self, name)
            if values is None and name != "revenue_growth_rates":
                continue
            if not isinstance(values, (list, tuple)) or len(values) != 5:
                raise ValueError(f"{name} requires five annual rates.")
            setattr(
                self,
                name,
                [number(v, f"{name} year {i + 1}", lo, hi) for i, v in enumerate(values)],
            )
        if self.wacc_override is not None:
            self.wacc_override = number(self.wacc_override, "WACC", 0.001, 0.5)
        if not isinstance(self.terminal_mode, str) or self.terminal_mode not in {
            "template",
            "normalized",
        }:
            raise ValueError("Terminal mode must be template or normalized.")
        if self.terminal_mode == "normalized":
            self.terminal_roic = number(self.terminal_roic, "Terminal ROIC", 0.001, 1)
            if self.terminal_growth_rate < 0 or self.terminal_growth_rate > self.terminal_roic:
                raise ValueError(
                    "Normalized terminal growth must be nonnegative and no greater than ROIC."
                )
        for name in [
            "future_debt",
            "future_cash",
            "future_shares",
            "future_preferred",
            "future_minority",
            "future_other_assets",
        ]:
            value = getattr(self, name)
            if value is not None:
                setattr(self, name, number(value, name, 0))
        if self.future_shares == 0:
            raise ValueError("Future diluted shares must be positive.")


@dataclass
class FinancialData:
    # Retains the original public Python data type for existing CLI clients.
    years: List[str]
    revenue: List[float]
    ebit: List[float]
    ebitda: List[float]
    net_income: List[float]
    effective_tax_rate: List[float]
    interest_expense: List[float]
    current_assets: List[float]
    current_liabilities: List[float]
    cash_and_equivalents: List[float]
    short_term_debt: List[float]
    long_term_debt: List[float]
    total_debt: List[float]
    total_assets: List[float]
    total_liabilities: List[float]
    property_plant_equipment_net: List[float]
    preferred_equity: List[float]
    d_and_a: List[float]
    capex: List[float]
    preferred_dividends: List[float]
    shares_outstanding: float
    beta: float
    stock_price: float
    market_cap: float
    risk_free_rate: float
    market_return_rate: float
    nwc_override: Optional[List[float]] = None
    book_value_override: Optional[List[float]] = None
    minority_interest: float = 0.0
    other_nonoperating_assets: float = 0.0
    metadata: dict = field(default_factory=dict)
    # Set only by loaders for equity-only methods. FCFF DCF keeps the strict default.
    minority_may_be_negative: bool = False

    @property
    def nwc(self):
        if self.nwc_override is not None:
            return self.nwc_override
        return [
            (a - c) - (l - d)
            for a, c, l, d in zip(
                self.current_assets,
                self.cash_and_equivalents,
                self.current_liabilities,
                self.short_term_debt,
            )
        ]

    @property
    def book_value(self):
        if self.book_value_override is not None:
            return self.book_value_override
        return [a - l for a, l in zip(self.total_assets, self.total_liabilities)]

    def validate(self):
        if len(self.years) != 3 or any(not isinstance(y, str) or not y for y in self.years):
            raise ValueError("Exactly three historical fiscal periods are required.")
        if self.years != sorted(set(self.years)):
            raise ValueError("Historical fiscal periods must be unique and chronological.")
        for name in [
            "revenue",
            "ebit",
            "d_and_a",
            "capex",
            "effective_tax_rate",
            "net_income",
            "total_debt",
            "cash_and_equivalents",
            "preferred_equity",
            "short_term_debt",
            "long_term_debt",
            "total_assets",
            "total_liabilities",
        ]:
            values = getattr(self, name)
            if not isinstance(values, (list, tuple)) or len(values) != 3:
                raise ValueError(
                    f"{name} requires three aligned historical values; missing is not zero."
                )
            setattr(self, name, [number(v, name) for v in values])
        for name in ["nwc", "book_value"]:
            values = getattr(self, name)
            if len(values) != 3:
                raise ValueError(f"{name} must align with revenue periods.")
            for v in values:
                number(v, name)
        if any(r <= 0 for r in self.revenue):
            raise ValueError("Historical revenue must be positive.")
        if any(
            v < 0
            for n in ["d_and_a", "capex", "total_debt", "cash_and_equivalents", "preferred_equity"]
            for v in getattr(self, n)
        ):
            raise ValueError(
                "D&A, CapEx outflows, debt, cash and preferred claims must be nonnegative."
            )
        if any(t < 0 or t > 1 for t in self.effective_tax_rate):
            raise ValueError(
                "Historical tax rate needs normalization to a rate between 0 and 100%."
            )
        self.shares_outstanding = number(self.shares_outstanding, "Diluted shares", 0)
        if self.shares_outstanding <= 0:
            raise ValueError("Diluted shares must be positive.")
        self.stock_price = number(self.stock_price, "Current price", 0)
        if self.stock_price <= 0:
            raise ValueError("Current price must be positive.")
        number(
            self.minority_interest,
            "minority_interest",
            None if self.minority_may_be_negative else 0,
        )
        number(self.other_nonoperating_assets, "other_nonoperating_assets", 0)


class DCFModel:
    def __init__(self, data: FinancialData, assumptions: DCFAssumptions):
        self.data = data
        self.assumptions = assumptions
        self.wacc = 0.0
        self.projections = []
        self.calculation_log = []
        self.result = None

    def calculate_wacc(self):
        a, d = self.assumptions, self.data
        a.validate()
        d.validate()
        if a.wacc_override is not None:
            self.wacc = a.wacc_override
        else:
            rf = number(d.risk_free_rate, "Risk-free rate", 0, 0.5)
            rm = number(d.market_return_rate, "Expected market return", 0, 0.5)
            beta = number(d.beta, "Beta", -2, 5)
            equity = number(d.market_cap, "Market equity value", 0)
            debt = d.total_debt[-1]
            pref = d.preferred_equity[-1]
            if equity <= 0:
                raise ValueError("Market equity value must be positive for calculated WACC.")
            if debt and (not d.interest_expense or d.interest_expense[-1] is None):
                raise ValueError("Interest expense is missing. Enter a WACC override.")
            kd = number(d.interest_expense[-1], "Interest expense", 0) / debt if debt else 0
            if pref and (not d.preferred_dividends or d.preferred_dividends[-1] is None):
                raise ValueError("Preferred dividends are missing. Enter a WACC override.")
            kp = number(d.preferred_dividends[-1], "Preferred dividends", 0) / pref if pref else 0
            self.wacc = (
                equity * (rf + beta * (rm - rf))
                + debt * kd * (1 - d.effective_tax_rate[-1])
                + pref * kp
            ) / (equity + debt + pref)
        self.wacc = number(self.wacc, "WACC", 0.001, 0.5)
        if self.wacc <= a.terminal_growth_rate:
            raise ValueError("Terminal growth must be lower than WACC.")
        return self.wacc

    def forecast_cash_flows(self):
        d, a = self.data, self.assumptions
        d.validate()
        a.validate()
        drivers = {
            "ebit": a.ebit_margins or [mean(v / r for v, r in zip(d.ebit, d.revenue))] * 5,
            "da": a.da_margins or [mean(v / r for v, r in zip(d.d_and_a, d.revenue))] * 5,
            "capex": a.capex_margins or [mean(v / r for v, r in zip(d.capex, d.revenue))] * 5,
            "nwc": a.nwc_margins or [mean(v / r for v, r in zip(d.nwc, d.revenue))] * 5,
            "tax": a.tax_rates or [d.effective_tax_rate[-1]] * 5,
            "net_income": a.net_income_margins
            or [mean(v / r for v, r in zip(d.net_income, d.revenue))] * 5,
            "book_value": a.book_value_margins
            or [mean(v / r for v, r in zip(d.book_value, d.revenue))] * 5,
        }
        rev = d.revenue[-1]
        prev = d.nwc[-1]
        rows = []
        for i, g in enumerate(a.revenue_growth_rates):
            rev *= 1 + g
            ebit = rev * drivers["ebit"][i]
            tax = ebit * drivers["tax"][i]
            da = rev * drivers["da"][i]
            capex = rev * drivers["capex"][i]
            nwc = rev * drivers["nwc"][i]
            change = nwc - prev
            # Matches CUIG, including modeled tax benefits for loss-making periods.
            flow = ebit - tax + da - capex - change
            row = {
                "Year": i + 1,
                "Revenue": rev,
                "EBIT": ebit,
                "Taxes": tax,
                "NOPAT": ebit - tax,
                "D&A": da,
                "EBITDA": ebit + da,
                "Net Income": rev * drivers["net_income"][i],
                "Book Value": rev * drivers["book_value"][i],
                "CapEx": capex,
                "NWC": nwc,
                "Change NWC": change,
                "UFCF": flow,
            }
            for k, v in row.items():
                number(v, k)
            rows.append(row)
            prev = nwc
        self.drivers = drivers
        self.projections = rows
        return rows

    def _value(self, wacc, g):
        number(wacc, "WACC", 0.001, 0.5)
        number(g, "Terminal growth", -0.1, 0.15)
        if wacc <= g:
            raise ValueError("Terminal growth must be lower than WACC.")
        if not self.projections:
            self.forecast_cash_flows()
        a, d = self.assumptions, self.data
        rows = self.projections
        if a.terminal_mode == "normalized":
            if g < 0 or g > a.terminal_roic:
                raise ValueError("Terminal growth must not exceed terminal ROIC.")
            terminal_nopat = rows[-1]["NOPAT"] * (1 + g)
            terminal_flow = terminal_nopat * (1 - g / a.terminal_roic)
        else:
            terminal_flow = rows[-1]["UFCF"] * (1 + g)
        if terminal_flow <= 0:
            raise ValueError(
                "Terminal free cash flow must be positive. Revise normalized operations or use a different valuation model."
            )
        terminal_value = terminal_flow / (wacc - g)
        stage1 = sum(r["UFCF"] / (1 + wacc) ** r["Year"] for r in rows)
        terminal_pv = terminal_value / (1 + wacc) ** 5
        ev = stage1 + terminal_pv
        ev12 = (
            sum(r["UFCF"] / (1 + wacc) ** (r["Year"] - 1) for r in rows[1:])
            + terminal_value / (1 + wacc) ** 4
        )
        debt = d.total_debt[-1]
        cash = d.cash_and_equivalents[-1]
        pref = d.preferred_equity[-1]

        def choose(value, default):
            return default if value is None else value

        future = {
            "debt": choose(a.future_debt, debt),
            "cash": choose(a.future_cash, cash),
            "shares": choose(a.future_shares, d.shares_outstanding),
            "preferred": choose(a.future_preferred, pref),
            "minority": choose(a.future_minority, d.minority_interest),
            "other_assets": choose(a.future_other_assets, d.other_nonoperating_assets),
        }
        equity = ev - debt + cash - pref - d.minority_interest + d.other_nonoperating_assets
        equity12 = (
            ev12
            - future["debt"]
            + future["cash"]
            - future["preferred"]
            - future["minority"]
            + future["other_assets"]
        )
        result = {
            "wacc": wacc,
            "terminal_growth": g,
            "terminal_fcff": terminal_flow,
            "terminal_value": terminal_value,
            "stage1_pv": stage1,
            "terminal_pv": terminal_pv,
            "enterprise_value": ev,
            "equity_value": equity,
            "intrinsic_value": max(0, equity) / d.shares_outstanding,
            "stage1_pv_12m": ev12 - terminal_value / (1 + wacc) ** 4,
            "terminal_pv_12m": terminal_value / (1 + wacc) ** 4,
            "enterprise_value_12m": ev12,
            "equity_value_12m": equity12,
            "target_price_12m": max(0, equity12) / future["shares"],
            "terminal_value_share": terminal_pv / ev if ev > 0 else None,
            "future_bridge": future,
        }
        for k, v in result.items():
            if isinstance(v, (int, float)):
                number(v, k)
        return result

    def calculate(self):
        self.calculate_wacc()
        self.forecast_cash_flows()
        self.result = self._value(self.wacc, self.assumptions.terminal_growth_rate)
        for row in self.projections:
            row["PV UFCF"] = row["UFCF"] / (1 + self.wacc) ** row["Year"]
        warnings = []
        if self.result["terminal_value_share"] and self.result["terminal_value_share"] > 0.8:
            warnings.append("More than 80% of enterprise value comes from the terminal value.")
        if self.assumptions.terminal_growth_rate > 0.04:
            warnings.append("Terminal growth exceeds 4%; justify the perpetual growth assumption.")
        if any(r["EBIT"] < 0 for r in self.projections):
            warnings.append(
                "Taxes include modeled loss benefits, as in CUIG; assess whether these benefits can be realized."
            )
        if self.result["equity_value"] < 0:
            warnings.append(
                "Enterprise value is insufficient to cover senior claims. Common-share value is floored at zero."
            )
        if self.assumptions.terminal_mode == "template":
            warnings.append(
                "CUIG terminal convention grows year-five FCFF. Stable-growth reinvestment is not separately normalized."
            )
        warnings.append(
            "12-month target assumes unchanged bridge items unless you entered year-one overrides; it is a scenario, not a stock-price prediction."
        )
        self.result.update(
            projections=self.projections,
            drivers=self.drivers,
            warnings=warnings,
            metadata=self.data.metadata,
        )
        self.calculation_log = [
            f"{k}: {v:,.6f}" for k, v in self.result.items() if isinstance(v, (int, float))
        ]
        return self.result

    def calculate_intrinsic_value(self):
        return self.calculate()["intrinsic_value"]

    def compute_intrinsic_value(self, wacc, terminal_growth_rate):
        return self._value(wacc, terminal_growth_rate)["intrinsic_value"]

    def generate_sensitivity_table(self):
        if self.result is None:
            self.calculate()
        growths = [
            self.assumptions.terminal_growth_rate + x for x in [-0.01, -0.005, 0, 0.005, 0.01]
        ]
        matrix = []
        for w in [self.wacc + x for x in [-0.01, -0.005, 0, 0.005, 0.01]]:
            prices = []
            for g in growths:
                try:
                    prices.append(self.compute_intrinsic_value(w, g))
                except ValueError:
                    prices.append(None)
            matrix.append((w, prices))
        return growths, matrix
