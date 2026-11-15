"""Served market data: prices and beta inputs from the Zion serving layer only.

Price history comes from the serving layer's ``/history`` contract, reached
through the ``ZION_FINANCIAL_QUERY`` service binding so no request leaves the
account. Pages carry ``rows`` (date plus raw and adjusted price bases),
``permno``, ``input_sha256`` (the source release ID) and ``coverage``; the
``next`` pointer paginates. Nothing here falls back to Yahoo Finance or any
other direct source: a missing binding or credential is a clear
not-configured error, and the risk-free rate has no served source yet, so
``risk_free_rate`` fails closed naming that gap instead of pulling a
Treasury yield from Yahoo.
"""

import math
from datetime import date, timedelta

from dcf_loader import ZION_BINDING_ORIGIN, ProviderError, provider_setting, ticker_symbol

HISTORY_PATH = "/history"
BENCHMARK_SYMBOL = "SPY"
PAGE_LIMIT = 500
MAX_PAGES = 40
BETA_WINDOW_DAYS = 5 * 366
MIN_BETA_WEEKS = 104


def _fail(message):
    raise ProviderError("Served market data: " + message)


def _transport(transport):
    if transport is not None:
        return transport
    from zion_equity_claims_service import ServiceBindingHTTP, service_binding

    binding = service_binding()
    if binding is None:
        _fail(
            "not configured (SERVED_MARKET_NOT_CONFIGURED): the "
            "ZION_FINANCIAL_QUERY service binding is unavailable in this "
            "runtime, so served price history cannot be reached."
        )
    return ServiceBindingHTTP(binding)


def _headers():
    from equity_claims_provider import claims_headers
    from zion_equity_claims_service import configured_caller

    history_credential = provider_setting("ZION_HISTORY_TOKEN")
    service_credential = provider_setting("ZION_SERVICE_TOKEN")
    try:
        return claims_headers(
            **{
                "token": history_credential,
                "service_token": service_credential,
                "caller": configured_caller(),
            }
        )
    except Exception:
        _fail(
            "credentials are not configured (SERVED_MARKET_NOT_CONFIGURED): "
            "set ZION_HISTORY_TOKEN or the scoped ZION_SERVICE_TOKEN on the "
            "server so the serving layer can be queried."
        )


def _finite(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        _fail(f"{label} requires a finite numeric observation.")
    return float(value)


def history_pages(symbol, date_from, date_to, *, transport=None):
    """Every served daily price row for ``symbol`` in the window, oldest first."""
    symbol = ticker_symbol(symbol)
    transport = _transport(transport)
    headers = _headers()
    params = {
        "symbol": symbol,
        "date_from": date_from,
        "date_to": date_to,
        "limit": PAGE_LIMIT,
    }
    rows, release, permno, coverage = [], None, None, {}
    for _ in range(MAX_PAGES):
        page = transport.get(ZION_BINDING_ORIGIN + HISTORY_PATH, headers=headers, params=params)
        if not isinstance(page, dict) or not isinstance(page.get("rows"), list):
            _fail(f"the serving layer returned an invalid history page for {symbol}.")
        if release is None:
            release = page.get("input_sha256")
            permno = page.get("permno")
            coverage = page.get("coverage") or {}
        elif page.get("input_sha256") != release:
            _fail("the served price history release changed during pagination.")
        rows.extend(page["rows"])
        nxt = page.get("next")
        if not nxt:
            break
        params = {
            "symbol": symbol,
            "date_from": date_from,
            "date_to": date_to,
            "limit": PAGE_LIMIT,
            "part": nxt.get("part"),
            "offset": nxt.get("offset"),
            "expected_input_sha256": nxt.get("expected_input_sha256") or release,
        }
    else:
        _fail(f"served price history for {symbol} exceeded its page budget.")
    rows.sort(key=lambda row: str(row.get("date") or ""))
    return {
        "symbol": symbol,
        "permno": permno,
        "release": release,
        "coverage": coverage,
        "rows": rows,
    }


def _adjusted_price(row):
    """Total-return price basis for one row, or None when no usable basis exists."""
    for key in ("distribution_adjusted_price", "split_adjusted_price", "raw_observed_price"):
        value = row.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
            return float(value)
    return None


def latest_price(symbol, asof, *, transport=None):
    """Latest served close on or before ``asof``. Never loads statements or peers."""
    symbol = ticker_symbol(symbol)
    start = (date.fromisoformat(asof) - timedelta(days=370)).isoformat()
    data = history_pages(symbol, start, asof, transport=transport)
    usable = []
    for row in data["rows"]:
        day = str(row.get("date") or "")
        if not day or day > asof:
            continue
        raw = row.get("raw_observed_price")
        price = raw if isinstance(raw, (int, float)) and not isinstance(raw, bool) and raw > 0 else _adjusted_price(row)
        if price is not None:
            usable.append((day, float(price)))
    if not usable:
        _fail(f"no served price observation for {symbol} on or before {asof}.")
    price_day, price = usable[-1]
    return {
        "ticker": symbol,
        "price": price,
        "price_as_of": price_day,
        "provenance": {
            "provider": "Zion serving layer price history (CRSP)",
            "release": data["release"],
            "permno": data["permno"],
            "basis": "raw_observed_price",
        },
    }


def weekly_total_returns(symbol, asof, *, transport=None):
    """ISO-week total returns from served daily adjusted prices over five years."""
    start = (date.fromisoformat(asof) - timedelta(days=BETA_WINDOW_DAYS)).isoformat()
    data = history_pages(symbol, start, asof, transport=transport)
    weekly = {}
    for row in data["rows"]:
        price = _adjusted_price(row)
        day_text = str(row.get("date") or "")
        if price is None or not day_text or day_text > asof:
            continue
        try:
            day = date.fromisoformat(day_text)
        except ValueError:
            continue
        weekly[day.isocalendar()[:2]] = (day, price)
    returns = {}
    previous = None
    for week in sorted(weekly):
        day, price = weekly[week]
        if previous is not None and 4 <= (day - previous[0]).days <= 10:
            returns[week] = price / previous[1] - 1
        previous = (day, price)
    return returns


def served_beta(symbol, asof, *, transport=None):
    """Beta of ``symbol`` against SPY from served weekly total returns."""
    stock = weekly_total_returns(symbol, asof, transport=transport)
    benchmark = weekly_total_returns(BENCHMARK_SYMBOL, asof, transport=transport)
    weeks = sorted(stock.keys() & benchmark.keys())
    if len(weeks) < MIN_BETA_WEEKS:
        _fail(
            f"beta requires at least {MIN_BETA_WEEKS} aligned weekly total "
            f"returns from served history; only {len(weeks)} are available."
        )
    xs, ys = [benchmark[w] for w in weeks], [stock[w] for w in weeks]
    xm, ym = sum(xs) / len(xs), sum(ys) / len(ys)
    variance = sum((x - xm) ** 2 for x in xs)
    if variance <= 0:
        _fail("benchmark variance is zero; beta is unavailable.")
    beta = sum((x - xm) * (y - ym) for x, y in zip(xs, ys)) / variance
    return _finite(beta, "computed beta"), len(weeks)


def risk_free_rate(asof):
    """Fail closed: the serving layer publishes no Treasury yield series yet."""
    raise ProviderError(
        "SERVED_RISK_FREE_RATE_NOT_CONFIGURED: the Zion serving layer does "
        "not publish a Treasury yield series yet, so the risk-free rate has "
        "no served source and capital costs cannot be completed through "
        "the data door. No direct Yahoo Treasury pull was made."
    )
