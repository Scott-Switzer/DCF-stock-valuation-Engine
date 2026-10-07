"""Templates, history, share links and watchlist use caller-scoped storage."""

import pytest

from app import app


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("DCF_STATE_PATH", str(tmp_path / "library.sqlite3"))


def client(tmp_path):
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))
    return app.test_client()


ASSUMPTIONS = {
    "revenue_growth_rates": [0.05] * 5,
    "terminal_growth_rate": 0.02,
    "wacc_override": 0.065,
    "terminal_mode": "template",
    "ebit_margins": [0.2] * 5,
    "da_margins": [0.05] * 5,
    "capex_margins": [0.06] * 5,
    "nwc_margins": [0.02] * 5,
    "tax_rates": [0.21] * 5,
    "net_income_margins": [0.15] * 5,
    "book_value_margins": [0.5] * 5,
}


def test_templates_crud(tmp_path):
    c = client(tmp_path)
    assert c.get("/api/templates?method=dcf").get_json() == []
    saved = c.post(
        "/api/templates",
        json={"name": "Bull", "method": "dcf", "assumptions": ASSUMPTIONS},
    )
    assert saved.status_code == 200
    listed = c.get("/api/templates?method=dcf").get_json()
    assert len(listed) == 1 and listed[0]["assumptions"] == ASSUMPTIONS
    assert c.get("/api/templates?method=ddm").get_json() == []
    assert c.delete(f"/api/templates/{listed[0]['id']}").status_code == 200
    assert c.get("/api/templates").get_json() == []
    bad = c.post("/api/templates", json={"name": "", "method": "dcf",
                                          "assumptions": ASSUMPTIONS})
    assert bad.status_code == 400


def test_share_requires_owned_valuation(tmp_path):
    c = client(tmp_path)
    missing = c.post("/api/share", json={"valuation_id": "nope"})
    assert missing.status_code == 400
    assert c.get("/v/nope").status_code == 404


def test_watchlist_crud_and_validation(tmp_path):
    c = client(tmp_path)
    assert c.get("/api/watchlist").get_json() == []
    assert c.post("/api/watchlist",
                  json={"ticker": "AAPL", "target": 200, "direction": "above"}
                  ).status_code == 200
    assert c.post("/api/watchlist",
                  json={"ticker": "!!!", "target": 1, "direction": "above"}
                  ).status_code == 400
    assert c.post("/api/watchlist",
                  json={"ticker": "AAPL", "target": 1, "direction": "sideways"}
                  ).status_code == 400
    entries = c.get("/api/watchlist").get_json()
    assert [e["ticker"] for e in entries] == ["AAPL"]
    assert c.delete("/api/watchlist", json={"ticker": "AAPL"}).status_code == 200
    assert c.get("/api/watchlist").get_json() == []


def test_history_empty_without_saves(tmp_path):
    c = client(tmp_path)
    assert c.get("/api/history?ticker=AAPL").get_json() == []


def test_shared_view_renders_saved_record(tmp_path):
    import library
    from dcf_loader import demo_document
    from dcf_code import DCFAssumptions

    c = client(tmp_path)
    doc = demo_document()
    a = DCFAssumptions(**ASSUMPTIONS)
    from app import evaluate

    result = evaluate(doc, a)
    from valuation_records import record_values

    with app.test_request_context(
        "/", environ_overrides={"REMOTE_ADDR": "127.0.0.1"}
    ):
        values = record_values(doc, a, result, library.caller_hash())
        library.history()
    import sqlite3
    from storage import Store

    db = sqlite3.connect(Store().path)
    with db:
        db.execute(
            "INSERT OR IGNORE INTO valuations(method,id,created_at,model_version,"
            "ticker,valuation_date,source_kind,is_demo,intrinsic_value,"
            "target_price_12m,market_price,upside,assumptions_json,financials_json,"
            "result_json,client_hash,input_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            values,
        )
    db.close()
    # Find the record through history, then share and view it.
    rows = c.get("/api/history").get_json()
    assert len(rows) == 1
    token = c.post("/api/share", json={"valuation_id": rows[0]["id"]}).get_json()["token"]
    page = c.get(f"/v/{token}")
    assert page.status_code == 200
    assert b"Shared read-only" in page.data
