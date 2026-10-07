import json
import pytest
from dcf_loader import ProviderError
from decision_support import historical_growth, parse_analysts, peer_fit


def page(packet):
    return (
        '<script type="application/json">'
        + json.dumps({"body": json.dumps({"quoteSummary": {"result": [packet]}})})
        + "</script>"
    )


def test_historical_growth_does_not_invent_zero_baseline():
    rows = [
        {"period_end": "2023-12-31", "revenue": 100},
        {"period_end": "2024-12-31", "revenue": 120},
        {"period_end": "2025-12-31", "revenue": 150},
    ]
    result = historical_growth(rows, "revenue")
    assert result["annual"][1]["growth"] == pytest.approx(0.2)
    assert result["cagr"] == pytest.approx(1.5**0.5 - 1)
    rows[0]["revenue"] = 0
    assert historical_growth(rows, "revenue")["annual"][1]["growth"] is None
    assert historical_growth(rows, "revenue")["cagr"] is None


def test_analyst_growth_is_revenue_not_eps_and_currency_verified():
    packet = {
        "price": {"symbol": "TEST", "currency": "USD"},
        "financialData": {
            "financialCurrency": "USD",
            "targetMeanPrice": {"raw": 140},
            "numberOfAnalystOpinions": {"raw": 20},
        },
        "earningsTrend": {
            "trend": [
                {
                    "period": "+1y",
                    "endDate": "2027-12-31",
                    "growth": {"raw": 0.99},
                    "revenueEstimate": {
                        "revenueCurrency": "USD",
                        "growth": {"raw": 0.12},
                        "avg": {"raw": 112},
                        "yearAgoRevenue": {"raw": 100},
                        "numberOfAnalysts": {"raw": 8},
                    },
                }
            ]
        },
    }
    result = parse_analysts(page(packet), "TEST")
    assert result["revenue"][0]["growth"] == 0.12
    assert result["target"]["mean"] == 140
    packet["price"]["symbol"] = "OTHER"
    with pytest.raises(ProviderError):
        parse_analysts(page(packet), "TEST")
    packet["price"]["symbol"] = "TEST"
    packet["price"]["currency"] = "EUR"
    with pytest.raises(ProviderError):
        parse_analysts(page(packet), "TEST")


def test_peer_fit_discloses_size_mismatch_and_unknown_business_fit():
    fit = peer_fit("AAPL", "DELL", 3e12, 1e11)
    assert fit["market_cap_ratio"] == pytest.approx(1 / 30)
    assert "size" in " ".join(fit["caveats"]).lower()
    assert fit["segments"]
    assert peer_fit("TEST", "OTHER", 100, 100)["fit_label"] == "Business fit unverified"


def test_references_cache_preserves_observation_time_and_is_compact(monkeypatch):
    import decision_support

    calls = []
    cache = {}
    packet = {
        "price": {"symbol": "TEST", "currency": "USD", "marketCap": {"raw": 1000}},
        "financialData": {"targetMeanPrice": {"raw": 140}},
    }

    class HTTP:
        def __init__(self, **kwargs):
            self.store = self

        def get(self, key, **kwargs):
            if not kwargs:
                return cache.get(key)
            calls.append(key)
            return page(packet)

        def set(self, key, value, ttl):
            cache[key] = value

    monkeypatch.setattr(decision_support, "JsonHTTP", HTTP)
    first = decision_support.load_analysts("TEST")
    second = decision_support.load_analysts("TEST")
    assert len(calls) == 1
    assert first["retrieved_at"] == second["retrieved_at"]
    assert first["market_cap"] == 1000
    assert len(json.dumps(cache)) < 2000


def test_reference_failure_is_negative_cached_without_blocking_model(monkeypatch):
    import decision_support

    cache = {}
    calls = []

    class HTTP:
        def __init__(self, **kwargs):
            self.store = self

        def get(self, key, **kwargs):
            if not kwargs:
                return cache.get(key)
            calls.append(key)
            raise ProviderError("Provider unavailable")

        def set(self, key, value, ttl):
            cache[key] = value
            assert ttl == 300

    monkeypatch.setattr(decision_support, "JsonHTTP", HTTP)
    for _ in range(2):
        with pytest.raises(ProviderError):
            decision_support.load_analysts("TEST")
    assert len(calls) == 1


