"""Football-field comparison uses one snapshot for every lane."""

import pytest

from app import app


@pytest.fixture(autouse=True)
def isolated_limits(tmp_path):
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))


def test_compare_form_renders():
    response = app.test_client().get("/compare")
    assert response.status_code == 200
    assert b"Football field" in response.data


def test_compare_rejects_bad_ticker():
    response = app.test_client().post("/compare", data={"ticker": "!!!---"})
    assert response.status_code == 400


def test_compare_demo_snapshot(monkeypatch):
    from dcf_loader import demo_document
    import auto_loading

    doc = demo_document()

    def fake_load(method, ticker, asof=None, **kwargs):
        from copy import deepcopy

        if method == "ddm":
            ddm = {k: deepcopy(doc[k]) for k in
                   ["valuation_date", "units", "company", "market", "source"]}
            ddm.update(
                schema_version="ddm-financials-v1",
                base_common_dividends=100.0,
                dividend_as_of="2025-12-31",
            )
            return {"financials": ddm, "form": {},
                    "warnings": [], "load_summary": {"capital_costs": {}}}
        if method == "relative":
            from suite_models import suite_sample

            rel = suite_sample("relative")
            return {"financials": rel, "form": {},
                    "warnings": [], "load_summary": {"capital_costs": {}}}
        return {"financials": deepcopy(doc), "form": {},
                "warnings": [],
                "load_summary": {"capital_costs": {"wacc": 0.065,
                                                  "cost_of_equity": 0.07},
                                 "elapsed_seconds": 0.1, "peer_count": 0}}

    monkeypatch.setattr(auto_loading, "load_method", fake_load)
    response = app.test_client().post("/compare", data={"ticker": "DEMO"})
    assert response.status_code == 200, response.data[:300]
    assert b"DCF 12-month target" in response.data
    assert b"Relative 12-month" in response.data
    assert b"Bear $" in response.data


def test_driver_impacts_and_method_notes():
    from copy import deepcopy
    from compare import driver_impacts, method_notes, baseline_dcf_assumptions
    from dcf_loader import demo_document

    doc = demo_document()
    impacts = driver_impacts(doc, baseline_dcf_assumptions(doc, 0.065))
    assert len(impacts) == 3
    assert all({"label", "delta"} <= set(i) for i in impacts)
    assert abs(impacts[0]["delta"]) >= abs(impacts[-1]["delta"])
    lanes = [
        {"method": "dcf", "label": "DCF intrinsic (today)", "value": 100.0},
        {"method": "ddm", "label": "DDM intrinsic (today)", "value": 50.0},
        {"method": "ddm", "label": "DDM", "value": None},
    ]
    notes = method_notes(doc, lanes)
    assert any("DDM sits" in n for n in notes)
    bank = deepcopy(doc)
    bank["company"]["sector"] = "Commercial Bank"
    assert any("financial" in n for n in method_notes(bank, lanes))


def _fake_loader(calls, doc):
    from copy import deepcopy

    def fake_load(method, ticker, asof=None, **kwargs):
        # Provider loads are calls without a snapshot; snapshot reuse is free.
        if kwargs.get("snapshot") is None:
            calls.append(method)
        if method == "relative":
            from suite_models import suite_sample

            return {"financials": suite_sample("relative"), "form": {},
                    "warnings": [], "load_summary": {"capital_costs": {}}}
        return {"financials": deepcopy(kwargs.get("snapshot") or doc), "form": {},
                "warnings": [],
                "load_summary": {"capital_costs": {"wacc": 0.065,
                                                  "cost_of_equity": 0.07},
                                 "elapsed_seconds": 0.1, "peer_count": 0}}

    return fake_load


def test_packet_reports_effective_custom_assumptions(monkeypatch):
    """Custom growth and WACC are echoed unchanged and reproduce the DCF lane."""
    from copy import deepcopy

    import auto_loading
    from app import assumptions_from_json, evaluate
    from dcf_loader import demo_document

    doc = demo_document()
    calls = []
    monkeypatch.setattr(auto_loading, "load_method", _fake_loader(calls, doc))
    custom = {
        "revenue_growth_rates": [0.08] * 5,
        "terminal_growth_rate": 0.025,
        "wacc_override": 0.07,
        "terminal_mode": "template",
        "ebit_margins": [0.25] * 5,
        "da_margins": [0.03] * 5,
        "capex_margins": [0.05] * 5,
        "nwc_margins": [0.01] * 5,
        "tax_rates": [0.25] * 5,
        "net_income_margins": [0.15] * 5,
        "book_value_margins": [0.5] * 5,
    }
    packet = app.test_client().post(
        "/api/compare", json={"ticker": "DEMO", "assumptions": custom}
    ).get_json()
    assumed = packet["assumptions"]
    assert packet["assumptions_source"] == "workspace"
    assert assumed["revenue_growth_rates"] == [0.08] * 5
    assert assumed["terminal_growth_rate"] == 0.025
    assert assumed["wacc_override"] == 0.07
    replay = evaluate(deepcopy(doc), assumptions_from_json(assumed))
    dcf_lane = next(l for l in packet["lanes"] if l["label"].startswith("DCF 12-month"))
    assert dcf_lane["value"] == pytest.approx(replay["target_price_12m"])


