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
