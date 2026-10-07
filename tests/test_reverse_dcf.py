"""Reverse DCF solves the implied driver or reports why it cannot."""

from dataclasses import asdict

import pytest

from app import app
from compare import baseline_dcf_assumptions
from dcf_loader import demo_document
from reverse_dcf import solve


def fixture():
    doc = demo_document()
    return doc, baseline_dcf_assumptions(doc, 0.065)


def test_solves_implied_growth_near_model_price():
    from app import evaluate

    doc, a = fixture()
    price = evaluate(doc, a)["intrinsic_value"]
    out = solve(doc, a, price, "revenue_growth")
    assert out["status"] == "solved"
    assert abs(out["implied"] - 0.05) < 0.005
    assert len(out["historical"]) == 2


def test_reports_above_and_below_range():
    doc, a = fixture()
    assert solve(doc, a, 1e12, "revenue_growth")["status"] == "above_range"
    assert solve(doc, a, 0.01, "revenue_growth")["status"] == "below_range"
    assert solve(doc, a, 1e12, "ebit_margin")["status"] == "above_range"


def test_rejects_bad_driver_and_price():
    doc, a = fixture()
    with pytest.raises(ValueError):
        solve(doc, a, 10.0, "wacc")
    with pytest.raises(ValueError):
        solve(doc, a, -5, "revenue_growth")


def test_reverse_endpoint(tmp_path):
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))
    doc, a = fixture()
    client = app.test_client()
    response = client.post(
        "/api/reverse",
        json={
            "financials": doc,
            "assumptions": asdict(a),
            "market_price": doc["market"]["price"],
        },
    )
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    assert body["revenue_growth"]["status"] == "solved"
    assert body["ebit_margin"]["status"] in {"solved", "above_range", "below_range"}
    assert client.post("/api/reverse", json={}).status_code == 400
