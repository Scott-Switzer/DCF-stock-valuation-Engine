"""Provider adapters. No provider failure or missing fact is interpreted as zero."""

from copy import deepcopy
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import urlparse
import requests
from dcf_code import FinancialData, number
from storage import Store

SCHEMA = "dcf-financials-v1"
HISTORY_FIELDS = (
    "revenue",
    "ebit",
    "net_income",
    "capex",
    "d_and_a",
    "nwc",
    "book_value",
    "tax_rate",
)
BRIDGE_FIELDS = (
    "short_term_debt",
    "long_term_debt",
    "cash",
    "preferred_equity",
    "minority_interest",
    "other_nonoperating_assets",
)


class ProviderError(RuntimeError):
    pass


def ticker_symbol(value):
    if not isinstance(value, str):
        raise ValueError("Ticker must be text.")
    value = value.strip().upper().replace(".", "-")
    if not re.fullmatch(r"[A-Z]{1,6}(?:-[A-Z]{1,2})?", value):
        raise ValueError("Enter a supported stock ticker, such as AAPL or BRK-B.")
    return value


def iso_date(value, label):
    if not isinstance(value, str):
        raise ValueError(f"{label} requires an ISO date (YYYY-MM-DD).")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{label} requires a valid ISO date (YYYY-MM-DD).") from None


def eligibility(company):
    text = " ".join(
        str(company.get(k, "")) for k in ["sector", "industry", "security_type"]
    ).lower()
    if company.get("eligible") is not True or any(
        x in text
        for x in [
            "bank",
            "insurance",
            "financial service",
            "reit",
            "real estate investment trust",
            "etf",
            "fund",
            "limited partnership",
            "mlp",
        ]
    ):
        raise ValueError(
            "This FCFF model supports eligible operating companies. Banks, insurers, REITs, funds and partnerships require another valuation model."
        )


def demo_document():
    try:
        from embedded_assets import ASSETS

        return json.loads(ASSETS["data/demo.json"])
    except ImportError:
        return json.loads((Path(__file__).parent / "data/demo.json").read_text())


def typed_number(value, label):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} requires a typed JSON number; missing is not zero.")
    return number(value, label)


