"""The direct-fetch gate: production reads through the serving layer only.

Yahoo Finance and SEC EDGAR fetches fail closed with a named missing served
source unless DCF_ALLOW_DIRECT_FETCH=1 is set for local development, in
which case they log a loud warning instead.
"""

import logging
from datetime import datetime, timezone

import pytest

from dcf_loader import (
    JsonHTTP,
    ProviderError,
    allow_direct_fetch,
    direct_fetch_guard,
    require_direct_fetch,
)

TODAY = datetime.now(timezone.utc).date().isoformat()
YAHOO_URL = "https://query2.finance.yahoo.com/v8/finance/chart/TEST"
SEC_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json"


@pytest.fixture(autouse=True)
def _gate_closed(monkeypatch):
    monkeypatch.delenv("DCF_ALLOW_DIRECT_FETCH", raising=False)


def test_gate_defaults_closed_and_opens_only_on_explicit_flag(monkeypatch):
    assert allow_direct_fetch() is False
    monkeypatch.setenv("DCF_ALLOW_DIRECT_FETCH", "1")
    assert allow_direct_fetch() is True
    monkeypatch.setenv("DCF_ALLOW_DIRECT_FETCH", "0")
    assert allow_direct_fetch() is False


def test_require_direct_fetch_names_the_missing_served_source():
    with pytest.raises(ProviderError, match="DIRECT_FETCH_DISABLED") as exc:
        require_direct_fetch("The widget loader", "a served widget source")
    assert "a served widget source" in str(exc.value)


def test_require_direct_fetch_warns_loudly_when_flag_on(monkeypatch, caplog):
    monkeypatch.setenv("DCF_ALLOW_DIRECT_FETCH", "1")
    with caplog.at_level(logging.WARNING, logger="dcf.direct_fetch"):
        require_direct_fetch("The widget loader", "a served widget source")
    assert "DCF_ALLOW_DIRECT_FETCH=1" in caplog.text
    assert "DIRECT" in caplog.text


@pytest.mark.parametrize("url", [YAHOO_URL, SEC_URL, "https://www.sec.gov/files/company_tickers.json"])
def test_transport_guard_blocks_direct_hosts(url):
    with pytest.raises(ProviderError, match="DIRECT_FETCH_DISABLED"):
        direct_fetch_guard(url)


def test_transport_guard_ignores_served_and_configured_hosts():
    direct_fetch_guard("https://zion.internal/private/v1/financial-history")
    direct_fetch_guard("https://example.com/v1/company/TEST")


def test_transport_guard_warns_and_allows_with_flag(monkeypatch, caplog):
    monkeypatch.setenv("DCF_ALLOW_DIRECT_FETCH", "1")
    with caplog.at_level(logging.WARNING, logger="dcf.direct_fetch"):
        direct_fetch_guard(YAHOO_URL)
    assert "DIRECT" in caplog.text


def test_jsonhttp_get_blocks_direct_url_before_any_session_use():
    class ExplodingSession:
        def get(self, *args, **kwargs):
            raise AssertionError("session must not be touched for a direct URL")

    http = JsonHTTP(session=ExplodingSession())
    with pytest.raises(ProviderError, match="DIRECT_FETCH_DISABLED"):
        http.get(YAHOO_URL)


def test_yahoo_provider_fails_closed_without_flag():
    from test_yahoo_provider import MockHTTP
    from yahoo_provider import load_company_metrics, load_yahoo

    with pytest.raises(ProviderError, match="DIRECT_FETCH_DISABLED"):
        load_yahoo("TEST", TODAY, MockHTTP())
    with pytest.raises(ProviderError, match="DIRECT_FETCH_DISABLED"):
        load_company_metrics("TEST", TODAY, MockHTTP())


def test_direct_sec_mode_fails_closed_without_flag():
    from dcf_loader import load_sec

    with pytest.raises(ProviderError, match="DIRECT_FETCH_DISABLED"):
        load_sec("TEST", TODAY, JsonHTTP())


