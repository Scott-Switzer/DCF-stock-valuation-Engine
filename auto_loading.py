"""Ticker-to-model assembly. Forecasts and peer selections remain explicit assumptions."""

from copy import deepcopy
from datetime import datetime, timezone
import time
from dcf_code import DCFAssumptions, DCFModel
from dcf_loader import JsonHTTP, ProviderError, parse_document, ticker_symbol, provider_setting
from yahoo_provider import load_yahoo, load_company_metrics, recalculate_costs, BASE, HEADERS

# Starter sets are visible and editable, not a claim that all businesses are identical.
PEER_GROUPS = (
    ("Computer hardware", ("AAPL", "DELL", "HPQ", "HPE")),
    ("Semiconductors", ("NVDA", "AMD", "AVGO", "QCOM", "INTC")),
    ("Software", ("MSFT", "ORCL", "CRM", "ADBE", "NOW")),
    ("Internet platforms", ("GOOGL", "GOOG", "META", "SNAP", "PINS")),
    ("Retail", ("AMZN", "WMT", "TGT", "COST")),
    ("Beverages", ("KO", "PEP", "KDP", "MNST")),
    ("Pharmaceuticals", ("JNJ", "PFE", "MRK", "BMY", "ABBV")),
    ("Energy", ("XOM", "CVX", "COP", "EOG", "OXY")),
)


def starter_peers(ticker, http):
    from decision_support import BUSINESSES

    if ticker == "AMZN":
        return "Retail and cloud segment candidates; different segment mixes", [
            "WMT",
            "MSFT",
            "GOOGL",
            "COST",
        ]
    for label, members in PEER_GROUPS:
        if ticker in members:
            return label, [
                s
                for s in members
                if s != ticker
                and not ({s, ticker} <= {"GOOG", "GOOGL"})
                and (
                    s not in BUSINESSES
                    or ticker not in BUSINESSES
                    or BUSINESSES[s][0] == BUSINESSES[ticker][0]
                    or BUSINESSES[s][1] & BUSINESSES[ticker][1]
                )
            ][:4]
    raw = http.get(
        f"{BASE}/v6/finance/recommendationsbysymbol/{ticker}",
        headers=HEADERS,
        ttl=3600,
        cache_key=f"yahoo-peer-suggestions-v1-{ticker}",
    )
    results = raw.get("finance", {}).get("result") or []
    peers = results[0].get("recommendedSymbols", []) if results else []
    symbols = []
    for peer in peers:
        try:
            symbol = ticker_symbol(peer.get("symbol"))
        except ValueError:
            continue
        if symbol != ticker and symbol not in symbols:
            symbols.append(symbol)
    return "Yahoo suggestions; industry comparability unverified", symbols[:4]


def company_classification(ticker, http):
    identity = provider_setting("EDGAR_IDENTITY")
    if "@" not in identity:
        return None
    headers = {"User-Agent": identity, "Accept": "application/json"}
    directory = http.get(
        "https://www.sec.gov/files/company_tickers.json",
        headers=headers,
        ttl=21600,
        cache_key="sec-directory",
    )
    entry = next(
        (
            v
            for v in directory.values()
            if isinstance(v, dict) and str(v.get("ticker", "")).replace(".", "-") == ticker
        ),
        None,
    )
    if entry is None:
        return None
    cik = str(entry["cik_str"]).zfill(10)
    packet = http.get(
        f"https://data.sec.gov/submissions/CIK{cik}.json",
        headers=headers,
        ttl=21600,
        cache_key=f"sec-classification-{cik}",
    )
    sic = str(packet.get("sic", ""))
    if not sic.isdigit():
        return None
    return {
        "sic": sic,
        "description": packet.get("sicDescription", ""),
        "entity_type": packet.get("entityType", ""),
        "source": "SEC submissions",
    }


