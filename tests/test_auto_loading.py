from datetime import datetime, timezone
import pytest
from app import app, form_payload, evaluate
from suite_views import suite_form_payload, suite_evaluate
from werkzeug.datastructures import MultiDict
from test_yahoo_provider import MockHTTP
import auto_loading


@pytest.fixture
def client(tmp_path, monkeypatch):
    class HTTP(MockHTTP):
        def get(self, url, **kwargs):
            raw = super().get(url, **kwargs)
            if "/timeseries/" in url:
                symbol = url.rsplit("/", 1)[-1]
                for row in raw["timeseries"]["result"]:
                    row["meta"]["symbol"] = [symbol]
            return raw

    monkeypatch.setattr(auto_loading, "JsonHTTP", lambda **kwargs: HTTP())
    monkeypatch.setattr(
        auto_loading, "starter_peers", lambda ticker, http: ("Fixture peer set", ["CMPA", "CMPB"])
    )
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))
    return app.test_client()


@pytest.mark.parametrize("method", ["dcf", "ddm", "relative"])
def test_ticker_load_fills_every_required_input_and_calculates(client, method):
    r = client.post(
        "/api/load/" + method,
        json={"ticker": "TEST", "valuation_date": datetime.now(timezone.utc).date().isoformat()},
    )
    assert r.status_code == 200, r.get_json()
    payload = r.get_json()
    f = MultiDict({k: str(v) if v is not None else "" for k, v in payload["form"].items()})
    d, a = form_payload(f) if method == "dcf" else suite_form_payload(method, f)
    v = evaluate(d, a) if method == "dcf" else suite_evaluate(method, d, a)
    assert v["target_price_12m"] > 0
    assert d["source"]["kind"] == "api"
    assert not v["metadata"]["is_demo"]
    if method == "dcf":
        assert payload["form"]["wacc"] == payload["load_summary"]["capital_costs"]["wacc"] * 100
    elif method == "ddm":
        assert d["base_common_dividends"] == 30
        assert payload["form"]["required_return"] == pytest.approx(9)
    else:
        assert len(d["comparables"]) == 2
        assert d["target"]["historical"]["book_value"] == 400
        assert d["target"]["forward"]["book_value"] == 420
        assert all(p["available_at"] == d["valuation_date"] for p in d["comparables"])


def test_premium_assumptions_recompute_loaded_wacc(client):
    low = client.post(
        "/api/load/dcf", json={"ticker": "TEST", "equity_risk_premium": 0.04}
    ).get_json()
    high = client.post(
        "/api/load/dcf", json={"ticker": "TEST", "equity_risk_premium": 0.07}
    ).get_json()
    assert low["form"]["wacc"] < high["form"]["wacc"]
    assert high["financials"]["source"]["capital_costs"]["equity_risk_premium"] == 0.07


def test_provider_failure_keeps_existing_work_and_returns_specific_error(client, monkeypatch):
    def failed(*args, **kwargs):
        raise auto_loading.ProviderError("Missing required financial observation.")

    monkeypatch.setattr(auto_loading, "load_yahoo", failed)
    r = client.post("/api/load/dcf", json={"ticker": "TEST"})
    assert r.status_code == 503
    assert r.get_json()["error"] == "Missing required financial observation."


def test_default_pages_are_live_blank_not_sample(client):
    for path in ["/", "/ddm", "/relative"]:
        r = client.get(path)
        assert r.status_code == 200
        assert b"Example Operating Company" not in r.data
        assert b"Load company" in r.data


def test_relative_partial_peer_coverage_is_disclosed(client, monkeypatch):
    real = auto_loading.load_company_metrics

    def load(ticker, *args, **kwargs):
        if ticker == "CMPA":
            raise auto_loading.ProviderError("Missing metric")
        return real(ticker, *args, **kwargs)

    monkeypatch.setattr(auto_loading, "load_company_metrics", load)
    r = client.post("/api/load/relative", json={"ticker": "TEST"})
    assert r.status_code == 200
    assert len(r.get_json()["financials"]["comparables"]) == 1
    assert any("Peer CMPA unavailable" in w for w in r.get_json()["warnings"])


def test_historical_yahoo_snapshot_is_rejected(client):
    r = client.post("/api/load/dcf", json={"ticker": "TEST", "valuation_date": "2020-01-01"})
    assert r.status_code == 503
    assert "historical point-in-time" in r.get_json()["error"]


@pytest.mark.parametrize("method", ["ddm", "relative"])
def test_loaded_financials_cannot_be_relabelled_as_another_ticker(client, method):
    loaded = client.post("/api/load/" + method, json={"ticker": "TEST"}).get_json()
    form = loaded["form"]
    form["ticker"] = "AAPL"
    r = client.post("/" + method, data=form)
    assert r.status_code == 400
    assert b"Load data for the new ticker" in r.data


@pytest.mark.parametrize("metric,value", [("capex", 500), ("net_income", -10)])
def test_rv_loading_does_not_require_valid_dcf_terminal_value_or_positive_earnings(
    client, monkeypatch, metric, value
):
    real = auto_loading.load_yahoo

    def load(*args, **kwargs):
        d = real(*args, **kwargs)
        for h in d["historical"]:
            h[metric] = value
        return d

    monkeypatch.setattr(auto_loading, "load_yahoo", load)
    r = client.post("/api/load/relative", json={"ticker": "TEST"})
    assert r.status_code == 200, r.get_json()
    if metric == "net_income":
        assert r.get_json()["form"]["include_pe"] == ""
    assert r.get_json()["form"]["include_ev_revenue"] == "yes"