def test_forms_remove_collection_banner_keep_privacy_and_explicit_unlock():
    from app import app

    with app.test_client() as client:
        for route in ["/?embedded=1", "/ddm?embedded=1", "/relative?embedded=1"]:
            response = client.get(route)
            html = response.get_data(as_text=True)
            assert response.status_code == 200
            assert "Calculating saves" not in html
            assert 'id="edit-sourced"' in html
            assert 'href="/privacy"' in html
            assert 'id="decision-context"' in html


def test_reference_endpoint_reports_provider_unavailability(monkeypatch):
    import decision_support
    from app import app

    monkeypatch.setattr(
        decision_support,
        "load_analysts",
        lambda ticker: (_ for _ in ()).throw(ProviderError("Unavailable")),
    )
    with app.test_client() as client:
        assert client.get("/api/references/TEST").status_code == 503


def test_nullable_modules_and_trend_entries_are_safe():
    with pytest.raises(ProviderError):
        parse_analysts(
            '<script type="application/json">{"body":"{\\"quoteSummary\\":null}"}</script>', "TEST"
        )
    packet = {
        "price": {"symbol": "TEST", "currency": "USD"},
        "earningsTrend": None,
        "financialData": {"targetMeanPrice": {"raw": 120}},
    }
    assert parse_analysts(page(packet), "TEST")["target"]["mean"] == 120
    packet["earningsTrend"] = {"trend": [None, 5, {"period": "+1y", "revenueEstimate": None}]}
    assert parse_analysts(page(packet), "TEST")["revenue"] == []


def test_four_peer_candidates_include_imperfect_fits_and_avoid_duplicate_issuer():
    from auto_loading import starter_peers

    assert starter_peers("AAPL", None)[1] == ["DELL", "HPQ", "HPE", "MSFT"]
    assert "GOOG" not in starter_peers("GOOGL", None)[1]
    assert {"MSFT", "WMT"} <= set(starter_peers("AMZN", None)[1])


def test_price_only_packet_does_not_hide_later_analyst_modules():
    price = page({"price": {"symbol": "TEST", "currency": "USD", "marketCap": {"raw": 1000}}})
    later = page(
        {
            "financialData": {"targetMeanPrice": {"raw": 140}},
            "earningsTrend": {
                "trend": [
                    {
                        "period": "+1y",
                        "endDate": "2027-12-31",
                        "revenueEstimate": {"revenueCurrency": "USD", "growth": {"raw": 0.1}},
                    }
                ]
            },
        }
    ).replace(
        '<script type="application/json">',
        '<script type="application/json" data-url="https://query1.finance.yahoo.com/v10/finance/quoteSummary/TEST">',
    )
    data = parse_analysts(price + later, "TEST")
    assert data["market_cap"] == 1000
    assert data["target"]["mean"] == 140
    assert data["revenue"][0]["growth"] == 0.1
    # A different issuer's packet cannot supply targets or revenue to TEST.
    other = later.replace("quoteSummary/TEST", "quoteSummary/OTHER")
    assert parse_analysts(price + other, "TEST")["target"]["mean"] is None


def test_goog_and_googl_have_equivalent_business_explanations():
    assert peer_fit("GOOG", "META", 100, 100) == peer_fit("GOOGL", "META", 100, 100)
    assert peer_fit("GOOG", "META", 100, 100)["shared_products_segments"] == ["advertising"]


def test_reference_rate_limit_applies_across_different_tickers(tmp_path, monkeypatch):
    from app import app
    import decision_support

    calls = []

    def load(ticker):
        calls.append(ticker)
        return {"ticker": ticker}

    monkeypatch.setattr(decision_support, "load_analysts", load)
    monkeypatch.setitem(app.config, "STATE_PATH", str(tmp_path / "limits.sqlite3"))
    with app.test_client() as client:
        for i in range(20):
            assert client.get("/api/references/T" + str(i)).status_code == 200
        blocked = client.get("/api/references/OTHER")
        assert blocked.status_code == 429
        assert len(calls) == 20