def relative_metrics(doc):
    latest = doc["historical"][-1]
    shares = doc["market"]["diluted_shares"]
    ordinary_equity = doc["source"].get("capital_costs", {}).get("market_equity_value")
    if ordinary_equity is None:
        # This is the same diluted-share market-equity convention used by RelativeModel.
        ordinary_equity = doc["market"]["price"] * shares
    b = doc["bridge"]
    ev = (
        ordinary_equity
        + b["short_term_debt"]
        + b["long_term_debt"]
        + b["preferred_equity"]
        + b["minority_interest"]
        - b["cash"]
        - b["other_nonoperating_assets"]
    )
    common = doc["source"]["common_book_equity"]["value"]
    denoms = {
        "ev_revenue": latest["revenue"],
        "ev_ebitda": latest["ebit"] + latest["d_and_a"],
        "ev_ebit": latest["ebit"],
        "pe": latest["net_income"],
        "pb": common,
    }
    return {
        key: (ev if key.startswith("ev_") else ordinary_equity) / value
        if value is not None and value > 0
        else None
        for key, value in denoms.items()
    }


def load_method(method, ticker, asof=None, equity_risk_premium=0.05, credit_spread=0.015):
    if method not in {"dcf", "ddm", "relative"}:
        raise ValueError("Choose DCF, DDM or relative valuation.")
    from decision_support import historical_growth, peer_fit

    start = time.monotonic()
    asof = asof or datetime.now(timezone.utc).date().isoformat()
    ticker = ticker_symbol(ticker)
    http = JsonHTTP(budget=40)
    dcf = load_yahoo(
        ticker, asof, http, include_capital_costs=method != "relative", require_wacc=method == "dcf"
    )
    dcf["source"]["revenue_growth_reference"] = historical_growth(dcf["historical"], "revenue")
    dividend_rows = dcf["source"]["common_dividends"]["historical"]
    dcf["source"]["dividend_growth_reference"] = historical_growth(dividend_rows, "value")
    dcf["source"]["dividend_per_share_growth_reference"] = historical_growth(
        [
            {
                "period_end": row["period_end"],
                "value": row["value"] / row["shares"]
                if row["value"] is not None and row["shares"] and row["shares"] > 0
                else None,
            }
            for row in dividend_rows
        ],
        "value",
    )
    try:
        classification = company_classification(ticker, http)
    except ProviderError:
        classification = None
    if classification:
        dcf["source"]["classification"] = classification
        dcf["company"]["sector"] = classification["description"]
        sic = int(classification["sic"])
        if 6000 <= sic <= 6999:
            raise ProviderError(
                "Automatic loading currently supports operating companies. This SEC industry needs sector-specific financial-firm or real-estate inputs."
            )
        dcf["source"]["warnings"] = [
            w
            for w in dcf["source"]["warnings"]
            if not w.startswith("Sector and industry are unavailable")
        ]
    else:
        dcf["source"]["warnings"].append(
            "SEC industry classification was unavailable; review the operating-company suitability confirmation."
        )
    costs = (
        recalculate_costs(dcf, equity_risk_premium, credit_spread) if method != "relative" else {}
    )
    from app import default_form
    from suite_views import suite_form, suite_assumptions, suite_evaluate

    form = default_form(dcf)
    form.update(
        mode="auto",
        wacc=(costs.get("wacc") or 0.065) * 100,
        equity_risk_premium=equity_risk_premium * 100,
        credit_spread=credit_spread * 100,
    )
    doc = dcf
    if method == "ddm":
        dividend = dcf["source"]["common_dividends"]
        if dividend["value"] is None or dividend["value"] <= 0:
            raise ProviderError(
                "This ticker has no verified positive annual common dividends in the snapshot. Use DCF or relative valuation instead of DDM."
            )
        doc = {
            k: deepcopy(dcf[k]) for k in ["valuation_date", "units", "company", "market", "source"]
        }
        doc.update(
            schema_version="ddm-financials-v1",
            base_common_dividends=dividend["value"],
            dividend_as_of=dividend["period_end"],
        )
        form = suite_form(method, doc)
        form.update(
            required_return=costs["cost_of_equity"] * 100,
            equity_risk_premium=equity_risk_premium * 100,
            credit_spread=credit_spread * 100,
        )
        suite_evaluate(
            method,
            doc,
            suite_assumptions(
                method,
                {
                    "dividend_growth_rates": [0.05] * 5,
                    "required_return": costs["cost_of_equity"],
                    "terminal_growth_rate": 0.02,
                },
            ),
        )
    elif method == "relative":
        a = DCFAssumptions(revenue_growth_rates=[0.05] * 5, terminal_growth_rate=0.02)
        forecast_model = DCFModel(parse_document(dcf), a)
        first = forecast_model.forecast_cash_flows()[0]
        latest = dcf["historical"][-1]
        common = dcf["source"]["common_book_equity"]["value"]
        doc = {
            k: deepcopy(dcf[k])
            for k in ["valuation_date", "units", "company", "market", "source", "bridge"]
        }
        doc.update(
            schema_version="relative-financials-v1",
            target={
                "historical_as_of": latest["period_end"],
                "historical": {
                    "revenue": latest["revenue"],
                    "ebitda": latest["ebit"] + latest["d_and_a"],
                    "ebit": latest["ebit"],
                    "net_income": latest["net_income"],
                    "book_value": common,
                },
                "forward": {
                    "revenue": first["Revenue"],
                    "ebitda": first["EBITDA"],
                    "ebit": first["EBIT"],
                    "net_income": first["Net Income"],
                    "book_value": common * 1.05 if common is not None else None,
                },
            },
            comparables=[],
        )
        label, symbols = starter_peers(ticker, http)
        doc["source"]["warnings"].append(
            f"Starter peer set: {label}. Review or replace peers; equal weighting does not establish business comparability."
        )
        doc["source"]["warnings"].append(
            "Forward target metrics use a 5% revenue-growth starter forecast and historical operating ratios; common book equity starts at 5% growth. These are editable forecast assumptions."
        )
        for symbol in symbols:
            try:
                peer = load_company_metrics(symbol, asof, http)
                doc["comparables"].append(
                    {
                        "ticker": symbol,
                        "name": peer["company"]["name"],
                        "as_of": peer["market"]["price_as_of"],
                        "available_at": asof,
                        "currency": "USD",
                        "source": f"Yahoo current price / latest annual fundamentals {peer['historical'][-1]['period_end']}",
                        "multiples": relative_metrics(peer),
                        "fit": peer_fit(
                            ticker,
                            symbol,
                            dcf["market"]["price"] * dcf["market"]["diluted_shares"],
                            peer["market"]["price"] * peer["market"]["diluted_shares"],
                        ),
                        "provenance": {
                            "financials": peer["historical"][-1],
                            "bridge": peer["bridge"],
                            "market": peer["market"],
                            "common_book_equity": peer["source"]["common_book_equity"],
                        },
                    }
                )
            except (ProviderError, ValueError) as exc:
                doc["source"]["warnings"].append(f"Peer {symbol} unavailable: {exc}")
        if not doc["comparables"]:
            raise ProviderError(
                "No complete starter peer snapshots were available. Retry or import a sourced peer set."
            )
        doc["comparables"].sort(key=lambda peer: peer["fit"]["score"], reverse=True)
        doc["source"]["peer_suggestions"] = [
            {"ticker": peer["ticker"], "name": peer["name"], **peer["fit"]}
            for peer in doc["comparables"]
        ]
        included = [
            k
            for k in ["ev_revenue", "ev_ebitda", "pe"]
            if doc["target"]["forward"][
                {"ev_revenue": "revenue", "ev_ebitda": "ebitda", "pe": "net_income"}[k]
            ]
            > 0
            and any(
                p["multiples"][k] is not None and p["multiples"][k] > 0 for p in doc["comparables"]
            )
        ]
        form = suite_form(method, doc)
        form.update(
            {
                f"include_{key}": "yes" if key in included else ""
                for key in ["ev_revenue", "ev_ebitda", "ev_ebit", "pe", "pb"]
            }
        )
        suite_evaluate(method, doc, suite_assumptions(method, {"included_methods": included}))
    return {
        "financials": doc,
        "form": form,
        "warnings": doc["source"]["warnings"],
        "load_summary": {
            "company": doc["company"]["name"],
            "ticker": ticker,
            "elapsed_seconds": round(time.monotonic() - start, 2),
            "historical_periods": [r["period_end"] for r in dcf["historical"]],
            "peer_count": len(doc.get("comparables", [])),
            "capital_costs": costs,
            "snapshot_kind": "current; not historical point-in-time",
        },
    }