def parse_document(doc):
    if not isinstance(doc, dict) or doc.get("schema_version") != SCHEMA:
        raise ValueError(f"Financial document must use {SCHEMA}.")
    for section in ["company", "market", "bridge", "source"]:
        if not isinstance(doc.get(section), dict):
            raise ValueError(f"Missing {section} section.")
    company, market, bridge, source = (doc[k] for k in ["company", "market", "bridge", "source"])
    symbol = ticker_symbol(company.get("ticker"))
    eligibility(company)
    asof = iso_date(doc.get("valuation_date"), "Valuation date")
    if asof > datetime.now(timezone.utc).date():
        raise ValueError("Valuation date cannot be in the future.")
    currency = company.get("currency")
    if currency != "USD" or market.get("currency") != currency:
        raise ValueError(
            "This release requires matching USD financial and market currency; FX conversion is not modeled."
        )
    if doc.get("units") != "absolute":
        raise ValueError("Financial amounts and shares must be in absolute units, not millions.")
    if not isinstance(source.get("name"), str) or not source.get("name") or not source.get("kind"):
        raise ValueError("A named source and source kind are required.")
    if not isinstance(source.get("warnings", []), list) or any(
        not isinstance(w, str) for w in source.get("warnings", [])
    ):
        raise ValueError("Source warnings must be a list of text messages.")
    if not isinstance(source.get("kind"), str) or source.get("kind") not in {
        "synthetic",
        "manual",
        "sec",
        "zion",
        "api",
    }:
        raise ValueError("Unknown financial source kind.")
    rows = doc.get("historical")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("Exactly three fiscal periods are required.")
    periods = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each fiscal period must be a financial record.")
        end = iso_date(row.get("period_end"), "Fiscal period")
        if end > asof:
            raise ValueError("Historical fiscal periods must be on or before the valuation date.")
        periods.append(end.isoformat())
        for name in HISTORY_FIELDS:
            typed_number(row.get(name), f"{end} {name}")
        if source["kind"] in {"sec", "zion", "api"}:
            available = iso_date(
                str(row.get("available_at", ""))[:10], "Financial availability date"
            )
            if available > asof:
                raise ValueError("A historical statement was not available on the valuation date.")
    if periods != sorted(set(periods)):
        raise ValueError("Fiscal periods must be unique and chronological.")
    if any(
        not 300 <= (date.fromisoformat(b) - date.fromisoformat(a)).days <= 430
        for a, b in zip(periods, periods[1:])
    ):
        raise ValueError("Three consecutive annual fiscal periods are required.")
    for name in BRIDGE_FIELDS:
        typed_number(bridge.get(name), name)
        number(bridge.get(name), name, 0)
    typed_number(market.get("price"), "Current price")
    typed_number(market.get("diluted_shares"), "Diluted shares")
    if market.get("price_as_of") is None:
        raise ValueError("Price as-of date is required.")
    if iso_date(str(market["price_as_of"])[:10], "Price date") > asof:
        raise ValueError("Price date is later than the valuation date.")
    if iso_date(str(bridge.get("as_of", ""))[:10], "Bridge as-of date") > asof:
        raise ValueError("Bridge date is later than valuation date.")
    get = lambda key: [number(r.get(key), key) for r in rows]
    debt = number(bridge["short_term_debt"], "Short-term debt", 0) + number(
        bridge["long_term_debt"], "Long-term debt", 0
    )
    zeros = [0.0] * 3

    def repeated(key):
        return [number(bridge[key], key, 0)] * 3

    fd = FinancialData(
        years=periods,
        revenue=get("revenue"),
        ebit=get("ebit"),
        ebitda=[r["ebit"] + r["d_and_a"] for r in rows],
        net_income=get("net_income"),
        effective_tax_rate=get("tax_rate"),
        interest_expense=[],
        current_assets=zeros,
        current_liabilities=zeros,
        cash_and_equivalents=repeated("cash"),
        short_term_debt=repeated("short_term_debt"),
        long_term_debt=repeated("long_term_debt"),
        total_debt=[debt] * 3,
        total_assets=get("book_value"),
        total_liabilities=zeros,
        property_plant_equipment_net=zeros,
        preferred_equity=repeated("preferred_equity"),
        d_and_a=get("d_and_a"),
        capex=get("capex"),
        preferred_dividends=[],
        shares_outstanding=number(market.get("diluted_shares"), "Diluted shares", 0),
        beta=1.0,
        stock_price=number(market.get("price"), "Current price", 0),
        market_cap=0.0,
        risk_free_rate=0.04,
        market_return_rate=0.1,
        nwc_override=get("nwc"),
        book_value_override=get("book_value"),
        minority_interest=number(bridge["minority_interest"], "Minority interest", 0),
        other_nonoperating_assets=number(
            bridge["other_nonoperating_assets"], "Other nonoperating assets", 0
        ),
        metadata={
            "ticker": symbol,
            "company_name": company.get("name", symbol),
            "currency": currency,
            "valuation_date": asof.isoformat(),
            "source": deepcopy(source),
            "price_as_of": market["price_as_of"],
            "shares_basis": market.get("shares_basis", "User supplied diluted shares"),
            "is_demo": source["kind"] == "synthetic" or source.get("origin_kind") == "synthetic",
            "document": deepcopy(doc),
        },
    )
    fd.validate()
    return fd


