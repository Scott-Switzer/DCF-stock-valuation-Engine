from copy import deepcopy
import io
import json
import sqlite3
import zipfile

import pytest

from app import app, assumptions_from_json, evaluate
from dcf_loader import demo_document
from storage import Store
from suite_models import suite_sample


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("DCF_STATE_PATH", str(tmp_path / "research.sqlite3"))
    monkeypatch.setattr(Store, "allow", lambda *args, **kwargs: True)
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "limits.sqlite3"))


def payload(method="dcf"):
    assumptions = {"revenue_growth_rates": [0.05] * 5, "terminal_growth_rate": 0.02, "wacc_override": 0.10}
    if method == "ddm":
        assumptions = {"dividend_growth_rates": [0.05] * 5, "required_return": 0.07, "terminal_growth_rate": 0.02}
    elif method == "relative":
        assumptions = {"included_methods": ["pe"]}
    return {"title": "Company research", "scenario_name": "Base", "method": method,
            "financials": demo_document() if method == "dcf" else suite_sample(method),
            "assumptions": assumptions, "thesis": {"thesis": "Test conclusion", "evidence": "User-provided source"}}


@pytest.mark.parametrize("method", ["dcf", "ddm", "relative"])
def test_save_read_and_export_frozen_snapshot(method):
    client = app.test_client()
    data = payload(method)
    data["result"] = {"target_price_12m": 999999999}  # Never trusted.
    response = client.post("/api/research", json=data)
    assert response.status_code == 201, response.get_json()
    record = response.get_json()
    assert record["snapshot"]["result"]["target_price_12m"] != 999999999
    data["thesis"]["thesis"] = "Later draft must not mutate saved notes"
    read = client.get(f"/api/research/{record['id']}").get_json()
    assert read == record
    assert read["snapshot"]["thesis"]["thesis"] == "Test conclusion"
    export = client.get(f"/research/{record['id']}/export/json")
    assert export.status_code == 200
    assert export.get_json() == record
    assert "no-store" in export.headers["Cache-Control"]
    workbook = client.get(f"/research/{record['id']}/export/xlsx")
    assert workbook.status_code == 200
    assert zipfile.ZipFile(io.BytesIO(workbook.data)).testzip() is None
    assert client.get(f"/research/{record['id']}").status_code == 200


def test_saved_result_matches_engine_and_revision_is_immutable():
    client = app.test_client()
    data = payload()
    first = client.post("/api/research", json=data).get_json()
    expected = evaluate(data["financials"], assumptions_from_json(data["assumptions"]))
    assert first["target_price"] == expected["target_price_12m"]
    data.update(parent_id=first["id"], scenario_name="Bull")
    data["assumptions"]["revenue_growth_rates"] = [0.10] * 5
    data["thesis"]["thesis"] = "Updated thesis"
    second = client.post("/api/research", json=data).get_json()
    assert first["id"] != second["id"]
    assert first["financial_hash"] == second["financial_hash"]
    assert first["target_price"] < second["target_price"]
    assert client.get(f"/api/research/{first['id']}").get_json() == first
    body = client.get(f"/research/{second['id']}").get_data(as_text=True)
    assert "Base" in body and "Bull" in body and "exact financial-input hash" in body


def test_anonymous_library_and_foreign_revision_are_isolated():
    owner, other = app.test_client(), app.test_client()
    record = owner.post("/api/research", json=payload()).get_json()
    assert other.get("/api/research").get_json() == []
    for path in [f"/api/research/{record['id']}", f"/research/{record['id']}", f"/research/{record['id']}/export/json", f"/research/{record['id']}/export/xlsx"]:
        assert other.get(path).status_code == 404
    data = payload()
    data["parent_id"] = record["id"]
    assert other.post("/api/research", json=data).status_code == 400
    replay = app.test_client()
    replay.set_cookie("lib_id", owner.get_cookie("lib_id").value)
    assert replay.get(f"/api/research/{record['id']}").get_json() == record


def test_account_claim_preserves_research_and_other_account_isolation():
    owner, other = app.test_client(), app.test_client()
    record = owner.post("/api/research", json=payload()).get_json()
    response = owner.post("/api/account/signup", json={"email": "research@example.invalid", "password": "correct horse battery"})
    assert response.status_code == 200
    assert owner.get(f"/api/research/{record['id']}").status_code == 200
    assert other.post("/api/account/signup", json={"email": "other@example.invalid", "password": "correct horse battery"}).status_code == 200
    assert other.get(f"/api/research/{record['id']}").status_code == 404
    second_session = app.test_client()
    second_session.set_cookie("dcf_session", owner.get_cookie("dcf_session").value)
    assert second_session.get(f"/api/research/{record['id']}").status_code == 200


def test_foreign_origin_rejected_and_cookie_hardened():
    client = app.test_client()
    assert client.post("/api/research", json=payload(), headers={"Origin": "https://evil.invalid"}).status_code == 403
    response = app.test_client().post("/api/research", json=payload())
    cookie = response.headers["Set-Cookie"]
    assert "Secure" in cookie and "HttpOnly" in cookie and "SameSite=Lax" in cookie


@pytest.mark.parametrize("change", [
    {"title": ""}, {"title": "a" * 101}, {"scenario_name": ""}, {"method": "residual"},
    {"financials": None}, {"thesis": {"unexpected": "not supported"}},
    {"thesis": {"thesis": "a" * 4001}}, {"thesis": {"thesis": None}},
    {"parent_id": "missing"},
])
def test_invalid_research_is_rejected_without_saving(change):
    client = app.test_client()
    data = payload()
    data.update(change)
    assert client.post("/api/research", json=data).status_code == 400
    assert client.get("/api/research").get_json() == []


def test_source_snapshot_changes_do_not_mix_scenario_groups():
    client = app.test_client()
    data = payload()
    first = client.post("/api/research", json=data).get_json()
    data = deepcopy(data)
    data["financials"]["market"]["price"] *= 2
    second = client.post("/api/research", json=data).get_json()
    assert first["financial_hash"] != second["financial_hash"]


def test_research_text_is_escaped_in_printable_report():
    client = app.test_client()
    data = payload()
    data["title"] = '<script>alert("title")</script>'
    data["thesis"]["thesis"] = '<img src=x onerror=alert("notes")>'
    record = client.post("/api/research", json=data).get_json()
    body = client.get(f"/research/{record['id']}").get_data(as_text=True)
    assert '<script>alert("title")</script>' not in body
    assert '<img src=x' not in body
    assert "&lt;img" in body


def test_migration_is_additive_idempotent_and_preserves_existing_rows():
    from pathlib import Path

    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE valuations (id TEXT)")
    db.execute("INSERT INTO valuations VALUES ('preserved')")
    sql = (Path(__file__).resolve().parents[1] / "migrations/0008_research.sql").read_text()
    db.executescript(sql)
    db.executescript(sql)
    assert db.execute("SELECT id FROM valuations").fetchall() == [("preserved",)]
    assert db.execute("SELECT count(*) FROM research_documents").fetchone() == (0,)


def test_workspace_has_structured_thesis_controls_and_research_library():
    client = app.test_client()
    body = client.get("/").get_data(as_text=True)
    assert 'id="research-form"' in body and 'id="research-save" disabled' in body
    assert 'name="market_disagreement"' in body and 'name="evidence"' in body
    assert client.get("/research").status_code == 200
    assert json.dumps(payload(), allow_nan=False)