def test_packet_labels_baseline_assumptions(monkeypatch):
    import auto_loading
    from dcf_loader import demo_document

    doc = demo_document()
    monkeypatch.setattr(auto_loading, "load_method", _fake_loader([], doc))
    packet = app.test_client().post(
        "/api/compare", json={"ticker": "DEMO"}
    ).get_json()
    assert packet["assumptions_source"] == "baseline"
    assert packet["assumptions"]["revenue_growth_rates"] == [0.05] * 5


def test_compare_reuses_validated_snapshot_without_dcf_load(monkeypatch):
    import auto_loading
    from dcf_loader import demo_document

    doc = demo_document()
    calls = []
    monkeypatch.setattr(auto_loading, "load_method", _fake_loader(calls, doc))
    client = app.test_client()
    response = client.post("/api/compare", json={"ticker": "DEMO", "snapshot": doc})
    assert response.status_code == 200, response.get_json()
    assert calls == []
    packet = response.get_json()
    assert packet["source"] == doc["source"]["name"]
    assert packet["valuation_date"] == doc["valuation_date"]
    assert packet["snapshot_reused"] is True

    tampered = dict(doc, schema_version="other")
    bad = client.post("/api/compare", json={"ticker": "DEMO", "snapshot": tampered})
    assert bad.status_code == 400
    mismatch = client.post("/api/compare", json={"ticker": "AAPL", "snapshot": doc})
    assert mismatch.status_code == 400


def test_compare_form_reuses_workspace_snapshot(monkeypatch):
    """The workspace's Compare button posts its loaded snapshot to /compare."""
    import json

    import auto_loading
    from dcf_loader import demo_document

    doc = demo_document()
    calls = []
    monkeypatch.setattr(auto_loading, "load_method", _fake_loader(calls, doc))
    response = app.test_client().post(
        "/compare",
        data={"ticker": "DEMO", "base_document": json.dumps(doc)},
    )
    assert response.status_code == 200, response.data[:300]
    assert b"workspace snapshot, no reload" in response.data
    assert calls == []
    bad = app.test_client().post(
        "/compare", data={"ticker": "DEMO", "base_document": "{broken"}
    )
    assert bad.status_code == 400


def test_compare_accepts_workspace_assumptions(monkeypatch):
    import json
    from dcf_loader import demo_document
    import auto_loading

    doc = demo_document()
    seen = {}

    def fake_load(method, ticker, asof=None, **kwargs):
        from copy import deepcopy

        if "assumptions" in kwargs and kwargs["assumptions"] is not None:
            seen["forecast"] = kwargs["assumptions"]
        if method == "relative":
            from suite_models import suite_sample

            return {"financials": suite_sample("relative"), "form": {},
                    "warnings": [],
                    "load_summary": {"capital_costs": {}}}
        return {"financials": deepcopy(doc), "form": {},
                "warnings": [],
                "load_summary": {"capital_costs": {"wacc": 0.065,
                                                  "cost_of_equity": 0.07},
                                 "elapsed_seconds": 0.1, "peer_count": 0}}

    monkeypatch.setattr(auto_loading, "load_method", fake_load)
    client = app.test_client()
    assumptions = {
        "revenue_growth_rates": [0.09] * 5,
        "terminal_growth_rate": 0.03,
        "wacc_override": 0.07,
        "terminal_mode": "template",
        "ebit_margins": [0.3] * 5,
        "da_margins": [0.05] * 5,
        "capex_margins": [0.06] * 5,
        "nwc_margins": [0.02] * 5,
        "tax_rates": [0.21] * 5,
        "net_income_margins": [0.2] * 5,
        "book_value_margins": [0.5] * 5,
    }
    response = client.post(
        "/compare",
        data={"ticker": "DEMO", "assumptions": json.dumps(assumptions)},
    )
    assert response.status_code == 200, response.data[:300]
    assert b"your scenario" in response.data
    api = client.post(
        "/api/compare", json={"ticker": "DEMO", "assumptions": assumptions}
    )
    assert api.status_code == 200, api.get_json()
    packet = api.get_json()
    assert packet["custom"] is True
    assert packet["lanes"][1]["band"]["Bull"] > packet["lanes"][1]["band"]["Bear"]
    bad = client.post(
        "/compare", data={"ticker": "DEMO", "assumptions": "{broken"}
    )
    assert bad.status_code == 400


@pytest.mark.parametrize("claim", ["preferred_equity", "minority_interest"])
def test_compare_does_not_value_residual_income_with_unmodeled_claims(monkeypatch, claim):
    import auto_loading
    from compare import football_field
    from dcf_loader import demo_document

    doc = demo_document()
    doc["bridge"][claim] = 10.0
    monkeypatch.setattr(auto_loading, "load_method", _fake_loader([], doc))
    packet = football_field("DEMO")
    assert packet["readiness"]["residual"]["state"] == "unavailable"
    lane = next(lane for lane in packet["lanes"] if lane["method"] == "residual")
    assert lane["value"] is None
    assert "not modeled" in lane["detail"]


def test_financial_firm_residual_forecast_does_not_require_fcff(monkeypatch):
    import auto_loading
    from compare import football_field
    from dcf_loader import demo_document

    doc = demo_document()
    doc['company']['is_financial'] = True
    doc['source']['capital_costs'] = {'cost_of_equity': 0.07}
    monkeypatch.setattr(auto_loading, 'load_method', _fake_loader([], doc))
    packet = football_field('DEMO')
    dcf = next(x for x in packet['lanes'] if x['method'] == 'dcf')
    residual = next(x for x in packet['lanes'] if x['method'] == 'residual')
    assert dcf['value'] is None
    assert isinstance(residual['value'], float)