class JsonHTTP:
    """One bounded request budget across all calls, explicit retries, no URL/key logs."""

    def __init__(self, budget=24, session=None, store=None):
        try:
            from flask import current_app, has_request_context

            self.edge = has_request_context() and current_app.config.get("CLOUDFLARE")
        except ImportError:
            self.edge = False
        self.deadline = time.monotonic() + budget
        self.session = None if self.edge else session or requests.Session()
        if self.edge:
            from provider_cache import EdgeStore

            self.store = store or EdgeStore()
        else:
            self.store = store or Store()

    def get(self, url, *, headers=None, params=None, ttl=0, cache_key=None):
        if cache_key:
            cached = self.store.get(cache_key)
            if cached is not None:
                return cached
        if self.edge:
            raw = self.edge_get(url, headers=headers, params=params)
            if cache_key and ttl:
                self.store.set(cache_key, raw, ttl)
            return raw
        for attempt in range(2):
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise ProviderError(
                    "Data provider exceeded its request deadline. Retry or enter financials manually."
                )
            try:
                with self.session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=(min(3, remaining), min(5, remaining)),
                    stream=True,
                    allow_redirects=False,
                ) as response:
                    if response.status_code in {429, 500, 502, 503, 504} and attempt == 0:
                        time.sleep(min(0.5, max(0, self.deadline - time.monotonic())))
                        continue
                    if response.status_code != 200:
                        raise ProviderError(
                            f"Data provider returned HTTP {response.status_code}. Check configuration or use manual input."
                        )
                    chunks = []
                    size = 0
                    for chunk in response.iter_content(65536):
                        if time.monotonic() > self.deadline:
                            raise ProviderError("Data provider exceeded its request deadline.")
                        size += len(chunk)
                        if size > 20_000_000:
                            raise ProviderError("Data provider response exceeded the size limit.")
                        chunks.append(chunk)
                    raw = json.loads(b"".join(chunks))
                    if cache_key and ttl:
                        self.store.set(cache_key, raw, ttl)
                    return raw
            except (requests.RequestException, json.JSONDecodeError, UnicodeError):
                if attempt == 1:
                    raise ProviderError(
                        "Data provider is unavailable or returned invalid JSON. Retry or use manual input."
                    ) from None
        raise ProviderError("Data provider is unavailable.")

    def edge_get(self, url, headers=None, params=None):
        from pyodide.ffi import run_sync
        from workers import fetch
        from urllib.parse import urlencode
        import js

        if params:
            url += "?" + urlencode(params)
        for attempt in range(2):
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise ProviderError("Data provider exceeded its request deadline.")
            try:
                response = run_sync(
                    fetch(
                        url,
                        headers=headers or {},
                        redirect="manual",
                        signal=js.AbortSignal.timeout(int(min(remaining, 8) * 1000)),
                    )
                )
                if response.status in {429, 500, 502, 503, 504} and attempt == 0:
                    continue
                if response.status != 200:
                    raise ProviderError(
                        f"Data provider returned HTTP {response.status}. Use manual input."
                    )
                reader = response.body.getReader()
                chunks = bytearray()
                while True:
                    chunk = run_sync(reader.read())
                    if chunk.done:
                        break
                    if (
                        time.monotonic() > self.deadline
                        or len(chunks) + chunk.value.byteLength > 20_000_000
                    ):
                        run_sync(reader.cancel())
                        raise ProviderError(
                            "Data provider exceeded the response size or time limit."
                        )
                    chunks.extend(chunk.value.to_bytes())
                return json.loads(chunks)
            except ProviderError:
                raise
            except Exception:
                if attempt == 1:
                    raise ProviderError(
                        "Data provider is unavailable or returned invalid JSON."
                    ) from None
        raise ProviderError("Data provider is unavailable.")


TAGS = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ],
    "ebit": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "d_and_a": [
        "DepreciationDepletionAndAmortization",
        "DepreciationDepletionAndAmortizationPropertyPlantAndEquipment",
    ],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    "current_assets": ["AssetsCurrent"],
    "current_liabilities": ["LiabilitiesCurrent"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue"],
    "short_term_debt": ["DebtCurrent"],
    "current_maturities": ["LongTermDebtCurrent"],
    "short_term_borrowings": ["ShortTermBorrowings"],
    "long_term_debt": ["LongTermDebtNoncurrent"],
    "total_assets": ["Assets"],
    "total_liabilities": ["Liabilities"],
    "tax_expense": ["IncomeTaxExpenseBenefit"],
    "pretax_income": [
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
    ],
    "diluted_shares": ["WeightedAverageNumberOfDilutedSharesOutstanding"],
    "preferred_equity": ["PreferredStockValue"],
    "minority_interest": ["MinorityInterest"],
}
DURATION = {
    "revenue",
    "ebit",
    "net_income",
    "d_and_a",
    "capex",
    "tax_expense",
    "pretax_income",
    "diluted_shares",
}


