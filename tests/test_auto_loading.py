from datetime import datetime, timezone
import json
import pytest
from app import app, form_payload, evaluate
from suite_views import suite_form_payload, suite_evaluate
from werkzeug.datastructures import MultiDict
from test_yahoo_provider import MockHTTP
import auto_loading
import decision_support
from decision_support import peer_review_status as real_peer_review_status


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
    # Served-data fixtures: the automatic load now takes statements only
    # from a published packet and market inputs only from the serving
    # layer. The packet mirrors the retired Yahoo fixture's statement
    # values (common dividends raised to 30 for the DDM expectation), and
    # the served market fakes mirror the old chart fixture (price 50,
    # beta 1.0, risk-free rate 4 percent).
    import ppe_provider
    import served_market
    from ppe_packets import build_packet
    from test_sec_first import full_facts, observation

    def packet_for(ticker, asof):
        facts = full_facts()
        for row in facts["facts"]["us-gaap"]["PaymentsOfDividendsCommonStock"]["units"]["USD"]:
            row["val"] = 30
        rows = [observation("revenue", 1000 + i * 100, i) for i in range(3)]
        return build_packet(ticker, "0000000001", rows, facts, asof, {})

    monkeypatch.setattr(
        ppe_provider,
        "load_packet",
        lambda ticker, asof=None, **kwargs: packet_for(
            ticker, asof or datetime.now(timezone.utc).date().isoformat()
        ),
    )
    monkeypatch.setattr(
        served_market,
        "latest_price",
        lambda symbol, asof, **kwargs: {
            "ticker": symbol,
            "price": 50.0,
            "price_as_of": asof,
            "provenance": {
                "provider": "Zion serving layer price history (CRSP)",
                "release": "fixture-release",
                "permno": 1,
                "basis": "raw_observed_price",
            },
        },
    )
    monkeypatch.setattr(served_market, "served_beta", lambda symbol, asof, **kwargs: (1.0, 150))
    monkeypatch.setattr(
        served_market, "risk_free_rate", lambda asof: {"rate": 0.04, "as_of": asof}
    )
    # Fixture peers are treated as reviewed so these tests exercise method selection.
    # Unverified peers are covered by test_loaded_candidate_peers_are_not_preselected.
    monkeypatch.setattr(decision_support, "peer_review_status", lambda fit: "reviewed")
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
    # The wire bundle carries financials once; the browser rebuilds
    # form.base_document from financials before any form submission.
    assert "base_document" not in payload["form"]
    payload["form"]["base_document"] = json.dumps(payload["financials"])
    assert json.loads(payload["form"]["base_document"]) == payload["financials"]
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
    import sec_first

    def failed(*args, **kwargs):
        raise auto_loading.ProviderError("Missing required financial observation.")

    monkeypatch.setattr(sec_first, "load_sec_first", failed)
    r = client.post("/api/load/dcf", json={"ticker": "TEST"})
    assert r.status_code == 503
    assert r.get_json()["error"] == "Missing required financial observation."


def test_financial_firm_statement_failure_names_suitability(client, monkeypatch):
    import sec_first

    def failed(*args, **kwargs):
        raise auto_loading.ProviderError(
            "Served packet missing OperatingIncome for 2023-12-31; cannot complete financials."
        )

    monkeypatch.setattr(sec_first, "load_sec_first", failed)
    # MRX is a registry-confirmed financial firm (SEC SIC 6200): no network needed.
    r = client.post("/api/load/dcf", json={"ticker": "MRX"})
    assert r.status_code == 503
    error = r.get_json()["error"]
    assert "financial firm" in error
    assert "Served packet missing OperatingIncome" in error


def test_nonfinancial_statement_failure_keeps_original_error(client, monkeypatch):
    import sec_first

    def failed(*args, **kwargs):
        raise auto_loading.ProviderError(
            "Served packet missing OperatingIncome for 2023-12-31; cannot complete financials."
        )

    monkeypatch.setattr(sec_first, "load_sec_first", failed)
    monkeypatch.setattr(auto_loading, "company_classification", lambda ticker, http: None)
    r = client.post("/api/load/dcf", json={"ticker": "TEST"})
    assert r.status_code == 503
    assert r.get_json()["error"].startswith("Served packet missing OperatingIncome")
    assert "financial firm" not in r.get_json()["error"]


