import pytest
import app as web
from dcf_loader import demo_document
from storage import Store


@pytest.fixture
def client(tmp_path):
    web.app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))
    return web.app.test_client()


def payload():
    return {
        "financials": demo_document(),
        "assumptions": {
            "revenue_growth_rates": [0.05] * 5,
            "terminal_growth_rate": 0.02,
            "wacc_override": 0.065,
        },
    }


@pytest.mark.parametrize("value", [None, "", True, float("inf"), float("nan")])
def test_missing_or_nonfinite_historical_value_is_rejected(client, value):
    p = payload()
    p["financials"]["historical"][0]["capex"] = value
    r = client.post("/api/calculate", json=p)
    assert r.status_code == 400
    assert "capex" in r.get_json()["error"]


def test_export_matches_api_result_and_preserves_assumptions(client):
    p = payload()
    p["assumptions"]["future_shares"] = 200
    r = client.post("/api/calculate", json=p)
    out = client.post("/export/json", json=p)
    assert r.status_code == out.status_code == 200
    assert out.get_json()["result"]["target_price_12m"] == r.get_json()["target_price_12m"]
    assert out.get_json()["assumptions"]["future_shares"] == 200
    csv = client.post("/export/csv", json=p)
    assert csv.status_code == 200
    assert b"Synthetic" in csv.data or b"synthetic" in csv.data
    assert b"200.0" in csv.data


def test_validation_error_preserves_edited_inputs(client):
    form = web.default_form(demo_document())
    form["terminal_growth"] = 10
    form["company_name"] = "My edited example"
    r = client.post("/", data=form)
    assert r.status_code == 400
    assert b"My edited example" in r.data
    assert b"Terminal growth must be lower" in r.data


def test_raw_forwarded_headers_cannot_bypass_limits(client):
    for i in range(10):
        assert (
            client.post(
                "/api/calculate", json=payload(), headers={"X-Forwarded-For": str(i)}
            ).status_code
            == 200
        )
    r = client.post("/api/calculate", json=payload(), headers={"X-Forwarded-For": "fresh"})
    assert r.status_code == 429
    assert r.headers["Retry-After"] == "60"


def test_limits_share_atomic_state_between_process_instances(tmp_path):
    path = str(tmp_path / "shared.sqlite3")
    a = Store(path)
    b = Store(path)
    assert a.allow("same", maximum=2)
    assert b.allow("same", maximum=2)
    assert not Store(path).allow("same", maximum=2)


def test_cache_does_not_return_expired_or_nonfinite_data(tmp_path):
    s = Store(str(tmp_path / "cache.sqlite3"))
    s.set("good", {"value": 1}, 60)
    assert s.get("good") == {"value": 1}
    s.set("old", {"value": 1}, -1)
    assert s.get("old") is None
    with pytest.raises(ValueError):
        s.set("bad", {"value": float("nan")}, 60)


@pytest.mark.parametrize(
    "section,key,value",
    [
        ("market", "price", 0),
        ("market", "diluted_shares", 0),
        ("bridge", "preferred_equity", None),
        ("market", "price_as_of", "2030-01-01"),
        ("market", "currency", "EUR"),
        ("company", "eligible", False),
    ],
)
def test_invalid_market_or_bridge_stops_api(client, section, key, value):
    p = payload()
    p["financials"][section][key] = value
    assert client.post("/api/calculate", json=p).status_code == 400


def test_historical_lookahead_is_rejected(client):
    p = payload()
    p["financials"]["source"]["kind"] = "zion"
    for row in p["financials"]["historical"]:
        row["available_at"] = "2027-01-01"
    assert client.post("/api/calculate", json=p).status_code == 400


def test_ticker_changed_without_loading_its_financials_is_rejected(client):
    form = web.default_form(demo_document())
    form["ticker"] = "AAPL"
    assert client.post("/", data=form).status_code == 400


def test_script_closing_text_is_not_executable_in_saved_inputs(client):
    form = web.default_form(demo_document())
    form["company_name"] = "</script><script>alert(1)</script>"
    r = client.post("/", data=form)
    assert r.status_code == 200
    assert b"<script>alert(1)</script>" not in r.data


def test_financial_api_missing_config_is_actionable(client, monkeypatch):
    monkeypatch.delenv("ZION_API_BASE_URL", raising=False)
    r = client.post(
        "/api/financials",
        json={"provider": "zion", "ticker": "AAPL", "valuation_date": "2026-10-06"},
    )
    assert r.status_code == 503
    assert "ZION_API_BASE_URL" in r.get_json()["error"]


def test_bad_json_does_not_raise_internal_error(client):
    assert (
        client.post("/api/calculate", data="[", content_type="application/json").status_code == 400
    )


def test_changed_sample_ticker_cannot_claim_live_source(client):
    form = web.default_form(demo_document())
    form["ticker"] = "AAPL"
    form["mode"] = "sec"
    assert client.post("/", data=form).status_code == 400


def test_provider_document_requires_typed_numeric_values(client):
    p = payload()
    p["financials"]["historical"][0]["ebit"] = "200"
    assert client.post("/api/calculate", json=p).status_code == 400


def test_malformed_source_warnings_are_rejected(client):
    p = payload()
    p["financials"]["source"]["warnings"] = "Not a list"
    assert client.post("/api/calculate", json=p).status_code == 400


def test_future_bridge_date_is_rejected_for_manual_data(client):
    p = payload()
    p["financials"]["bridge"]["as_of"] = "2030-01-01"
    assert client.post("/api/calculate", json=p).status_code == 400


def test_manual_mode_cannot_hide_synthetic_origin(client):
    form = web.default_form(demo_document())
    form.update(mode="manual", ticker="AAPL")
    r = client.post("/", data=form)
    assert r.status_code == 200
    assert b"This is an offline synthetic example" in r.data


@pytest.mark.parametrize(
    "field,value",
    [
        ("terminal_mode", []),
        ("terminal_mode", {}),
        ("wacc_override", {}),
        ("revenue_growth_rates", {}),
    ],
)
def test_malformed_assumption_types_are_validation_errors(client, field, value):
    p = payload()
    p["assumptions"][field] = value
    assert client.post("/api/calculate", json=p).status_code == 400
