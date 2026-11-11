"""Served market data: price history through the serving layer contract only.

The transport is a fake; no test touches the network. Pages follow the
/history contract: rows with raw and adjusted price bases, permno,
input_sha256 as the release ID, coverage, and a next pointer.
"""

from datetime import date, timedelta

import pytest

import served_market
from dcf_loader import ProviderError

RELEASE = "a" * 64
ASOF = "2026-10-22"


@pytest.fixture(autouse=True)
def _served_token(monkeypatch):
    monkeypatch.setenv("ZION_HISTORY_TOKEN", "test-token")


def row(day, raw, adjusted=None):
    return {
        "date": day,
        "permno": 14593,
        "raw_observed_price": raw,
        "split_adjusted_price": raw,
        "distribution_adjusted_price": raw if adjusted is None else adjusted,
        "source_total_return": None,
        "source_return_ex_ordinary_dividends": None,
        "missing_adjustment_factors": 0,
    }


class FakeTransport:
    """Serves canned pages keyed by symbol, honoring part/offset params."""

    def __init__(self, pages_by_symbol):
        self.pages_by_symbol = pages_by_symbol
        self.calls = []

    def get(self, url, headers=None, params=None):
        self.calls.append(dict(params))
        pages = self.pages_by_symbol[params["symbol"]]
        part = params.get("part") or 0
        return pages[part]


def page(rows, nxt=None, release=RELEASE):
    return {
        "symbol": "TEST",
        "permno": 14593,
        "input_sha256": release,
        "coverage": {"date_min": rows[0]["date"], "date_max": rows[-1]["date"], "rows": len(rows)},
        "rows": rows,
        "next": nxt,
    }


def test_history_pages_follows_pagination_and_pins_release():
    first = page(
        [row("2026-10-20", 10.0), row("2026-10-21", 11.0)],
        nxt={"part": 1, "offset": 0, "expected_input_sha256": RELEASE},
    )
    second = page([row("2026-10-22", 12.0)])
    transport = FakeTransport({"TEST": [first, second]})
    data = served_market.history_pages("TEST", "2026-10-01", ASOF, transport=transport)
    assert [r["date"] for r in data["rows"]] == ["2026-10-20", "2026-10-21", "2026-10-22"]
    assert data["release"] == RELEASE
    assert data["permno"] == 14593
    assert transport.calls[1]["expected_input_sha256"] == RELEASE


def test_history_pages_rejects_a_release_change_mid_pagination():
    first = page([row("2026-10-21", 11.0)], nxt={"part": 1, "offset": 0})
    second = page([row("2026-10-22", 12.0)], release="b" * 64)
    transport = FakeTransport({"TEST": [first, second]})
    with pytest.raises(ProviderError, match="release changed"):
        served_market.history_pages("TEST", "2026-10-01", ASOF, transport=transport)


def test_latest_price_uses_last_served_close_on_or_before_asof():
    transport = FakeTransport(
        {"TEST": [page([row("2026-10-20", 10.0), row("2026-10-21", 11.5), row("2026-10-22", 12.0)])]}
    )
    quote = served_market.latest_price("TEST", "2026-10-21", transport=transport)
    assert quote["price"] == 11.5
    assert quote["price_as_of"] == "2026-10-21"
    assert quote["provenance"]["release"] == RELEASE
    assert quote["provenance"]["permno"] == 14593


def test_latest_price_without_rows_fails_closed():
    transport = FakeTransport({"TEST": [page([row("2026-10-20", 10.0)])]})
    with pytest.raises(ProviderError, match="no served price observation"):
        served_market.latest_price("TEST", "2026-10-19", transport=transport)


def weekly_series(weeks=150, stock_exponent=2.0):
    """One row per week; the stock's weekly return is stock_exponent times SPY's."""
    start = date(2023, 12, 4)  # a Monday
    bench_price, stock_price = 100.0, 100.0
    bench_rows, stock_rows = [], []
    for i in range(weeks):
        day = (start + timedelta(weeks=i)).isoformat()
        bench_rows.append(row(day, bench_price))
        stock_rows.append(row(day, stock_price))
        r = 0.01 if i % 2 else -0.006
        bench_price *= 1 + r
        stock_price *= 1 + stock_exponent * r
    return bench_rows, stock_rows


def test_served_beta_recovers_the_known_relationship():
    bench_rows, stock_rows = weekly_series()
    transport = FakeTransport({"TEST": [page(stock_rows)], "SPY": [page(bench_rows)]})
    beta, n = served_market.served_beta("TEST", ASOF, transport=transport)
    assert beta == pytest.approx(2.0, abs=1e-9)
    assert n >= 104


def test_served_beta_requires_104_aligned_weeks():
    bench_rows, stock_rows = weekly_series(weeks=60)
    transport = FakeTransport({"TEST": [page(stock_rows)], "SPY": [page(bench_rows)]})
    with pytest.raises(ProviderError, match="104 aligned weekly"):
        served_market.served_beta("TEST", ASOF, transport=transport)


def test_risk_free_rate_fails_closed_naming_the_missing_served_source():
    with pytest.raises(ProviderError, match="SERVED_RISK_FREE_RATE_NOT_CONFIGURED"):
        served_market.risk_free_rate(ASOF)


def test_missing_binding_is_a_clear_not_configured_error():
    with pytest.raises(ProviderError, match="SERVED_MARKET_NOT_CONFIGURED"):
        served_market.latest_price("TEST", ASOF)