def test_default_pages_are_live_blank_not_sample(client):
    for path in ["/", "/ddm", "/relative"]:
        r = client.get(path)
        assert r.status_code == 200
        assert b"Example Operating Company" not in r.data
        assert b"Load company" in r.data


def test_relative_partial_peer_coverage_is_disclosed(client, monkeypatch):
    real = auto_loading.load_peer_document

    def load(ticker, *args, **kwargs):
        if ticker == "CMPA":
            raise auto_loading.ProviderError("Missing metric")
        return real(ticker, *args, **kwargs)

    monkeypatch.setattr(auto_loading, "load_peer_document", load)
    r = client.post("/api/load/relative", json={"ticker": "TEST"})
    assert r.status_code == 200
    assert len(r.get_json()["financials"]["comparables"]) == 1
    assert any("Peer CMPA unavailable" in w for w in r.get_json()["warnings"])


def test_historical_snapshot_is_rejected(client):
    r = client.post("/api/load/dcf", json={"ticker": "TEST", "valuation_date": "2020-01-01"})
    assert r.status_code == 503
    assert "DIRECT_FETCH_DISABLED" in r.get_json()["error"]


@pytest.mark.parametrize("method", ["ddm", "relative"])
def test_loaded_financials_cannot_be_relabelled_as_another_ticker(client, method):
    loaded = client.post("/api/load/" + method, json={"ticker": "TEST"}).get_json()
    form = loaded["form"]
    form["base_document"] = json.dumps(loaded["financials"])
    form["ticker"] = "AAPL"
    r = client.post("/" + method, data=form)
    assert r.status_code == 400
    assert b"Load data for the new ticker" in r.data


def _serve_test_packet_with(monkeypatch, mutator):
    """Rebuild the TEST packet with one statement input changed.

    Peers keep the fixture packet; only the target's served statements move,
    mirroring the retired Yahoo-fixture mutation these tests used before.
    """
    import ppe_provider
    from ppe_packets import build_packet
    from test_sec_first import full_facts, observation

    previous = ppe_provider.load_packet

    def load_packet(ticker, asof=None, **kwargs):
        if ticker != "TEST":
            return previous(ticker, asof, **kwargs)
        facts = full_facts()
        mutator(facts["facts"]["us-gaap"])
        for row in facts["facts"]["us-gaap"]["PaymentsOfDividendsCommonStock"]["units"]["USD"]:
            row["val"] = 30
        rows = [observation("revenue", 1000 + i * 100, i) for i in range(3)]
        return build_packet(ticker, "0000000001", rows, facts, asof, {})

    monkeypatch.setattr(ppe_provider, "load_packet", load_packet)


@pytest.mark.parametrize("metric,value", [("capex", 500), ("net_income", -10)])
def test_rv_loading_does_not_require_valid_dcf_terminal_value_or_positive_earnings(
    client, monkeypatch, metric, value
):
    def mutate(tags):
        if metric == "capex":
            for row in tags["PaymentsToAcquirePropertyPlantAndEquipment"]["units"]["USD"]:
                row["val"] = value
        else:
            for tag in (
                "NetIncomeLoss",
                "NetIncomeLossAvailableToCommonStockholdersBasic",
            ):
                for row in tags[tag]["units"]["USD"]:
                    row["val"] = value

    _serve_test_packet_with(monkeypatch, mutate)
    r = client.post("/api/load/relative", json={"ticker": "TEST"})
    assert r.status_code == 200, r.get_json()
    if metric == "net_income":
        assert r.get_json()["form"]["include_pe"] == ""
    assert r.get_json()["form"]["include_ev_revenue"] == "yes"


