import app as web


def test_api_calculation_rejects_invalid_numeric_inputs():
    r = web.app.test_client().post(
        "/api/calculate", json={"financials": {}, "assumptions": {"terminal_growth_rate": "NaN"}}
    )
    assert r.status_code == 400
    assert r.is_json


def test_health_endpoint_is_available_without_market_data():
    r = web.app.test_client().get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "healthy"


def test_search_supports_autocomplete_without_network():
    r = web.app.test_client().get("/api/search?q=AAPL")
    assert r.status_code == 200
    assert any(v["symbol"] == "AAPL" for v in r.get_json())
