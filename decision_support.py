"""Dated decision references; never silently replace a forecast assumption."""

import json
import math
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from urllib.parse import quote

from dcf_loader import JsonHTTP, ProviderError, ticker_symbol


def number(value):
    value = value.get("raw") if isinstance(value, dict) else value
    return (
        value
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
        else None
    )


def historical_growth(rows, key):
    annual = []
    previous = None
    for row in rows:
        value = number(row.get(key))
        growth = (
            value / previous - 1
            if value is not None and previous is not None and previous > 0 and value >= 0
            else None
        )
        annual.append({"period_end": row["period_end"], "value": value, "growth": growth})
        previous = value
    cagr = None
    if (
        len(annual) > 1
        and annual[0]["value"]
        and annual[0]["value"] > 0
        and annual[-1]["value"] is not None
        and annual[-1]["value"] >= 0
    ):
        years = len(annual) - 1
        if years > 0:
            cagr = (annual[-1]["value"] / annual[0]["value"]) ** (1 / years) - 1
    return {
        "annual": annual,
        "cagr": cagr,
        "basis": key,
        "source": "Yahoo annual financial statements; computed from reported fiscal-year amounts",
    }


class ScriptPackets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.parts = []
        self.packets = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.in_script = dict(attrs).get("type") == "application/json"
            self.parts = []

    def handle_data(self, data):
        if self.in_script:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.in_script:
            try:
                packet = json.loads("".join(self.parts))
                if isinstance(packet, dict) and isinstance(packet.get("body"), str):
                    self.packets.append(json.loads(packet["body"]))
            except (ValueError, TypeError):
                pass
            self.in_script = False


def parse_analysts(html, ticker):
    parser = ScriptPackets()
    parser.feed(html)
    for packet in parser.packets:
        summary = packet.get("quoteSummary") if isinstance(packet, dict) else None
        results = summary.get("result") if isinstance(summary, dict) else None
        if not isinstance(results, list) or not results:
            continue
        root = results[0]
        if not isinstance(root, dict):
            continue
        price = root.get("price", {})
        if (
            not isinstance(price, dict)
            or price.get("symbol") != ticker
            or price.get("currency") != "USD"
        ):
            continue
        revenues = []
        trend_packet = root.get("earningsTrend") or {}
        if not isinstance(trend_packet, dict):
            trend_packet = {}
        trends = trend_packet.get("trend") or []
        if not isinstance(trends, list):
            trends = []
        for trend in trends:
            if not isinstance(trend, dict):
                continue
            if trend.get("period") not in {"0y", "+1y"}:
                continue
            estimate = trend.get("revenueEstimate", {})
            if not isinstance(estimate, dict) or estimate.get("revenueCurrency") != "USD":
                continue
            end = trend.get("endDate")
            try:
                date.fromisoformat(end)
            except (TypeError, ValueError):
                continue
            revenues.append(
                {
                    "period": trend["period"],
                    "period_end": end,
                    "growth": number(estimate.get("growth")),
                    "average": number(estimate.get("avg")),
                    "low": number(estimate.get("low")),
                    "high": number(estimate.get("high")),
                    "year_ago_revenue": number(estimate.get("yearAgoRevenue")),
                    "analysts": number(estimate.get("numberOfAnalysts")),
                }
            )
        financial = root.get("financialData") or {}
        if not isinstance(financial, dict):
            financial = {}
        target = {
            k: number(financial.get(v))
            for k, v in {
                "mean": "targetMeanPrice",
                "median": "targetMedianPrice",
                "low": "targetLowPrice",
                "high": "targetHighPrice",
                "analysts": "numberOfAnalystOpinions",
            }.items()
        }
        if target["mean"] is not None and target["mean"] <= 0:
            target["mean"] = None
        if not revenues and target["mean"] is None and number(price.get("marketCap")) is None:
            continue
        return {
            "revenue": revenues,
            "target": target,
            "currency": "USD",
            "market_cap": number(price.get("marketCap")),
            "source": "Yahoo Finance analyst consensus",
            "source_url": f"https://finance.yahoo.com/quote/{quote(ticker, safe='')}/analysis/",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "horizon": "Analyst price targets typically refer to the next 12 months; provider does not supply individual target dates.",
        }
    raise ProviderError(
        "Verified USD analyst revenue estimates and price targets are unavailable for this ticker."
    )


def load_analysts(ticker):
    ticker = ticker_symbol(ticker)
    http = JsonHTTP(budget=8)
    key = f"yahoo-analyst-references-v2-{ticker}"
    cached = http.store.get(key)
    if cached is not None:
        if "error" in cached:
            raise ProviderError(cached["error"])
        return cached
    try:
        result = parse_analysts(
            http.get(
                f"https://finance.yahoo.com/quote/{quote(ticker, safe='')}/analysis/",
                headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html"},
                text_response=True,
            ),
            ticker,
        )
    except ProviderError as exc:
        http.store.set(key, {"error": str(exc)}, 300)
        raise
    http.store.set(key, result, 3600)
    return result


