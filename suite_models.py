"""CUIG dividend discount and forward trading-comparable valuation engines."""

from copy import deepcopy
from dataclasses import dataclass, asdict
from datetime import date
import statistics
from dcf_code import number
from dcf_loader import demo_document, iso_date, ticker_symbol, BRIDGE_FIELDS, typed_number

MULTIPLES = {
    "ev_revenue": ("EV / Revenue", "revenue"),
    "ev_ebitda": ("EV / EBITDA", "ebitda"),
    "ev_ebit": ("EV / EBIT", "ebit"),
    "pe": ("P / E", "net_income"),
    "pb": ("P / B", "book_value"),
}


def suite_identity(doc, method):
    if not isinstance(doc, dict) or doc.get("schema_version") != f"{method}-financials-v1":
        raise ValueError(f"Use a {method}-financials-v1 financial document.")
    for key in ["company", "market", "source"]:
        if not isinstance(doc.get(key), dict):
            raise ValueError(f"Missing {key} section.")
    company, market, source = (doc[k] for k in ["company", "market", "source"])
    company["ticker"] = ticker_symbol(company.get("ticker"))
    if not isinstance(company.get("name"), str) or not company["name"].strip():
        raise ValueError("A company name is required.")
    if not isinstance(market.get("shares_basis"), str) or not market["shares_basis"].strip():
        raise ValueError("A diluted share-count basis is required.")
    asof = iso_date(doc.get("valuation_date"), "Valuation date")
    if asof > date.today():
        raise ValueError("Valuation date cannot be in the future.")
    if (
        doc.get("units") != "absolute"
        or company.get("currency") != "USD"
        or market.get("currency") != "USD"
    ):
        raise ValueError("Use absolute USD amounts and shares; currency conversion is not modeled.")
    if company.get("eligible") is not True:
        raise ValueError(
            "Confirm the company and inputs are suitable for the selected valuation method."
        )
    if (
        not isinstance(source.get("name"), str)
        or not source["name"].strip()
        or not isinstance(source.get("kind"), str)
        or source["kind"] not in {"synthetic", "manual", "sec", "zion", "api"}
    ):
        raise ValueError("A named source and valid source kind are required.")
    available = source.get("available_at")
    if source["kind"] in {"sec", "zion", "api"} and available is None:
        raise ValueError("Provider financials require a source availability date.")
    if available is not None:
        if (
            not isinstance(available, str)
            or iso_date(available[:10], "Source availability date") > asof
        ):
            raise ValueError("Financial inputs were not available on the valuation date.")
    warnings = source.get("warnings", [])
    if not isinstance(warnings, list) or any(not isinstance(w, str) for w in warnings):
        raise ValueError("Source warnings must be text messages.")
    for key in ["price", "diluted_shares"]:
        typed_number(market.get(key), key)
        number(market[key], key, 0.000001)
    if iso_date(market.get("price_as_of"), "Price date") > asof:
        raise ValueError("Price date is later than valuation date.")
    return {
        "ticker": company["ticker"],
        "company_name": company.get("name", company["ticker"]),
        "currency": "USD",
        "valuation_date": asof.isoformat(),
        "is_demo": source["kind"] == "synthetic" or source.get("origin_kind") == "synthetic",
    }


def suite_sample(method, blank=False):
    base = demo_document()
    doc = {k: deepcopy(base[k]) for k in ["valuation_date", "units", "company", "market", "source"]}
    doc["company"].setdefault("is_financial", False)
    doc["schema_version"] = f"{method}-financials-v1"
    if method == "ddm":
        doc.update(base_common_dividends=100.0, dividend_as_of="2025-12-31")
    elif method == "relative":
        doc["bridge"] = deepcopy(base["bridge"])
        doc["target"] = {
            "historical_as_of": "2025-12-31",
            "historical": {
                "revenue": 1000.0,
                "ebitda": 230.0,
                "ebit": 200.0,
                "net_income": 150.0,
                "book_value": 500.0,
            },
            "forward": {
                "revenue": 1050.0,
                "ebitda": 241.5,
                "ebit": 210.0,
                "net_income": 157.5,
                "book_value": 525.0,
            },
        }
        doc["comparables"] = [
            {
                "ticker": f"CMP{letter}",
                "name": f"Synthetic peer {letter}",
                "as_of": "2026-10-06",
                "currency": "USD",
                "source": "Synthetic example multiples",
                "multiples": dict(zip(MULTIPLES, values)),
            }
            for letter, values in zip(
                "ABCD",
                [
                    [2, 10, 12, 15, 3],
                    [3, 12, 14, 17, 4],
                    [2.5, 11, 13, 16, 3.5],
                    [3.5, 13, 15, 18, 4.5],
                ],
            )
        ]
    else:
        raise ValueError("Choose ddm or relative valuation.")
    if blank:
        doc["valuation_date"] = date.today().isoformat()
        doc["company"].update(ticker="", name="", sector="", eligible=False)
        doc["source"] = {"kind": "manual", "name": "User-entered financials", "warnings": []}
        doc["market"].update(
            price=None, diluted_shares=None, price_as_of=date.today().isoformat(), shares_basis=""
        )
        if method == "ddm":
            doc["base_common_dividends"] = None
            doc["dividend_as_of"] = ""
        else:
            doc["target"]["historical_as_of"] = ""
            for period in ["historical", "forward"]:
                doc["target"][period] = dict.fromkeys(doc["target"][period])
            doc["bridge"] = {**dict.fromkeys(BRIDGE_FIELDS), "as_of": ""}
            doc["comparables"] = []
    return doc


