"""Edge-cache safety: user-scope and bearer-token responses must never be
publicly cacheable, while public reference data stays cacheable."""

import pytest

from app import app


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("DCF_STATE_PATH", str(tmp_path / "library.sqlite3"))


def client(tmp_path):
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))
    return app.test_client()


def test_user_pages_are_private_no_store(tmp_path):
    c = client(tmp_path)
    for path in ("/", "/compare", "/watchlist", "/providers"):
        res = c.get(path)
        assert res.status_code == 200, path
        assert res.headers["Cache-Control"] == "private, no-store", path


def test_identity_minting_response_is_not_cacheable(tmp_path):
    c = client(tmp_path)
    res = c.get("/")
    assert res.headers.get("Set-Cookie"), "fresh visitor must mint identity"
    assert res.headers["Cache-Control"] == "private, no-store"


def _share_token(c):
    import library
    from dcf_loader import demo_document
    from dcf_code import DCFAssumptions
    from app import evaluate
    from tests.test_library import ASSUMPTIONS
    from valuation_records import record_values

    doc = demo_document()
    result = evaluate(doc, DCFAssumptions(**ASSUMPTIONS))
    c.get("/api/history")  # mints the signed owner cookie
    cookie = c.get_cookie("lib_id")
    assert cookie is not None
    with app.test_request_context(
        "/",
        environ_overrides={
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_COOKIE": f"lib_id={cookie.value}",
        },
    ):
        values = record_values(doc, DCFAssumptions(**ASSUMPTIONS), result, library.caller_hash())
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
    rows = c.get("/api/history").get_json()
    assert len(rows) == 1
    return c.post("/api/share", json={"valuation_id": rows[0]["id"]}).get_json()["token"]


def test_shared_link_live_and_revoked_are_not_cacheable(tmp_path):
    c = client(tmp_path)
    token = _share_token(c)
    live = c.get(f"/v/{token}")
    assert live.status_code == 200
    assert live.headers["Cache-Control"] == "private, no-store"
    assert c.delete(f"/api/share/{token}").status_code in (200, 204)
    gone = c.get(f"/v/{token}")
    assert gone.status_code == 404
    assert "no-store" in gone.headers["Cache-Control"]


def test_unknown_shared_link_is_not_cacheable(tmp_path):
    c = client(tmp_path)
    res = c.get("/v/nope")
    assert res.status_code == 404
    assert "no-store" in res.headers["Cache-Control"]


def test_separate_users_do_not_share_watchlist(tmp_path):
    first, second = client(tmp_path), client(tmp_path)
    saved = first.post(
        "/api/watchlist",
        json={"ticker": "AAPL", "target": 100, "direction": "above"},
    )
    assert saved.status_code in (200, 201)
    assert first.get("/api/watchlist").get_json() != []
    assert second.get("/api/watchlist").get_json() == []


def test_public_reference_stays_edge_cacheable(tmp_path):
    c = client(tmp_path)
    res = c.get("/api/sample")
    assert res.status_code == 200
    assert res.headers["Cache-Control"].startswith("public, max-age=300")