def test_loaded_candidate_peers_are_not_preselected(client, monkeypatch):
    # Restore the real fit classification, undoing the fixture's reviewed override.
    monkeypatch.setattr(decision_support, "peer_review_status", real_peer_review_status)
    r = client.post("/api/load/relative", json={"ticker": "TEST"})
    assert r.status_code == 200, r.get_json()
    payload = r.get_json()
    statuses = {p["ticker"]: p["review_status"] for p in payload["financials"]["comparables"]}
    assert statuses and set(statuses.values()) == {"candidate"}
    form = payload["form"]
    assert all(form.get(f"include_{k}") in ("", None) for k in ["ev_revenue", "ev_ebitda", "pe"])


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
    if scenario == "preferred_equity":
        def mutate(tags):
            for row in tags["PreferredStockValue"]["units"]["USD"]:
                row["val"] = 40

        _serve_test_packet_with(monkeypatch, mutate)
    if scenario == "short_returns":
        # Beta inputs are unusable (too little served history); a relative
        # load must not care, because it never requests capital costs.
        import served_market

        def no_beta(symbol, asof, **kwargs):
            raise auto_loading.ProviderError(
                "Served market data: beta requires at least 104 aligned weekly total returns."
            )

        monkeypatch.setattr(served_market, "served_beta", no_beta)
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
    form["base_document"] = json.dumps(loaded["financials"])
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

    monkeypatch.setattr(auto_loading, "load_peer_document", missing)
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


def test_wire_bundle_dedups_base_document_but_manual_form_keeps_it(client):
    from app import default_form

    for method in ("dcf", "ddm", "relative"):
        payload = client.post("/api/load/" + method, json={"ticker": "TEST"}).get_json()
        # One wire copy: financials travel as structured data, not twice.
        assert "base_document" not in payload["form"]
        assert payload["financials"]["company"]["ticker"] == "TEST"
        # Browser-side reconstruction is exactly the delivered snapshot.
        assert json.loads(json.dumps(payload["financials"])) == payload["financials"]
    # Manual/classic flows still render the field server-side.
    from dcf_loader import demo_document

    assert json.loads(default_form(demo_document())["base_document"])["schema_version"] == (
        "dcf-financials-v1"
    )


def test_bundled_preview_matches_preview_api_path(client):
    from app import evaluate, form_payload

    loaded = client.post("/api/load/dcf", json={"ticker": "TEST"}).get_json()
    preview = loaded.get("preview")
    assert preview, "dcf bundle carries the baseline preview"
    # No second copy of the snapshot inside the preview.
    assert "input_financials" not in preview
    # Same numbers the iframe preview would compute from the submitted form.
    form = dict(loaded["form"])
    form["base_document"] = json.dumps(loaded["financials"])
    doc, assumptions = form_payload(
        MultiDict({k: str(v) if v is not None else "" for k, v in form.items()})
    )
    expected = evaluate(doc, assumptions)
    assert preview["intrinsic_value"] == expected["intrinsic_value"]
    assert preview["target_price_12m"] == expected["target_price_12m"]
    assert preview["upside_12m"] == expected["upside_12m"]


@pytest.mark.parametrize("method", ["ddm", "relative"])
def test_suite_bundles_have_no_dcf_preview(client, method):
    loaded = client.post("/api/load/" + method, json={"ticker": "TEST"}).get_json()
    assert "preview" not in loaded


def test_assemble_wire_bundle_dedups_base_document(client):
    loaded = client.post("/api/load/dcf", json={"ticker": "TEST"}).get_json()
    for method in ("ddm", "relative"):
        response = client.post(
            "/api/assemble/" + method, json={"financials": loaded["financials"]}
        )
        assert response.status_code == 200, response.get_json()
        bundle = response.get_json()
        assert "base_document" not in bundle["form"]
        assert json.loads(json.dumps(bundle["financials"])) == bundle["financials"]


def test_automatic_relative_evaluation_uses_only_reviewed_peers(client, monkeypatch):
    import suite_views

    statuses = iter(["reviewed", "excluded"])
    monkeypatch.setattr(decision_support, "peer_review_status", lambda fit: next(statuses))
    original = suite_views.suite_evaluate
    evaluated = []
    def capture(method, doc, assumptions):
        evaluated.extend(p["review_status"] for p in doc["comparables"])
        return original(method, doc, assumptions)
    monkeypatch.setattr(suite_views, "suite_evaluate", capture)
    response = client.post("/api/load/relative", json={"ticker": "TEST"})
    assert response.status_code == 200
    assert evaluated == ["reviewed"]
    assert len(response.get_json()["financials"]["comparables"]) == 2