@dataclass
class DDMAssumptions:
    dividend_growth_rates: list
    required_return: float
    terminal_growth_rate: float
    future_shares: float | None = None

    def validate(self):
        if (
            not isinstance(self.dividend_growth_rates, (list, tuple))
            or len(self.dividend_growth_rates) != 5
        ):
            raise ValueError("DDM requires five annual dividend growth rates.")
        self.dividend_growth_rates = [
            number(g, f"Year {i + 1} dividend growth", -0.5, 1)
            for i, g in enumerate(self.dividend_growth_rates)
        ]
        self.required_return = number(self.required_return, "Required return on equity", 0.001, 0.5)
        self.terminal_growth_rate = number(
            self.terminal_growth_rate, "Terminal dividend growth", -0.1, 0.15
        )
        if self.terminal_growth_rate >= self.required_return:
            raise ValueError(
                "Terminal dividend growth must be below the required return on equity."
            )
        if self.future_shares is not None:
            self.future_shares = number(self.future_shares, "12-month diluted shares", 0.000001)


class DDMModel:
    def __init__(self, doc, assumptions):
        self.doc = deepcopy(doc)
        self.a = deepcopy(assumptions)

    def calculate(self):
        doc, a = self.doc, self.a
        metadata = suite_identity(doc, "ddm")
        a.validate()
        typed_number(doc.get("base_common_dividends"), "Latest annual common dividends")
        dividend = number(doc["base_common_dividends"], "Latest annual common dividends", 0.000001)
        if iso_date(doc.get("dividend_as_of"), "Dividend fiscal date") > iso_date(
            doc["valuation_date"], "Valuation date"
        ):
            raise ValueError("Dividend date is later than valuation date.")
        projections = []
        for i, g in enumerate(a.dividend_growth_rates):
            dividend *= 1 + g
            projections.append(
                {
                    "year": i + 1,
                    "growth": g,
                    "dividends": dividend,
                    "pv_dividends": dividend / (1 + a.required_return) ** (i + 1),
                    "pv_dividends_12m": None if i == 0 else dividend / (1 + a.required_return) ** i,
                }
            )
        terminal = (
            dividend * (1 + a.terminal_growth_rate) / (a.required_return - a.terminal_growth_rate)
        )
        stage1 = sum(p["pv_dividends"] for p in projections)
        stage12 = sum(p["pv_dividends_12m"] or 0 for p in projections)
        tvpv = terminal / (1 + a.required_return) ** 5
        tv12 = terminal / (1 + a.required_return) ** 4
        shares = doc["market"]["diluted_shares"]
        future = a.future_shares or shares
        today = (stage1 + tvpv) / shares
        target = (stage12 + tv12) / future
        warnings = [
            "Common cash dividends only; buybacks and preferred dividends are not part of this DDM.",
            "Required return on equity discounts dividends. WACC and enterprise debt adjustments are not used.",
            "Twelve-month value excludes the first dividend; it is an ex-dividend scenario, not guaranteed return.",
            "Use DDM only when dividends represent sustainable shareholder distributions. The model is sensitive to payout policy.",
        ]
        if tvpv / (stage1 + tvpv) > 0.8:
            warnings.append("More than 80% of present equity value comes from terminal dividends.")
        if a.future_shares is None:
            warnings.append("Twelve-month diluted shares are assumed unchanged, as in CUIG.")
        rates = [a.terminal_growth_rate + d for d in [-0.01, -0.005, 0, 0.005, 0.01]]
        sensitivity = []
        for ke in [a.required_return + d for d in [-0.01, -0.005, 0, 0.005, 0.01]]:
            values = []
            for g in rates:
                if ke <= 0 or g >= ke or g <= -1:
                    values.append(None)
                else:
                    values.append(
                        (
                            sum(p["dividends"] / (1 + ke) ** p["year"] for p in projections)
                            + dividend * (1 + g) / (ke - g) / (1 + ke) ** 5
                        )
                        / shares
                    )
            sensitivity.append({"rate": ke, "values": values})
        return finite_result(
            {
                "method": "ddm",
                "model_version": "cuig-ddm-v1",
                "metadata": metadata,
                "intrinsic_value": today,
                "target_price_12m": target,
                "current_price": doc["market"]["price"],
                "upside": today / doc["market"]["price"] - 1,
                "upside_12m": target / doc["market"]["price"] - 1,
                "projections": projections,
                "stage1_pv": stage1,
                "stage1_pv_12m": stage12,
                "terminal_value": terminal,
                "pv_terminal": tvpv,
                "pv_terminal_12m": tv12,
                "equity_value": stage1 + tvpv,
                "equity_value_12m": stage12 + tv12,
                "diluted_shares": shares,
                "diluted_shares_12m": future,
                "sensitivity": {"growth_rates": rates, "rows": sensitivity},
                "warnings": warnings,
                "assumptions": asdict(a),
            }
        )


