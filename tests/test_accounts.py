"""Accounts: hashed passwords, server-side sessions, and per-account isolation."""

import sqlite3

import pytest

import accounts
import library
from app import app
from storage import Store

PASSWORD = "correct horse battery"
TEMPLATE = {"name": "Bull", "method": "dcf", "assumptions": {
    "revenue_growth_rates": [0.05] * 5, "terminal_growth_rate": 0.02,
    "wacc_override": 0.065, "terminal_mode": "template", "ebit_margins": [0.2] * 5,
    "da_margins": [0.05] * 5, "capex_margins": [0.06] * 5, "nwc_margins": [0.02] * 5,
    "tax_rates": [0.21] * 5, "net_income_margins": [0.15] * 5,
    "book_value_margins": [0.5] * 5}}


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("DCF_STATE_PATH", str(tmp_path / "library.sqlite3"))
    # Rate limiting has its own tests; these focus on account behaviour.
    monkeypatch.setattr(Store, "allow", lambda self, key, maximum=10, window=60: True)
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))


def db():
    return sqlite3.connect(Store().path)


def signup(client, email, password=PASSWORD):
    return client.post("/api/account/signup", json={"email": email, "password": password})


def as_user(token):
    client = app.test_client()
    client.set_cookie("dcf_session", token)
    return client


def session_token(client):
    return client.get_cookie("dcf_session").value


def test_signup_sets_hardened_session_cookie():
    c = app.test_client()
    res = signup(c, "Analyst@Example.com ")
    assert res.status_code == 200
    assert res.get_json() == {"email": "analyst@example.com", "signed_in": True}
    header = res.headers["Set-Cookie"]
    assert "dcf_session=" in header
    assert "HttpOnly" in header and "Secure" in header and "SameSite=Lax" in header
    assert "no-store" in res.headers["Cache-Control"]
    me = as_user(session_token(c)).get("/api/account/me")
    assert me.get_json()["email"] == "analyst@example.com"


def test_me_requires_a_session():
    res = app.test_client().get("/api/account/me")
    assert res.status_code == 401
    assert "no-store" in res.headers["Cache-Control"]


def test_passwords_and_tokens_are_never_stored_in_clear():
    c = app.test_client()
    signup(c, "stored@example.com")
    token = session_token(c)
    with db() as conn:
        (stored,) = conn.execute("SELECT password_hash FROM users").fetchone()
        (digest,) = conn.execute("SELECT token_hash FROM sessions").fetchone()
    assert stored.startswith("pbkdf2_sha256$100000$") and PASSWORD not in stored
    assert digest != token and len(digest) == 64


def test_wrong_password_and_unknown_email_fail_identically():
    c = app.test_client()
    signup(c, "owner@example.com")
    wrong = app.test_client().post(
        "/api/account/login", json={"email": "owner@example.com", "password": "wrong password!!"})
    unknown = app.test_client().post(
        "/api/account/login", json={"email": "nobody@example.com", "password": PASSWORD})
    assert wrong.status_code == unknown.status_code == 400
    assert wrong.get_json() == unknown.get_json() == {"error": accounts.FAILURE}
    assert "Set-Cookie" not in wrong.headers


def test_signup_validation_and_duplicates():
    c = app.test_client()
    assert signup(c, "short@example.com", "tooshort").status_code == 400
    assert signup(c, "not-an-email", PASSWORD).status_code == 400
    assert signup(c, "dup@example.com").status_code == 200
    again = signup(app.test_client(), "DUP@example.com")
    assert again.status_code == 400 and "already has an account" in again.get_json()["error"]


def test_login_issues_a_new_session_and_logout_revokes_it():
    first = app.test_client()
    signup(first, "rotate@example.com")
    old = session_token(first)
    login = app.test_client().post(
        "/api/account/login", json={"email": "rotate@example.com", "password": PASSWORD})
    assert login.status_code == 200
    new = login.headers["Set-Cookie"].split(";")[0].split("=", 1)[1]
    assert new != old
    assert as_user(new).get("/api/account/me").status_code == 200
    out = as_user(new).post("/api/account/logout")
    assert out.status_code == 200 and "Max-Age=0" in out.headers["Set-Cookie"]
    assert as_user(new).get("/api/account/me").status_code == 401


def test_expired_sessions_are_rejected():
    c = app.test_client()
    signup(c, "expiry@example.com")
    token = session_token(c)
    with db() as conn:
        conn.execute("UPDATE sessions SET expires_at='2000-01-01T00:00:00+00:00'")
    assert as_user(token).get("/api/account/me").status_code == 401