def sec_fact(facts, metric, end, cutoff):
    """Exact tag, unit and period matching. Latest filing available at cutoff."""
    unit = "shares" if metric == "diluted_shares" else "USD"
    for tag in TAGS[metric]:
        candidates = []
        for row in (
            facts.get("facts", {}).get("us-gaap", {}).get(tag, {}).get("units", {}).get(unit, [])
        ):
            if (
                row.get("end") != end
                or row.get("form") not in {"10-K", "10-K/A"}
                or row.get("filed", "9999") > cutoff
            ):
                continue
            if metric in DURATION:
                try:
                    days = (date.fromisoformat(row["end"]) - date.fromisoformat(row["start"])).days
                except (KeyError, ValueError):
                    continue
                if not 330 <= days <= 400:
                    continue
            elif row.get("start"):
                continue
            candidates.append(row)
        if candidates:
            latest = max(r["filed"] for r in candidates)
            top = [r for r in candidates if r["filed"] == latest]
            if len({r["val"] for r in top}) != 1:
                raise ProviderError(
                    f"Ambiguous SEC facts for {metric}, {end}; review the filing manually."
                )
            row = top[0]
            return number(row["val"], metric), {
                "tag": tag,
                "period_end": end,
                "filed": row["filed"],
                "accession": row.get("accn"),
                "unit": unit,
            }
    if metric == "short_term_debt":
        maturity, mp = sec_fact(facts, "current_maturities", end, cutoff)
        borrowing, bp = sec_fact(facts, "short_term_borrowings", end, cutoff)
        if maturity is not None and borrowing is not None:
            return maturity + borrowing, {
                "components": [mp, bp],
                "filed": max(mp["filed"], bp["filed"]),
                "period_end": end,
                "unit": "USD",
            }
    return None, None


def blank_document(ticker, name, asof, kind):
    return {
        "schema_version": SCHEMA,
        "valuation_date": asof,
        "units": "absolute",
        "company": {
            "ticker": ticker,
            "name": name,
            "currency": "USD",
            "eligible": False,
            "sector": "",
        },
        "market": {
            "price": None,
            "price_as_of": asof,
            "currency": "USD",
            "diluted_shares": None,
            "shares_basis": "Requires confirmation",
        },
        "bridge": {**dict.fromkeys(BRIDGE_FIELDS), "as_of": None},
        "historical": [],
        "source": {
            "name": kind.upper(),
            "kind": kind,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "warnings": [],
        },
    }


def load_sec(ticker, asof, http):
    identity = provider_setting("EDGAR_IDENTITY")
    if "@" not in identity:
        raise ProviderError(
            "Set EDGAR_IDENTITY to your name and contact email on the server before using SEC data. Sample and manual modes remain available."
        )
    headers = {
        "User-Agent": identity,
        "Accept-Encoding": "gzip, deflate",
        "Accept": "application/json",
    }
    directory = http.get(
        "https://www.sec.gov/files/company_tickers.json",
        headers=headers,
        ttl=86400,
        cache_key="sec-directory",
    )
    entry = next(
        (r for r in directory.values() if str(r.get("ticker", "")).replace(".", "-") == ticker),
        None,
    )
    if not entry:
        raise ProviderError(
            "Ticker not found in SEC directory. Enter CIK-backed financials manually."
        )
    cik = str(entry["cik_str"]).zfill(10)
    facts = http.get(
        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
        headers=headers,
        ttl=3600,
        cache_key=f"sec-facts-{cik}",
    )
    doc = blank_document(ticker, entry["title"], asof, "sec")
    doc["source"].update(url=f"https://www.sec.gov/edgar/browse/?CIK={cik}", cik=cik)
    candidates = set()
    for tag in TAGS["revenue"]:
        for row in (
            facts.get("facts", {}).get("us-gaap", {}).get(tag, {}).get("units", {}).get("USD", [])
        ):
            if row.get("filed", "9999") <= asof and row.get("end", "9999") <= asof:
                candidates.add(row["end"])
    ends = []
    for end in sorted(candidates, reverse=True):
        value, _ = sec_fact(facts, "revenue", end, asof)
        if value is not None:
            ends.append(end)
            if len(ends) == 3:
                break
    ends.sort()
    if len(ends) != 3:
        raise ProviderError(
            "SEC did not provide three annual USD revenue periods. Use manual input or Zion."
        )
    for end in ends:
        extracted = {key: sec_fact(facts, key, end, asof) for key in TAGS}
        val = lambda key: extracted[key][0]
        provenance = {key: p for key, (_, p) in extracted.items() if p}
        nwc = (
            (val("current_assets") - val("cash"))
            - (val("current_liabilities") - val("short_term_debt"))
            if all(
                val(k) is not None
                for k in ["current_assets", "cash", "current_liabilities", "short_term_debt"]
            )
            else None
        )
        book = (
            val("total_assets") - val("total_liabilities")
            if val("total_assets") is not None and val("total_liabilities") is not None
            else None
        )
        tax = (
            val("tax_expense") / val("pretax_income")
            if val("tax_expense") is not None and val("pretax_income") not in {None, 0}
            else None
        )
        row = {
            "period_end": end,
            "available_at": max((p["filed"] for p in provenance.values()), default=asof),
            "provenance": provenance,
            **{k: val(k) for k in ["revenue", "ebit", "net_income", "capex", "d_and_a"]},
            "nwc": nwc,
            "book_value": book,
            "tax_rate": tax,
        }
        doc["historical"].append(row)
    for k in ["short_term_debt", "long_term_debt", "cash", "preferred_equity", "minority_interest"]:
        doc["bridge"][k] = extracted[k][0]
    doc["bridge"]["as_of"] = ends[-1]
    doc["market"]["diluted_shares"] = extracted["diluted_shares"][0]
    doc["market"]["shares_basis"] = (
        "Annual weighted-average diluted shares from latest annual filing; review for current dilution."
    )
    doc["source"]["warnings"] = [
        "Confirm eligibility and enter a dated market price. Missing facts remain blank and must be completed from the filing.",
        "Review current debt classification: short-term borrowings can exist in addition to the current portion of long-term debt.",
        "Review D&A taxonomy coverage, loss tax benefits, leases, noncontrolling interests and excess cash before valuation.",
    ]
    return doc