def test_percentage_roundtrip_keeps_source_provenance(client):
    loaded = client.post("/api/load/dcf", json={"ticker": "TEST"}).get_json()
    import json

    doc = loaded["financials"]
    doc["historical"][1]["tax_rate"] = 0.24091185164189982
    from app import default_form

    form = default_form(doc)
    form["mode"] = "auto"
    form["financial_document"] = json.dumps(doc)
    rebuilt, _ = form_payload(MultiDict({k: str(v) for k, v in form.items()}))
    assert not any("tax_rate" in v for v in rebuilt["source"]["manual_overrides"])
    assert rebuilt["historical"][1]["provenance"] == doc["historical"][1]["provenance"]


def test_blank_ticker_can_load_offline_example(client):
    r = client.post("/api/financials", json={"provider": "sample", "ticker": ""})
    assert r.status_code == 200
    assert r.get_json()["financials"]["source"]["kind"] == "synthetic"


@pytest.mark.parametrize(
    "method,scenario",
    [("relative", "short_returns"), ("relative", "preferred_equity"), ("ddm", "preferred_equity")],
)
def test_loading_only_requires_method_capital_costs(client, monkeypatch, method, scenario):
    http = auto_loading.JsonHTTP()
    if scenario == "preferred_equity":
        for metric in http.financials["timeseries"]["result"]:
            for key, rows in metric.items():
                if key in {"annualStockholdersEquity", "annualTotalEquityGrossMinorityInterest"}:
                    for row in rows:
                        row["reportedValue"]["raw"] = 440
                elif key == "annualTotalAssets":
                    for row in rows:
                        row["reportedValue"]["raw"] = 740
    real_get = http.get

    def get(url, **kwargs):
        data = real_get(url, **kwargs)
        if scenario == "short_returns" and "/chart/" in url:
            chart = data["chart"]["result"][0]
            chart["timestamp"] = chart["timestamp"][:2]
            chart["indicators"]["adjclose"][0]["adjclose"] = chart["indicators"]["adjclose"][0][
                "adjclose"
            ][:2]
        return data

    http.get = get
    monkeypatch.setattr(auto_loading, "JsonHTTP", lambda **kwargs: http)
    r = client.post("/api/load/" + method, json={"ticker": "TEST"})
    assert r.status_code == 200, r.get_json()
    if method == "relative":
        assert r.get_json()["load_summary"]["capital_costs"] == {}
        if scenario == "preferred_equity":
            assert r.get_json()["financials"]["bridge"]["preferred_equity"] == 40
    else:
        costs = r.get_json()["load_summary"]["capital_costs"]
        assert costs["cost_of_equity"] > 0
        assert costs["wacc"] is None
        assert costs["preferred_equity"] == 40


def test_workspace_relative_uses_current_dcf_year_one_assumptions(client):
    from app import form_payload

    loaded = client.post("/api/load/dcf", json={"ticker": "TEST"}).get_json()
    form = loaded["form"]
    form["growth_0"] = 17
    doc, assumptions = form_payload(
        MultiDict({k: str(v) if v is not None else "" for k, v in form.items()})
    )
    from dataclasses import asdict

    response = client.post(
        "/api/assemble/relative", json={"financials": doc, "assumptions": asdict(assumptions)}
    )
    assert response.status_code == 200, response.get_json()
    assert response.get_json()["financials"]["target"]["forward"]["revenue"] == pytest.approx(
        doc["historical"][-1]["revenue"] * 1.17
    )


def test_workspace_keeps_four_candidates_when_all_peer_snapshots_fail(client, monkeypatch):
    loaded = client.post("/api/load/dcf", json={"ticker": "TEST"}).get_json()
    monkeypatch.setattr(
        auto_loading,
        "starter_peers",
        lambda *args: ("Unverified candidates", ["AAPL", "MSFT", "WMT", "JNJ"]),
    )

    def missing(*args, **kwargs):
        raise auto_loading.ProviderError("Missing required peer financials")

    monkeypatch.setattr(auto_loading, "load_company_metrics", missing)
    response = client.post("/api/assemble/relative", json={"financials": loaded["financials"]})
    assert response.status_code == 200, response.get_json()
    result = response.get_json()
    assert len(result["financials"]["source"]["peer_suggestions"]) == 4
    assert result["financials"]["comparables"] == []
    assert all(not x["available"] for x in result["financials"]["source"]["peer_suggestions"])


def test_relative_multiples_use_diluted_equity_without_reusing_wacc_weights():
    from dcf_loader import demo_document
    from auto_loading import relative_metrics

    doc = demo_document()
    doc["source"]["common_book_equity"] = {"value": 500}
    doc["source"]["capital_costs"] = {"market_equity_value": 5000}
    actual = relative_metrics(doc)
    assert actual["pe"] == pytest.approx(
        doc["market"]["price"]
        * doc["market"]["diluted_shares"]
        / doc["historical"][-1]["net_income"]
    )