def test_accounts_see_only_their_own_library():
    a = app.test_client()
    signup(a, "alice@example.com")
    token_a = session_token(a)
    assert as_user(token_a).post("/api/templates", json=TEMPLATE).status_code == 200
    b = app.test_client()
    signup(b, "bob@example.com")
    token_b = session_token(b)
    assert as_user(token_b).get("/api/templates?method=dcf").get_json() == []
    names = [t["name"] for t in as_user(token_a).get("/api/templates?method=dcf").get_json()]
    assert names == ["Bull"]


def test_browser_library_is_claimed_on_signup():
    anonymous = app.test_client()
    assert anonymous.post("/api/templates", json=TEMPLATE).status_code == 200
    lib_cookie = anonymous.get_cookie("lib_id").value
    signing = app.test_client()
    signing.set_cookie("lib_id", lib_cookie)
    assert signup(signing, "claim@example.com").status_code == 200
    names = [t["name"] for t in as_user(session_token(signing)).get(
        "/api/templates?method=dcf").get_json()]
    assert names == ["Bull"]


def test_change_password_revokes_other_sessions_only():
    first = app.test_client()
    signup(first, "rotate-pw@example.com")
    keep = session_token(first)
    other = app.test_client().post(
        "/api/account/login", json={"email": "rotate-pw@example.com", "password": PASSWORD})
    other_token = other.headers["Set-Cookie"].split(";")[0].split("=", 1)[1]
    assert as_user(other_token).get("/api/account/me").status_code == 200

    new_password = "a brand new passphrase"
    wrong = as_user(keep).post("/api/account/password", json={
        "current_password": "not the password", "new_password": new_password})
    assert wrong.status_code == 400 and wrong.get_json() == {"error": "Current password is incorrect."}
    assert as_user(keep).get("/api/account/me").status_code == 200

    ok = as_user(keep).post("/api/account/password", json={
        "current_password": PASSWORD, "new_password": new_password})
    assert ok.status_code == 200 and ok.get_json() == {"changed": True, "signed_in": True}
    assert as_user(keep).get("/api/account/me").status_code == 200
    assert as_user(other_token).get("/api/account/me").status_code == 401
    old = app.test_client().post(
        "/api/account/login", json={"email": "rotate-pw@example.com", "password": PASSWORD})
    assert old.status_code == 400
    new = app.test_client().post(
        "/api/account/login", json={"email": "rotate-pw@example.com", "password": new_password})
    assert new.status_code == 200


def test_change_password_requires_a_session_and_short_replacements_fail():
    anonymous = app.test_client().post(
        "/api/account/password", json={"current_password": PASSWORD, "new_password": "long enough password"})
    assert anonymous.status_code == 401
    c = app.test_client()
    signup(c, "short-pw@example.com")
    short = as_user(session_token(c)).post("/api/account/password", json={
        "current_password": PASSWORD, "new_password": "tiny"})
    assert short.status_code == 400
    assert as_user(session_token(c)).get("/api/account/me").status_code == 200


def test_account_routes_are_rate_limited_locally(monkeypatch):
    monkeypatch.setattr(
        Store, "allow",
        lambda self, key, maximum=10, window=60: not key.endswith("/api/account/login"))
    res = app.test_client().post(
        "/api/account/login", json={"email": "x@example.com", "password": PASSWORD})
    assert res.status_code == 429


def test_cross_site_account_writes_are_rejected():
    library._local().close()  # initialise the schema so the count below is meaningful
    res = app.test_client().post(
        "/api/account/signup", json={"email": "csrf@example.com", "password": PASSWORD},
        headers={"Origin": "https://evil.example"})
    assert res.status_code == 403
    with db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0


def test_form_flow_for_the_account_page():
    c = app.test_client()
    page = c.get("/account")
    assert page.status_code == 200 and b"Create account" in page.data
    assert page.headers["Cache-Control"] == "private, no-store"
    res = c.post("/account/signup", data={"email": "form@example.com", "password": PASSWORD})
    assert res.status_code == 303 and res.headers["Location"] == "/account"
    assert b"Signed in as" in c.get("/account").data
    bad = app.test_client().post("/account/login", data={"email": "form@example.com",
                                                          "password": "nope nope nope"})
    assert bad.status_code == 400 and accounts.FAILURE.encode() in bad.data


def test_password_hash_roundtrip_and_rejects_malformed_or_oversized_costs():
    stored = accounts.hash_password(b"a password of length twelve+")
    assert accounts.verify_password(b"a password of length twelve+", stored)
    assert not accounts.verify_password(b"something else entirely!", stored)
    assert not accounts.verify_password(b"x", "not-a-hash")
    too_costly = stored.replace("$100000$", "$150000$")
    assert not accounts.verify_password(b"a password of length twelve+", too_costly)


def test_iteration_count_stays_within_workers_webcrypto_cap():
    assert accounts.ITERATIONS <= 100_000
    assert accounts.MIN_PASSWORD >= 12