ZION_METRICS = {
    "revenue": "revenue",
    "ebit": "operating_income",
    "net_income": "net_income",
    "capex": "capital_expenditures",
    "d_and_a": "depreciation_and_amortization",
    "nwc": "net_working_capital",
    "book_value": "shareholders_equity",
    "tax_rate": "effective_tax_rate",
    "short_term_debt": "short_term_debt",
    "long_term_debt": "long_term_debt",
    "cash": "cash_and_cash_equivalents",
    "preferred_equity": "preferred_equity",
    "minority_interest": "minority_interest",
    "other_nonoperating_assets": "other_nonoperating_assets",
    "diluted_shares": "weighted_average_diluted_shares",
    "current_assets": "current_assets",
    "current_liabilities": "current_liabilities",
    "tax_expense": "income_tax_expense",
    "pretax_income": "pretax_income",
}


def zion_document(packet, ticker, asof):
    if not isinstance(packet, dict) or packet.get("symbol") != ticker:
        raise ProviderError("Zion returned a mismatched company packet.")
    fundamentals = packet.get("fundamentals", {})
    if packet.get("status") != "AVAILABLE" or fundamentals.get("status") != "AVAILABLE":
        raise ProviderError("Zion company fundamentals are unavailable.")
    annual = fundamentals.get("annual", [])
    if not isinstance(annual, list):
        raise ProviderError("Zion annual observations must be a list.")
    doc = blank_document(ticker, ticker, asof, "zion")
    doc["source"].update(
        releases=packet.get("releases", {}),
        request_id=packet.get("request_id"),
        identity=packet.get("identity", {}),
    )
    groups = {}
    inverse = {v: k for k, v in ZION_METRICS.items()}
    for obs in annual:
        if not isinstance(obs, dict) or obs.get("period_type") != "annual":
            raise ProviderError("Zion annual data contains a nonannual observation.")
        end = obs.get("period_end")
        metric = inverse.get(obs.get("metric_id"))
        if not end or end > asof or metric is None:
            continue
        available = str(obs.get("available_at", ""))
        if not available or available[:10] > asof:
            continue
        expected = (
            "shares" if metric == "diluted_shares" else "pure" if metric == "tax_rate" else "USD"
        )
        if obs.get("unit") != expected:
            raise ProviderError(
                f"Zion {metric} unit must be {expected}. No FX or scale conversion is implicit."
            )
        value = number(obs.get("value_decimal", obs.get("value")), metric)
        record = groups.setdefault(end, {})
        if metric in record and record[metric][0] != value:
            raise ProviderError(
                f"Zion has conflicting {metric} observations for {end}. Resolve revisions before valuation."
            )
        record[metric] = (value, deepcopy(obs))
    ends = sorted(k for k, v in groups.items() if "revenue" in v)[-3:]
    if len(ends) != 3:
        raise ProviderError(
            "Zion needs three annual revenue periods available at the valuation date. Use manual input for missing coverage."
        )
    for end in ends:
        group = groups[end]
        val = lambda k: group.get(k, (None, None))[0]
        row = {
            "period_end": end,
            "available_at": max(v[1]["available_at"] for v in group.values()),
            "provenance": {k: v[1] for k, v in group.items()},
            **{k: val(k) for k in HISTORY_FIELDS},
        }
        if row["capex"] is not None:
            row["capex"] = abs(row["capex"])
        if row["nwc"] is None and all(
            val(k) is not None
            for k in ["current_assets", "cash", "current_liabilities", "short_term_debt"]
        ):
            row["nwc"] = (val("current_assets") - val("cash")) - (
                val("current_liabilities") - val("short_term_debt")
            )
        if (
            row["tax_rate"] is None
            and val("pretax_income") not in {None, 0}
            and val("tax_expense") is not None
        ):
            row["tax_rate"] = val("tax_expense") / val("pretax_income")
        doc["historical"].append(row)
    for k in BRIDGE_FIELDS:
        doc["bridge"][k] = val(k)
    doc["bridge"]["as_of"] = ends[-1]
    doc["market"]["diluted_shares"] = val("diluted_shares")
    latest = packet.get("prices", {}).get("latest", {}).get("observation") or {}
    if (
        latest
        and packet.get("prices", {}).get("latest", {}).get("status") == "AVAILABLE"
        and latest.get("session_date", "9999") <= asof
        and latest.get("unit") is not None
    ):
        if latest.get("unit") != "USD/share":
            raise ProviderError("Zion price currency does not match USD financials.")
        doc["market"]["price"] = number(latest.get("close"), "Zion close", 0)
        doc["market"]["price_as_of"] = latest.get("session_date")
        doc["source"]["price_observation"] = deepcopy(latest)
    doc["source"]["warnings"] = [
        "Confirm operating-company eligibility, dilution, debt classification and any missing fields. Zion release and observation provenance are preserved."
    ]
    if latest and latest.get("unit") is None:
        doc["source"]["warnings"].append(
            "Price currency is unverified. Enter a dated USD market price manually."
        )
    return doc