# Curated product/segment taxonomy, not reported segment revenue or a statistical equivalence claim.
BUSINESSES = {
    "AAPL": ("Consumer electronics", {"devices", "computers", "consumer ecosystem"}),
    "DELL": ("Computer hardware", {"computers", "enterprise hardware"}),
    "HPQ": ("Computer hardware", {"computers", "printing"}),
    "HPE": ("Enterprise hardware", {"enterprise hardware", "cloud infrastructure"}),
    "NVDA": ("Semiconductors", {"chips", "AI accelerators", "data centers"}),
    "AMD": ("Semiconductors", {"chips", "AI accelerators", "computers", "data centers"}),
    "AVGO": ("Semiconductors", {"chips", "networking", "infrastructure software"}),
    "QCOM": ("Semiconductors", {"chips", "mobile devices"}),
    "INTC": ("Semiconductors", {"chips", "computers", "data centers"}),
    "MSFT": ("Software", {"enterprise software", "cloud infrastructure", "consumer ecosystem"}),
    "ORCL": ("Software", {"enterprise software", "cloud infrastructure", "databases"}),
    "CRM": ("Software", {"enterprise software", "customer software"}),
    "ADBE": ("Software", {"enterprise software", "creative software"}),
    "NOW": ("Software", {"enterprise software", "workflow software"}),
    "AMZN": ("Retail and cloud", {"retail", "cloud infrastructure", "advertising"}),
    "WMT": ("Retail", {"retail", "grocery"}),
    "TGT": ("Retail", {"retail", "general merchandise"}),
    "COST": ("Retail", {"retail", "grocery", "membership"}),
    "GOOGL": ("Internet", {"advertising", "cloud infrastructure", "consumer ecosystem"}),
    "META": ("Internet", {"advertising", "social media"}),
    "SNAP": ("Internet", {"advertising", "social media"}),
    "PINS": ("Internet", {"advertising", "social media"}),
    "KO": ("Beverages", {"beverages", "distribution"}),
    "PEP": ("Beverages", {"beverages", "snacks", "distribution"}),
    "KDP": ("Beverages", {"beverages", "distribution"}),
    "MNST": ("Beverages", {"beverages", "energy drinks"}),
    "JNJ": ("Pharmaceuticals", {"pharmaceuticals", "medical devices"}),
    "PFE": ("Pharmaceuticals", {"pharmaceuticals"}),
    "MRK": ("Pharmaceuticals", {"pharmaceuticals"}),
    "BMY": ("Pharmaceuticals", {"pharmaceuticals"}),
    "ABBV": ("Pharmaceuticals", {"pharmaceuticals"}),
    "XOM": ("Energy", {"oil and gas", "refining"}),
    "CVX": ("Energy", {"oil and gas", "refining"}),
    "COP": ("Energy", {"oil and gas"}),
    "EOG": ("Energy", {"oil and gas"}),
    "OXY": ("Energy", {"oil and gas", "chemicals"}),
}


def peer_fit(target, peer, target_cap, peer_cap):
    target_business = BUSINESSES.get(target)
    business = BUSINESSES.get(peer)
    shared = sorted(target_business[1] & business[1]) if target_business and business else []
    same = bool(target_business and business and target_business[0] == business[0])
    ratio = (
        peer_cap / target_cap
        if target_cap and target_cap > 0 and peer_cap and peer_cap > 0
        else None
    )
    caveats = []
    if ratio is not None and not 0.25 <= ratio <= 4:
        caveats.append("Material size mismatch; market equity outside 0.25–4× target.")
    if target == "AMZN" and peer in {"WMT", "TGT", "COST"}:
        caveats.append("Retail fit only; does not match AWS cloud economics.")
    if target == "AAPL":
        caveats.append("Hardware fit only; ecosystem/services mix differs materially.")
    score = (
        (3 if same else 0)
        + len(shared)
        + (max(0, 1 - abs(math.log(ratio)) / math.log(4)) if ratio else 0)
    )
    return {
        "industry": business[0] if business else "Unverified",
        "segments": sorted(business[1]) if business else [],
        "shared_products_segments": shared,
        "fit_label": "Industry and product fit"
        if same and shared
        else "Partial product/competitive fit"
        if shared
        else "Business fit unverified",
        "market_equity_value": peer_cap,
        "market_cap_ratio": ratio,
        "score": round(score, 3),
        "caveats": caveats,
        "source": "Curated industry/product taxonomy; size from Yahoo price × annual diluted shares (market-equity proxy, not current outstanding-share market cap). Segment revenue weights are not verified.",
    }
