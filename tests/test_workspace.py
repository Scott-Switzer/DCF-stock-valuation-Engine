from datetime import datetime, timezone
from unittest.mock import patch
import pytest
from app import app, default_form
from suite_views import suite_form
from suite_models import suite_sample
from dcf_loader import demo_document
from auto_loading import starter_peers


@pytest.fixture
def client(tmp_path):
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))
    return app.test_client()


@pytest.mark.parametrize("method", ["dcf", "ddm", "relative"])
def test_preview_never_saves(client, method):
    doc = demo_document() if method == "dcf" else suite_sample(method)
    form = default_form(doc) if method == "dcf" else suite_form(method, doc)
    with (
        patch("app.save_valuation", side_effect=AssertionError("preview saved")),
        patch("suite_views.save_valuation", side_effect=AssertionError("preview saved")),
    ):
        response = client.post("/api/preview/" + method, data=form)
    assert response.status_code == 200, response.get_json()
    assert "saved_record_id" not in response.get_json()


class NoRecommendations:
    def get(self, *args, **kwargs):
        return {}


@pytest.mark.parametrize("symbol", ["AAPL", "GOOG", "GOOGL", "KO", "AMZN", "ZZZZ"])
def test_always_four_distinct_peer_candidates(symbol):
    _, symbols = starter_peers(symbol, NoRecommendations())
    assert len(symbols) == len(set(symbols)) == 4
    assert symbol not in symbols
    assert not {"GOOG", "GOOGL"} <= set(symbols)


def test_method_assembly_reuses_loaded_snapshot(client):
    doc = demo_document()
    doc["valuation_date"] = datetime.now(timezone.utc).date().isoformat()
    doc["source"]["common_dividends"] = {
        "value": 30,
        "period_end": doc["historical"][-1]["period_end"],
        "historical": [],
    }
    doc["source"]["capital_costs"] = {"cost_of_equity": 0.09, "wacc": 0.08}
    with patch("auto_loading.load_yahoo", side_effect=AssertionError("company fetched twice")):
        response = client.post("/api/assemble/ddm", json={"financials": doc})
    assert response.status_code == 200, response.get_json()
    assert response.get_json()["financials"]["base_common_dividends"] == 30


def test_preview_returns_the_actual_edited_inputs(client):
    form = default_form(demo_document())
    form["growth_0"] = "17"
    response = client.post("/api/preview/dcf", data=form)
    assert response.status_code == 200
    result = response.get_json()
    assert result["assumptions"]["revenue_growth_rates"][0] == 0.17
    assert result["input_financials"]["company"]["ticker"] == form["ticker"]


def test_excluding_peer_leaves_other_peers_sourced(client):
    doc = suite_sample("relative")
    form = suite_form("relative", doc)
    form.update(peer_selection="explicit", peer_include_0="yes")
    form.update({f"peer_include_{i}": "" for i in range(1, 4)})
    response = client.post("/api/preview/relative", data=form)
    assert response.status_code == 200, response.get_json()
    assert len(response.get_json()["input_financials"]["comparables"]) == 1


def test_only_embedded_editors_allow_same_origin_framing(client):
    standard = client.get("/")
    embedded = client.get("/?embedded=1")
    assert standard.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in standard.headers["Content-Security-Policy"]
    assert embedded.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert "frame-ancestors 'self'" in embedded.headers["Content-Security-Policy"]


def test_invalid_preview_rejects_terminal_growth_without_saving(client):
    form = default_form(demo_document())
    form["terminal_growth"] = "15"
    form["wacc"] = "8"
    response = client.post("/api/preview/dcf", data=form)
    assert response.status_code == 400
    assert "lower than WACC" in response.get_json()["error"]

@pytest.mark.parametrize('method,missing', [('ddm','common_dividends'),('relative','common_book_equity')])
def test_imported_snapshot_missing_method_data_returns_clear_error(client, method, missing):
    doc = demo_document()
    doc['source'].pop(missing, None)
    response = client.post('/api/assemble/' + method, json={'financials':doc})
    assert response.status_code == 400
    assert missing in response.get_json()['error']