@dataclass
class RelativeAssumptions:
    included_methods: list

    def validate(self):
        if (
            not isinstance(self.included_methods, (list, tuple))
            or not self.included_methods
            or any(not isinstance(k, str) or k not in MULTIPLES for k in self.included_methods)
        ):
            raise ValueError("Select at least one supported valuation multiple.")
        if len(set(self.included_methods)) != len(self.included_methods):
            raise ValueError("Each multiple can be selected only once.")


class RelativeModel:
    def __init__(self, doc, assumptions):
        self.doc = deepcopy(doc)
        self.a = deepcopy(assumptions)

    def calculate(self):
        doc, a = self.doc, self.a
        metadata = suite_identity(doc, "relative")
        a.validate()
        target = doc.get("target")
        bridge = doc.get("bridge")
        peers = doc.get("comparables")
        if (
            not isinstance(target, dict)
            or any(not isinstance(target.get(k), dict) for k in ["historical", "forward"])
            or not isinstance(bridge, dict)
        ):
            raise ValueError(
                "Provide historical/forward target metrics and an explicit equity bridge."
            )
        asof = iso_date(doc["valuation_date"], "Valuation date")
        for label, value in [
            ("Historical date", target.get("historical_as_of")),
            ("Bridge date", bridge.get("as_of")),
        ]:
            if iso_date(value, label) > asof:
                raise ValueError(f"{label} is later than valuation date.")
        for k in BRIDGE_FIELDS:
            typed_number(bridge.get(k), k)
            number(bridge[k], k, 0)
        if not isinstance(peers, list) or not 1 <= len(peers) <= 20:
            raise ValueError("Enter between one and twenty comparable companies.")
        financial = any(
            t
            in " ".join(
                str(doc["company"].get(k, "")) for k in ["sector", "industry", "security_type"]
            ).lower()
            for t in ["bank", "insurance", "financial service", "investment firm"]
        )
        financial = financial or doc["company"].get("is_financial") is True
        if financial and any(k.startswith("ev_") for k in a.included_methods):
            raise ValueError(
                "For financial firms, use equity multiples P/E and P/B only, as in CUIG."
            )
        for period in ["historical", "forward"]:
            for _, metric in MULTIPLES.values():
                value = target[period].get(metric)
                if value is not None:
                    typed_number(value, f"{period} {metric}")
        tickers = []
        for p in peers:
            if not isinstance(p, dict) or not isinstance(p.get("multiples"), dict):
                raise ValueError("Each peer needs an explicit multiples record.")
            symbol = ticker_symbol(p.get("ticker"))
            tickers.append(symbol)
            if symbol == doc["company"]["ticker"]:
                raise ValueError("Do not include the target company in its own peer average.")
            if p.get("available_at") is not None:
                available = p["available_at"]
                if (
                    not isinstance(available, str)
                    or iso_date(available[:10], "Peer availability date") > asof
                ):
                    raise ValueError("Peer inputs were not available on the valuation date.")
            if p.get("currency") != "USD":
                raise ValueError("Peer metrics must use matching USD conventions.")
            if iso_date(p.get("as_of"), "Peer multiple date") > asof:
                raise ValueError("Peer multiple date is later than valuation date.")
            if not isinstance(p.get("source"), str) or not p["source"].strip():
                raise ValueError("Each peer needs a source reference.")
            for k in MULTIPLES:
                value = p["multiples"].get(k)
                if value is not None:
                    typed_number(value, f"{symbol} {k}")
        if len(set(tickers)) != len(tickers):
            raise ValueError("Each comparable ticker must be unique.")
        shares = doc["market"]["diluted_shares"]
        price = doc["market"]["price"]
        claims = (
            bridge["short_term_debt"]
            + bridge["long_term_debt"]
            + bridge["preferred_equity"]
            + bridge["minority_interest"]
            - bridge["cash"]
            - bridge["other_nonoperating_assets"]
        )
        marketev = price * shares + claims
        rows = []
        warnings = []
        for k, (label, metric) in MULTIPLES.items():
            values = [
                p["multiples"][k]
                for p in peers
                if p["multiples"].get(k) is not None and p["multiples"][k] > 0
            ]
            excluded = len(peers) - len(values)
            forward = target["forward"].get(metric)
            historical = target["historical"].get(metric)
            valid = (
                bool(values)
                and forward is not None
                and forward > 0
                and (not financial or not k.startswith("ev_"))
            )
            if k in a.included_methods and not valid:
                raise ValueError(
                    f"{label} needs a positive forward {metric} and at least one valid positive peer multiple. Exclude unsuitable methods."
                )
            if excluded:
                warnings.append(
                    f"{label}: {excluded} peer(s) with missing/nonpositive multiples excluded; coverage differs by metric."
                )
            avg = statistics.mean(values) if values else None
            implied = (
                (avg * forward - (claims if k.startswith("ev_") else 0)) / shares if valid else None
            )
            if implied is not None and implied < 0:
                warnings.append(
                    f"{label} implies negative common equity; its share value is floored at zero."
                )
            market_multiple = (
                (marketev if k.startswith("ev_") else price * shares) / historical
                if historical is not None
                and historical > 0
                and (not k.startswith("ev_") or (marketev > 0 and not financial))
                else None
            )
            rows.append(
                {
                    "key": k,
                    "label": label,
                    "metric": metric,
                    "included": k in a.included_methods,
                    "count": len(values),
                    "mean": avg,
                    "minimum": min(values) if values else None,
                    "maximum": max(values) if values else None,
                    "forward_metric": forward,
                    "historical_metric": historical,
                    "market_multiple": market_multiple,
                    "implied_price": max(0, implied) if implied is not None else None,
                    "raw_implied_price": implied,
                }
            )
        targetprice = statistics.mean(r["implied_price"] for r in rows if r["included"])
        warnings += [
            "Arithmetic peer mean and equal weighting across selected methods match CUIG. This is a forward year-one relative target, not a discounted intrinsic value.",
            "Choose comparable operations, leverage, accounting and growth; use consistent trailing/forward peer denominator conventions. Multiples are user supplied, not fetched market data.",
            "P/E and P/B already imply common equity: debt is not deducted again. Enterprise multiples use the explicit common-equity bridge.",
            "Current bridge and diluted shares carry into the forward target; review projected capital structure before relying on it.",
        ]
        if financial:
            warnings.append("Financial firm: enterprise multiples are excluded from selection.")
        return finite_result(
            {
                "method": "relative",
                "model_version": "cuig-relative-v1",
                "metadata": metadata,
                "intrinsic_value": None,
                "target_price_12m": targetprice,
                "current_price": price,
                "upside": None,
                "upside_12m": targetprice / price - 1,
                "multiples": rows,
                "market_enterprise_value": marketev,
                "net_common_claims": claims,
                "diluted_shares": shares,
                "warnings": warnings,
                "assumptions": asdict(a),
            }
        )