def provider_setting(name):
    try:
        from flask import current_app, has_request_context, request

        if has_request_context() and current_app.config.get("CLOUDFLARE"):
            return str(getattr(request.environ["workers.env"], name, ""))
    except ImportError:
        pass
    return os.getenv(name, "")


def configured_url(name):
    base = provider_setting(name).rstrip("/")
    p = urlparse(base)
    if p.scheme != "https" or not p.netloc or p.username or p.password or p.query or p.fragment:
        raise ProviderError(f"Configure {name} as an HTTPS base URL on the server.")
    return base


def load_document(source, ticker, asof):
    ticker = ticker_symbol(ticker)
    iso_date(asof, "Valuation date")
    if source == "sample":
        return demo_document()
    if source == "manual":
        doc = blank_document(ticker, ticker, asof, "manual")
        year = date.fromisoformat(asof).year
        doc["historical"] = [
            {"period_end": f"{y}-12-31", **dict.fromkeys(HISTORY_FIELDS)}
            for y in range(year - 3, year)
        ]
        doc["bridge"]["as_of"] = doc["historical"][-1]["period_end"]
        doc["source"]["warnings"] = [
            "User-entered financials require independent source verification."
        ]
        return doc
    http = JsonHTTP()
    if source in {"auto", "yahoo"}:
        from yahoo_provider import load_yahoo

        return load_yahoo(ticker, asof, http)
    if source == "sec":
        return load_sec(ticker, asof, http)
    if source == "zion":
        base = configured_url("ZION_API_BASE_URL")
        token = provider_setting("ZION_API_TOKEN")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        # Zion supports an explicit point-in-time instant; date-only values are invalid.
        packet = http.get(
            f"{base}/v1/company/{ticker}",
            headers=headers,
            params={"as_of": f"{asof}T23:59:59Z", "limit": 1000},
        )
        return zion_document(packet, ticker, asof)
    if source == "api":
        base = configured_url("DCF_API_BASE_URL")
        token = provider_setting("DCF_API_TOKEN")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        doc = http.get(
            f"{base}/v1/valuation/financials/{ticker}", headers=headers, params={"as_of": asof}
        )
        if not isinstance(doc, dict) or doc.get("company", {}).get("ticker") != ticker:
            raise ProviderError("API returned a mismatched financial document.")
        parse_document(doc)
        return doc
    raise ValueError("Choose sample, SEC, Zion or the configured financial API.")


def load_data_from_api(ticker):
    # Compatibility wrapper. The browser offers manual completion when provider fields are missing.
    source = os.getenv("DCF_DEFAULT_PROVIDER", "zion")
    return parse_document(
        load_document(source, ticker, datetime.now(timezone.utc).date().isoformat())
    )