def test_guidance_fails_closed_without_flag():
    from guidance import load_guidance

    with pytest.raises(ProviderError, match="DIRECT_FETCH_DISABLED"):
        load_guidance("TEST")


def test_analyst_scrape_fails_closed_without_flag(monkeypatch):
    import decision_support

    class HTTP:
        def __init__(self, **kwargs):
            self.store = self

        def get(self, key, **kwargs):
            return None

        def set(self, key, value, ttl):
            raise AssertionError("nothing may be cached for a blocked fetch")

    monkeypatch.setattr(decision_support, "JsonHTTP", HTTP)
    with pytest.raises(ProviderError, match="DIRECT_FETCH_DISABLED"):
        decision_support.load_analysts("TEST")


def test_adjustment_facts_report_unavailable_instead_of_fetching():
    from accounting_policy import fetch_adjustment_facts

    class ExplodingHTTP:
        def get(self, *args, **kwargs):
            raise AssertionError("no companyconcept fetch may happen")

    result = fetch_adjustment_facts(
        "0000000001", ["2025-12-31"], ExplodingHTTP(), as_of=TODAY, include_ebit=True
    )
    assert result["facts"] == {"intangible_impairment": [], "goodwill_impairment": []}
    assert any(
        "DIRECT_FETCH_DISABLED" in entry["reason"] for entry in result["unavailable"]
    )


def test_starter_peers_never_fetch_recommendations():
    from auto_loading import starter_peers

    class ExplodingHTTP:
        def get(self, *args, **kwargs):
            raise AssertionError("no Yahoo recommendation fetch may happen")

    label, symbols = starter_peers("ZZZZ", ExplodingHTTP())
    assert symbols == ["MSFT", "IBM", "WMT", "JNJ"]
    assert "Yahoo" not in label


def test_classification_stays_unconfirmed_without_flag():
    from auto_loading import company_classification

    class ExplodingHTTP:
        def get(self, *args, **kwargs):
            raise AssertionError("no SEC directory fetch may happen")

    assert company_classification("ZZZZ", ExplodingHTTP()) is None


def test_auto_load_fails_closed_on_missing_served_risk_free_rate(monkeypatch):
    """The headline behavior: packet statements load, then the load stops.

    Price and beta have served sources (faked here); the risk-free rate does
    not, so a DCF auto load must surface SERVED_RISK_FREE_RATE_NOT_CONFIGURED
    instead of pulling a Treasury yield from Yahoo.
    """
    import auto_loading
    import ppe_provider
    import served_market
    from test_sec_first import full_packet

    packet = full_packet()
    monkeypatch.setattr(ppe_provider, "load_packet", lambda *a, **k: packet)
    monkeypatch.setattr(
        served_market,
        "latest_price",
        lambda symbol, asof, **kwargs: {
            "ticker": symbol,
            "price": 50.0,
            "price_as_of": asof,
            "provenance": {"provider": "fixture", "release": "r", "permno": 1, "basis": "raw"},
        },
    )
    monkeypatch.setattr(served_market, "served_beta", lambda symbol, asof, **kwargs: (1.0, 150))
    # risk_free_rate is deliberately NOT faked: the real one fails closed.
    with pytest.raises(ProviderError, match="SERVED_RISK_FREE_RATE_NOT_CONFIGURED"):
        auto_loading.load_method("dcf", "TEST", TODAY, http=JsonHTTP())


def test_auto_load_without_packet_fails_closed(monkeypatch):
    import auto_loading
    import ppe_provider

    monkeypatch.setattr(ppe_provider, "load_packet", lambda *a, **k: None)
    with pytest.raises(ProviderError, match="DIRECT_FETCH_DISABLED"):
        auto_loading.load_method("dcf", "TEST", TODAY, http=JsonHTTP())
