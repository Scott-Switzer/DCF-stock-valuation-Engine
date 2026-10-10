"""Share links can be listed, revoked and expired; only their owner controls them.

Also covers the signup race: two requests can pass the email SELECT together,
and only the UNIQUE violation may become the friendly duplicate message.
"""

import sqlite3

import pytest

import accounts
import library
from app import app, evaluate
from dcf_code import DCFAssumptions
from dcf_loader import demo_document
from storage import Store
from valuation_records import record_values

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


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("DCF_STATE_PATH", str(tmp_path / "library.sqlite3"))
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))


def saved_valuation(client):
    """Insert one valuation owned by this client's browser library; return its id."""
    doc = demo_document()
    a = DCFAssumptions(**ASSUMPTIONS)
    result = evaluate(doc, a)
    client.get("/api/history")  # mints the signed owner cookie
    cookie = client.get_cookie("lib_id")
    with app.test_request_context(
        "/",
        environ_overrides={
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_COOKIE": f"lib_id={cookie.value}",
        },
    ):
        values = record_values(doc, a, result, library.caller_hash())
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
    return client.get("/api/history").get_json()[0]["id"]


def test_revoked_link_stops_working_and_is_listed_as_revoked():
    owner = app.test_client()
    valuation_id = saved_valuation(owner)
    token = owner.post("/api/share", json={"valuation_id": valuation_id}).get_json()["token"]
    assert owner.get(f"/v/{token}").status_code == 200

    assert owner.delete(f"/api/share/{token}").get_json() == {"revoked": True}
    assert owner.get(f"/v/{token}").status_code == 404

    [listed] = owner.get("/api/shares").get_json()
    assert listed["token"] == token and listed["revoked_at"]


def test_expired_link_stops_working_and_unexpired_link_works():
    owner = app.test_client()
    valuation_id = saved_valuation(owner)
    live = owner.post(
        "/api/share", json={"valuation_id": valuation_id, "expires_in_days": 1}
    ).get_json()["token"]
    expired = owner.post(
        "/api/share", json={"valuation_id": valuation_id, "expires_in_days": 1}
    ).get_json()["token"]
    db = sqlite3.connect(Store().path)
    with db:
        db.execute(
            "UPDATE share_links SET expires_at=? WHERE token=?",
            ("2000-01-01T00:00:00+00:00", expired),
        )
    db.close()
    assert owner.get(f"/v/{live}").status_code == 200
    assert owner.get(f"/v/{expired}").status_code == 404


@pytest.mark.parametrize("bad", [0, 366, "soon", True, 1.5])
def test_expiry_must_be_a_whole_number_of_days(bad):
    owner = app.test_client()
    valuation_id = saved_valuation(owner)
    response = owner.post(
        "/api/share", json={"valuation_id": valuation_id, "expires_in_days": bad}
    )
    assert response.status_code == 400


def test_another_owner_cannot_list_or_revoke_a_link():
    owner = app.test_client()
    valuation_id = saved_valuation(owner)
    token = owner.post("/api/share", json={"valuation_id": valuation_id}).get_json()["token"]

    stranger = app.test_client()
    assert stranger.get("/api/shares").get_json() == []
    attempt = stranger.delete(f"/api/share/{token}")
    assert attempt.status_code == 404
    # The owner's link is untouched by the failed attempt.
    assert owner.get(f"/v/{token}").status_code == 200
    assert owner.get("/api/shares").get_json()[0]["revoked_at"] is None


def test_duplicate_signup_race_gives_the_friendly_message(monkeypatch):
    with app.app_context():
        accounts.signup("racer@example.com", "a long enough password", None)
        # Simulate the race: the pre-check misses the existing row.
        monkeypatch.setattr(library, "_fetchall", lambda sql, params=(): [])
        with pytest.raises(ValueError, match="already has an account"):
            accounts.signup("racer@example.com", "a long enough password", None)


def test_unrelated_database_errors_are_not_disguised(monkeypatch):
    def broken(sql, params=()):
        raise RuntimeError("disk I/O error")

    with app.app_context():
        monkeypatch.setattr(library, "_fetchall", lambda sql, params=(): [])
        monkeypatch.setattr(library, "_run", broken)
        with pytest.raises(RuntimeError, match="disk I/O error"):
            accounts.signup("fresh@example.com", "a long enough password", None)


def test_account_page_shows_share_panel_only_when_signed_in(monkeypatch):
    client = app.test_client()
    assert b'id="share-list"' not in client.get("/account").data
    monkeypatch.setattr(
        accounts, "current_user", lambda: {"id": "u1", "email": "a@example.com", "created_at": "x"}
    )
    page = client.get("/account").data
    assert b'id="share-list"' in page and b"js/shares.js" in page


def test_old_share_links_remain_reachable_and_revocable():
    owner = app.test_client()
    valuation_id = saved_valuation(owner)
    # Insert directly so request rate limits do not mask pagination behavior.
    cookie = owner.get_cookie('lib_id')
    with app.test_request_context('/', environ_overrides={'HTTP_COOKIE': f'lib_id={cookie.value}'}):
        owner_hash = library.caller_hash()
    db = sqlite3.connect(Store().path)
    with db:
        for i in range(51):
            db.execute('INSERT INTO share_links(token,valuation_id,created_at,client_hash) VALUES (?,?,?,?)',
                       (f'page-{i:02}', valuation_id, f'2026-01-01T00:00:{i:02}+00:00', owner_hash))
    db.close()
    first = owner.get('/api/shares').get_json()
    second = owner.get('/api/shares?offset=50').get_json()
    assert len(first) == 50 and len(second) == 1
    assert second[0]['token'] == 'page-00'
    assert owner.delete('/api/share/page-00').status_code == 200
    assert owner.get('/api/shares?offset=-1').status_code == 400
