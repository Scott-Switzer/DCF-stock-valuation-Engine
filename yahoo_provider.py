"""Yahoo current snapshots; annual facts are never represented as point-in-time filings."""

from datetime import datetime, timezone, date
import math
from urllib.parse import quote
from dcf_loader import JsonHTTP, ProviderError, blank_document, ticker_symbol, parse_document

BASE = "https://query2.finance.yahoo.com"
HEADERS = {"User-Agent": "DCF-Valuation-Engine/1.0", "Accept": "application/json"}
METRICS = (
    "TotalRevenue OperatingIncome NetIncomeCommonStockholders ReconciledDepreciation DepreciationAndAmortization CapitalExpenditure CurrentAssets CurrentLiabilities CashAndCashEquivalents CurrentDebt LongTermDebt TotalDebt StockholdersEquity CommonStockEquity TotalEquityGrossMinorityInterest MinorityInterest PreferredStockEquity TotalAssets TotalLiabilitiesNetMinorityInterest TaxProvision TaxRateForCalcs PretaxIncome InterestExpense DilutedAverageShares CommonStockDividendPaid OrdinarySharesNumber"
).split()
SHARES = {"DilutedAverageShares", "OrdinarySharesNumber"}


def finite(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ProviderError(f"Yahoo {label} requires a finite numeric observation.")
    return float(value)


def chart(http, symbol):
    packet = http.get(
        f"{BASE}/v8/finance/chart/{quote(symbol, safe='')}",
        headers=HEADERS,
        params={"range": "5y", "interval": "1wk", "events": "div,splits"},
        ttl=900,
        cache_key=f"yahoo-chart-v1-{symbol}",
    )
    envelope = packet.get("chart", {})
    if envelope.get("error") or not envelope.get("result"):
        raise ProviderError(f"Yahoo market history is unavailable for {symbol}.")
    return envelope["result"][0]


def weekly_returns(packet):
    timestamps = packet.get("timestamp", [])
    blocks = packet.get("indicators", {}).get("adjclose", [])
    if not blocks:
        raise ProviderError("Yahoo adjusted total-return history is unavailable.")
    prices = blocks[0].get("adjclose", [])
    if len(timestamps) != len(prices):
        raise ProviderError("Yahoo market timestamps and prices do not align.")
    result = {}
    previous = None
    for stamp, raw in zip(timestamps, prices):
        day = datetime.fromtimestamp(finite(stamp, "timestamp"), timezone.utc).date()
        week = day.isocalendar()[:2]
        if raw is None:
            previous = None
            continue
        price = finite(raw, "adjusted price")
        if price <= 0:
            raise ProviderError("Yahoo adjusted prices must be positive.")
        if previous is not None and 4 <= (day - previous[0]).days <= 10:
            result[week] = price / previous[1] - 1
        previous = (day, price)
    return result


def market_beta(stock, benchmark):
    stock, benchmark = weekly_returns(stock), weekly_returns(benchmark)
    weeks = sorted(stock.keys() & benchmark.keys())
    if len(weeks) < 104:
        raise ProviderError("Beta requires at least 104 aligned weekly total returns.")
    xs, ys = [benchmark[w] for w in weeks], [stock[w] for w in weeks]
    xm, ym = sum(xs) / len(xs), sum(ys) / len(ys)
    variance = sum((x - xm) ** 2 for x in xs)
    if variance <= 0:
        raise ProviderError("Benchmark variance is zero; beta is unavailable.")
    return finite(
        sum((x - xm) * (y - ym) for x, y in zip(xs, ys)) / variance, "computed beta"
    ), len(weeks)


def annual_facts(packet, ticker, asof):
    envelope = packet.get("timeseries", {})
    if envelope.get("error") or not isinstance(envelope.get("result"), list):
        raise ProviderError("Yahoo annual financials are unavailable.")
    facts = {}
    for block in envelope["result"]:
        symbols = block.get("meta", {}).get("symbol", [])
        if symbols and any(s != ticker for s in symbols):
            raise ProviderError("Yahoo returned mismatched financial symbols.")
        for metric in METRICS:
            for obs in block.get("annual" + metric, []):
                end = obs.get("asOfDate")
                try:
                    date.fromisoformat(end)
                except (TypeError, ValueError):
                    raise ProviderError("Yahoo annual financial date is invalid.") from None
                if end > asof:
                    continue
                if obs.get("periodType") != "12M":
                    raise ProviderError("Yahoo annual observation must cover 12 months.")
                if obs.get("currencyCode") != "USD":
                    raise ProviderError(
                        "Yahoo financial observations must use USD; FX is not implicit."
                    )
                value = finite(obs.get("reportedValue", {}).get("raw"), metric)
                key = (end, metric)
                provenance = {
                    "metric": "annual" + metric,
                    "period_end": end,
                    "unit": "shares"
                    if metric in SHARES
                    else "pure"
                    if metric == "TaxRateForCalcs"
                    else "USD",
                    "provider_currency_code": obs.get("currencyCode"),
                    "value": value,
                }
                if key in facts and facts[key][0] != value:
                    raise ProviderError(f"Yahoo conflicting {metric} observations for {end}.")
                facts[key] = (value, provenance)
    return facts


def load_yahoo(ticker, asof, http=None, include_capital_costs=True, require_wacc=True):
    ticker = ticker_symbol(ticker)
    now = datetime.now(timezone.utc)
    if asof != now.date().isoformat():
        raise ProviderError(
            "Yahoo supports only the current UTC date; historical point-in-time snapshots are unavailable."
        )
    http = http or JsonHTTP()
    stock = chart(http, ticker)
    meta = stock.get("meta", {})
    if meta.get("symbol") != ticker or meta.get("instrumentType") != "EQUITY":
        raise ProviderError("Yahoo requires an operating-company equity ticker.")
    if meta.get("currency") != "USD":
        raise ProviderError("Yahoo market currency must be USD.")
    price = finite(meta.get("regularMarketPrice"), "current price")
    price_day = (
        datetime.fromtimestamp(
            finite(meta.get("regularMarketTime"), "price timestamp"), timezone.utc
        )
        .date()
        .isoformat()
    )
    if price <= 0 or price_day > asof:
        raise ProviderError("Yahoo market price or date is invalid.")
    raw = http.get(
        f"{BASE}/ws/fundamentals-timeseries/v1/finance/timeseries/{ticker}",
        headers=HEADERS,
        params={
            "type": ",".join("annual" + m for m in METRICS),
            "period1": int(now.timestamp()) - 6 * 366 * 86400,
            "period2": int(now.timestamp()),
        },
        ttl=3600,
        cache_key=f"yahoo-financials-v2-{ticker}-{asof}",
    )
    facts = annual_facts(raw, ticker, asof)
    ends = sorted({end for end, metric in facts if metric == "TotalRevenue"})[-3:]
    if len(ends) != 3:
        raise ProviderError("Yahoo needs three aligned annual financial periods.")
    doc = blank_document(
        ticker, meta.get("longName") or meta.get("shortName") or ticker, asof, "api"
    )
    doc["company"].update(eligible=True, security_type="EQUITY")
    warnings = [
        "Yahoo current snapshot is not point-in-time filing data. Financial availability dates mean retrieval date, not filing dates.",
        "Yahoo normalizes fiscal dates to month ends; verify fiscal-period coverage against company filings.",
        "Sector and industry are unavailable from this endpoint; confirm operating-company eligibility.",
        "Other nonoperating assets are explicitly assumed to be zero; review excess investments and other adjustments.",
    ]

    def get(end, metric, optional=False):
        if (end, metric) not in facts:
            if optional:
                return None
            raise ProviderError(f"Yahoo missing {metric} for {end}; cannot complete financials.")
        return facts[end, metric][0]

    for end in ends:
        total = get(end, "TotalDebt", True)
        short, long = get(end, "CurrentDebt", True), get(end, "LongTermDebt", True)
        if total is not None:
            for metric, known in [("CurrentDebt", long), ("LongTermDebt", short)]:
                if (end, metric) not in facts and known is not None and total >= known:
                    value = total - known
                    facts[end, metric] = (
                        value,
                        {
                            "metric": metric,
                            "period_end": end,
                            "value": value,
                            "unit": "USD",
                            "derived_from": [
                                "annualTotalDebt",
                                "annualLongTermDebt"
                                if metric == "CurrentDebt"
                                else "annualCurrentDebt",
                            ],
                        },
                    )
                    warnings.append(
                        f"{metric} for {end} inferred from total debt less the other reported debt component."
                    )
        v = lambda m, optional=False: get(end, m, optional)
        da = v("ReconciledDepreciation", True)
        if da is None:
            da = v("DepreciationAndAmortization")
        pretax, provision = v("PretaxIncome", True), v("TaxProvision", True)
        tax_rate = provision / pretax if provision is not None and pretax not in {None, 0} else None
        tax_provenance = {
            "derived_from": ["annualTaxProvision", "annualPretaxIncome"],
            "period_end": end,
            "unit": "pure",
            "value": tax_rate,
        }
        if tax_rate is None or not 0 <= tax_rate <= 1:
            normalized = v("TaxRateForCalcs", True)
            if normalized is None or not 0 <= normalized <= 1:
                raise ProviderError(
                    f"Yahoo tax rate for {end} is unavailable or outside supported bounds; no tax assumption is invented."
                )
            tax_provenance = {
                **facts[end, "TaxRateForCalcs"][1],
                "basis": "Yahoo normalized TaxRateForCalcs fallback",
                "reported_tax_ratio": tax_rate,
            }
            tax_rate = normalized
            warnings.append(
                f"Tax rate for {end} uses Yahoo normalized annualTaxRateForCalcs ({normalized:.2%}) because the reported tax ratio is missing or outside zero to one; review this normalized assumption."
            )
        row = {
            "period_end": end,
            "available_at": asof,
            "revenue": v("TotalRevenue"),
            "ebit": v("OperatingIncome"),
            "net_income": v("NetIncomeCommonStockholders"),
            "capex": abs(v("CapitalExpenditure")),
            "d_and_a": da,
            "nwc": v("CurrentAssets")
            - v("CashAndCashEquivalents")
            - v("CurrentLiabilities")
            + v("CurrentDebt"),
            "book_value": v("StockholdersEquity"),
            "tax_rate": tax_rate,
            "provenance": {m: p for (d, m), (_, p) in facts.items() if d == end},
        }
        row["provenance"]["tax_rate"] = tax_provenance
        doc["historical"].append(row)
    end = ends[-1]
    v = lambda m, optional=False: get(end, m, optional)
    preferred = v("PreferredStockEquity", True)
    if preferred is None:
        preferred = v("StockholdersEquity") - v("CommonStockEquity")
        if preferred < 0:
            raise ProviderError(
                "Preferred equity cannot be inferred from a negative equity difference."
            )
        warnings.append("Preferred equity is inferred as stockholders equity minus common equity.")
    minority = v("MinorityInterest", True)
    if minority is None:
        minority = v("TotalEquityGrossMinorityInterest") - v("StockholdersEquity")
        if minority < 0:
            raise ProviderError(
                "Minority interest cannot be inferred from a negative equity difference."
            )
        warnings.append(
            "Minority interest is inferred as total equity including minority interest minus stockholders equity."
        )
    if preferred != 0 and include_capital_costs and require_wacc:
        raise ProviderError(
            "Nonzero preferred equity requires an explicit preferred cost assumption; Yahoo WACC cannot be completed."
        )
    doc["bridge"].update(
        short_term_debt=v("CurrentDebt"),
        long_term_debt=v("LongTermDebt"),
        cash=v("CashAndCashEquivalents"),
        preferred_equity=preferred,
        minority_interest=minority,
        other_nonoperating_assets=0.0,
        as_of=end,
    )
    diluted, ordinary = v("DilutedAverageShares"), v("OrdinarySharesNumber")
    if diluted <= 0 or ordinary <= 0:
        raise ProviderError("Yahoo annual share counts must be positive.")
    doc["market"].update(
        price=price,
        price_as_of=price_day,
        diluted_shares=diluted,
        shares_basis=f"Yahoo annualDilutedAverageShares, {end}; annual weighted-average dilution",
    )
    costs = {}
    if include_capital_costs:
        warnings.extend(
            [
                "Capital costs use dated market inputs and explicit equity risk premium and credit spread assumptions.",
                "Market equity weights use annual ordinary shares; valuation shares use annual weighted-average dilution.",
            ]
        )
        benchmark, treasury = chart(http, "SPY"), chart(http, "^TNX")
        beta, n = market_beta(stock, benchmark)
        tm = treasury.get("meta", {})
        if tm.get("symbol") != "^TNX" or benchmark.get("meta", {}).get("symbol") != "SPY":
            raise ProviderError("Yahoo returned a mismatched capital-cost benchmark.")
        rf_date = (
            datetime.fromtimestamp(
                finite(tm.get("regularMarketTime"), "Treasury timestamp"), timezone.utc
            )
            .date()
            .isoformat()
        )
        rf = finite(tm.get("regularMarketPrice"), "Treasury yield") / 100
        if rf_date > asof or not 0 <= rf < 1:
            raise ProviderError("Yahoo Treasury yield date or units are invalid.")
        debt = v("CurrentDebt") + v("LongTermDebt")
        interest = v("InterestExpense", True)
        cost_debt = abs(interest) / debt if interest is not None and debt > 0 else rf + 0.015
        basis = (
            f"Latest annual interest expense / latest annual debt, {end}"
            if interest is not None and debt > 0
            else f"Dated Treasury yield ({rf_date}) + assumed 1.5% credit spread; latest interest expense unavailable or no debt"
        )
        if interest is None:
            warnings.append(
                "Latest annual interest expense is missing; cost of debt uses current Treasury yield plus assumed credit spread. Older interest observations are not carried forward."
            )
        cost_equity = rf + beta * 0.05
        equity = finite(ordinary * price, "equity market value")
        tax = doc["historical"][-1]["tax_rate"]
        if debt < 0 or not 0 <= tax <= 1:
            raise ProviderError("Yahoo debt or effective tax rate is outside supported bounds.")
        costs = {
            "risk_free_rate": rf,
            "risk_free_rate_as_of": rf_date,
            "beta": beta,
            "beta_basis": f"Five-year weekly adjusted total returns versus SPY; {n} aligned observations",
            "equity_risk_premium": 0.05,
            "credit_spread": 0.015,
            "cost_of_debt": cost_debt,
            "cost_of_equity": cost_equity,
            "wacc": (equity * cost_equity + debt * cost_debt * (1 - tax)) / (equity + debt)
            if require_wacc
            else None,
            "capital_cost_method": "wacc" if require_wacc else "equity",
            "debt_cost_basis": basis,
            "equity_market_value": equity,
            "market_equity_value": equity,
            "debt_book_value": debt,
            "debt": debt,
            "tax_rate": tax,
            "preferred_equity": preferred,
            "preferred_cost": None,
            "reported_cost_of_debt": abs(interest) / debt
            if interest is not None and debt > 0
            else None,
            "equity_shares_as_of": end,
        }
    common = v("CommonStockEquity", True)
    raw_dividends = v("CommonStockDividendPaid", True)
    dividends = abs(raw_dividends) if raw_dividends is not None else None
    if common is None:
        warnings.append("Common book equity is unavailable; common P/B and ROE cannot be computed.")
    if dividends is None:
        warnings.append(
            "Common cash dividends are unavailable; DDM cannot be computed. Missing dividends do not mean zero."
        )
    doc["source"].update(
        name="Yahoo Finance current snapshot",
        available_at=asof,
        retrieved_at=now.isoformat(),
        warnings=warnings,
        capital_costs=costs,
        common_dividends={
            "value": dividends,
            "per_share": dividends / diluted if dividends is not None else None,
            "period_end": end,
            "shares_basis": "Annual diluted weighted-average shares",
            "unit": "USD",
        },
        common_book_equity={
            "value": common,
            "period_end": end,
            "unit": "USD",
            "historical": [
                {"period_end": d, "value": get(d, "CommonStockEquity", True)} for d in ends
            ],
        },
        finance_diagnostics={
            "roe": v("NetIncomeCommonStockholders") / common if common else None,
            "roe_basis": "Latest annual common net income / ending common equity",
            "period_end": end,
        },
        bridge_provenance={m: p for (d, m), (_, p) in facts.items() if d == end},
        market_observation={"price": price, "currency": "USD", "as_of": price_day},
    )
    for key, value in costs.items():
        if isinstance(value, (int, float)):
            finite(value, key)
    try:
        parse_document(doc)
    except ValueError as exc:
        raise ProviderError(f"Yahoo financial snapshot failed validation: {exc}") from None
    return doc


def load_company_metrics(ticker, asof, http=None):
    """Peer snapshot without additional benchmark or Treasury requests."""
    return load_yahoo(ticker, asof, http, include_capital_costs=False)


def recalculate_costs(doc, equity_risk_premium=0.05, credit_spread=0.015):
    """Apply explicit market-premium assumptions to a sourced snapshot in place."""
    costs = doc["source"]["capital_costs"]
    erp, spread = (
        finite(equity_risk_premium, "equity risk premium"),
        finite(credit_spread, "credit spread"),
    )
    if not 0 <= erp <= 1 or not 0 <= spread <= 1:
        raise ProviderError("Capital cost assumptions must be between zero and one.")
    costs["equity_risk_premium"], costs["credit_spread"] = erp, spread
    costs["cost_of_equity"] = costs["risk_free_rate"] + costs["beta"] * erp
    costs["cost_of_debt"] = (
        costs["reported_cost_of_debt"]
        if costs["reported_cost_of_debt"] is not None
        else costs["risk_free_rate"] + spread
    )
    if costs["reported_cost_of_debt"] is None:
        costs["debt_cost_basis"] = (
            f"Dated Treasury yield ({costs['risk_free_rate_as_of']}) + assumed {spread:.2%} credit spread; latest interest expense unavailable or no debt"
        )
    warnings = doc["source"]["warnings"]
    warnings[:] = [w for w in warnings if not w.startswith("Equity risk premium ")]
    warnings.append(
        f"Equity risk premium {erp:.2%} and credit spread {spread:.2%} are explicit valuation assumptions."
    )
    equity, debt = costs["market_equity_value"], costs["debt"]
    costs["wacc"] = (
        (
            (
                equity * costs["cost_of_equity"]
                + debt * costs["cost_of_debt"] * (1 - costs["tax_rate"])
            )
            / (equity + debt)
        )
        if costs.get("capital_cost_method", "wacc") == "wacc"
        else None
    )
    return costs