def finite_result(value):
    if isinstance(value, dict):
        for v in value.values():
            finite_result(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            finite_result(v)
    elif isinstance(value, float):
        number(value, "Calculated result")
    return value


def from_dcf_document(method, financials, assumptions):
    """Carry verified DCF identity/forward drivers; never invent dividends or peers."""
    from dcf_code import DCFModel
    from dcf_loader import parse_document

    model = DCFModel(parse_document(financials), assumptions)
    result = model.calculate()
    doc = suite_sample(method, blank=True)
    for key in ["valuation_date", "units", "company", "market", "source"]:
        doc[key] = deepcopy(financials[key])
    doc["company"]["eligible"] = False
    doc["source"]["linked_dcf_assumptions"] = asdict(assumptions)
    if doc["source"]["kind"] in {"sec", "zion", "api"}:
        doc["source"]["available_at"] = max(row["available_at"] for row in financials["historical"])
    latest = financials["historical"][-1]
    if method == "ddm":
        doc["base_common_dividends"] = None
        doc["dividend_as_of"] = latest["period_end"]
    else:
        doc["source"].setdefault("warnings", []).append(
            "Enter verified historical and forward common book equity for P/B; DCF book value may include preferred and noncontrolling equity."
        )
        first = result["projections"][0]
        doc["bridge"] = deepcopy(financials["bridge"])
        doc["target"] = {
            "historical_as_of": latest["period_end"],
            "historical": {
                "revenue": latest["revenue"],
                "ebitda": latest["ebit"] + latest["d_and_a"],
                "ebit": latest["ebit"],
                "net_income": latest["net_income"],
                "book_value": None,
            },
            "forward": {
                "revenue": first["Revenue"],
                "ebitda": first["EBITDA"],
                "ebit": first["EBIT"],
                "net_income": first["Net Income"],
                "book_value": None,
            },
        }
    return doc
