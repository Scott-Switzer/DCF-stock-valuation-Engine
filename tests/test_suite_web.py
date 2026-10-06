import json
import pytest
from app import app
from suite_models import suite_sample
from suite_views import suite_form


@pytest.fixture
def client(tmp_path):
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))
    return app.test_client()


@pytest.mark.parametrize("method", ["ddm", "relative"])
def test_method_pages_calculation_exports_and_import_preserve_values(client, method):
    assert client.get("/" + method).status_code == 200
    form = suite_form(method)
    result = client.post("/" + method, data=form)
    assert result.status_code == 200
    assert b"Synthetic example" in result.data
    a = (
        {"dividend_growth_rates": [0.05] * 5, "required_return": 0.07, "terminal_growth_rate": 0.02}
        if method == "ddm"
        else {"included_methods": ["ev_revenue", "ev_ebitda", "pe"]}
    )
    payload = {"financials": suite_sample(method), "assumptions": a}
    calculated = client.post("/api/calculate/" + method, json=payload)
    assert calculated.status_code == 200
    exported = client.post(
        "/export/" + method + "/json", data={"suite_payload": json.dumps(payload)}
    )
    assert exported.status_code == 200
    full = exported.get_json()
    assert full["result"]["target_price_12m"] == calculated.get_json()["target_price_12m"]
    csv = client.post("/export/" + method + "/csv", json=payload)
    assert csv.status_code == 200
    assert b"12-month target" in csv.data
    imported = client.post("/api/import/" + method, json=full)
    assert imported.status_code == 200
    replay = client.post("/" + method, data=imported.get_json()["form"])
    assert replay.status_code == 200


@pytest.mark.parametrize("method", ["ddm", "relative"])
def test_blank_model_and_invalid_structures(client, method):
    blank = client.get("/api/sample/" + method + "?blank=1").get_json()
    assert blank["financials"]["source"]["kind"] == "manual"
    assert blank["financials"]["market"]["price"] is None
    assert (
        client.post(
            "/api/calculate/" + method, json={"financials": {}, "assumptions": {}}
        ).status_code
        == 400
    )
    bad = suite_form(method)
    bad["base_document"] = '{"schema_version":"' + method + '-financials-v1","company":[]}'
    assert client.post("/" + method, data=bad).status_code == 400


def test_ddm_preserves_inputs_after_invalid_terminal_growth(client):
    form = suite_form("ddm")
    form["terminal_growth"] = "9"
    form["company_name"] = "Keep me"
    r = client.post("/ddm", data=form)
    assert r.status_code == 400
    assert b"Keep me" in r.data
    assert b"below the required return" in r.data


def test_relative_rejects_duplicate_peers_and_self_comparisons(client):
    form = suite_form("relative")
    form["peer_ticker_0"] = "DEMO"
    r = client.post("/relative", data=form)
    assert r.status_code == 400
    assert b"own peer average" in r.data


@pytest.mark.parametrize("method", ["ddm", "relative"])
def test_dcf_handoff_carries_forecast_without_inventing_dividends_or_peers(client, method):
    from dcf_loader import demo_document

    payload = {
        "financials": demo_document(),
        "assumptions": {
            "revenue_growth_rates": [0.05] * 5,
            "terminal_growth_rate": 0.02,
            "wacc_override": 0.065,
        },
    }
    r = client.post("/api/from-dcf/" + method, json=payload)
    assert r.status_code == 200
    form = r.get_json()["form"]
    assert form["ticker"] == "DEMO"
    assert form["eligible"] == ""
    if method == "ddm":
        assert form["base_common_dividends"] is None
    else:
        assert form["forward_revenue"] == 1050
        assert form["forward_ebitda"] == 241.5
        assert form["peer_ticker_0"] == ""
