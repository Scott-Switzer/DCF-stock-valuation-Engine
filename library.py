"""User library: scenario templates, shared links, watchlist and history.

Dual backend: Cloudflare D1 when running on Workers, local SQLite
otherwise (same file as the rate-limit store). Rows are scoped by a
caller hash so one browser cannot enumerate another's library.
"""

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS valuations (
 id TEXT PRIMARY KEY, created_at TEXT NOT NULL, model_version TEXT NOT NULL,
 ticker TEXT NOT NULL, valuation_date TEXT NOT NULL, source_kind TEXT NOT NULL,
 is_demo INTEGER NOT NULL, intrinsic_value REAL, target_price_12m REAL NOT NULL,
 market_price REAL NOT NULL, upside REAL, assumptions_json TEXT NOT NULL,
 financials_json TEXT NOT NULL, result_json TEXT NOT NULL,
 method TEXT NOT NULL DEFAULT 'dcf', client_hash TEXT NOT NULL,
 input_hash TEXT NOT NULL, UNIQUE(client_hash,input_hash));
CREATE TABLE IF NOT EXISTS templates (
 id TEXT PRIMARY KEY, created_at TEXT NOT NULL, client_hash TEXT NOT NULL,
 name TEXT NOT NULL, method TEXT NOT NULL, assumptions_json TEXT NOT NULL,
 UNIQUE(client_hash, name));
CREATE TABLE IF NOT EXISTS share_links (
 token TEXT PRIMARY KEY, valuation_id TEXT NOT NULL, created_at TEXT NOT NULL,
 client_hash TEXT NOT NULL, expires_at TEXT, revoked_at TEXT);
CREATE TABLE IF NOT EXISTS watchlist (
 client_hash TEXT NOT NULL, ticker TEXT NOT NULL, target REAL NOT NULL,
 direction TEXT NOT NULL CHECK(direction IN ('above','below')),
 created_at TEXT NOT NULL, PRIMARY KEY (client_hash, ticker));
CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
 created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, created_at TEXT NOT NULL,
 expires_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS sessions_expiry ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS valuations_owner_created ON valuations(client_hash, created_at);
CREATE TABLE IF NOT EXISTS research_documents (
 id TEXT PRIMARY KEY, client_hash TEXT NOT NULL, created_at TEXT NOT NULL,
 parent_id TEXT, title TEXT NOT NULL, ticker TEXT NOT NULL, method TEXT NOT NULL,
 scenario_name TEXT NOT NULL, financial_hash TEXT NOT NULL,
 market_price REAL NOT NULL, target_price REAL NOT NULL, snapshot_json TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS research_owner_created ON research_documents(client_hash, created_at);
CREATE INDEX IF NOT EXISTS research_owner_financial ON research_documents(client_hash, financial_hash, created_at);
"""


COOKIE = "lib_id"
WATCH_LIMIT = 25
WATCH_BUDGET_SECONDS = 12
SHARE_MAX_DAYS = 365
SHARE_LIST_LIMIT = 50


def same_origin_request():
    """Browser writes must come from this origin; non-browser clients send no Origin."""
    from flask import request

    origin = request.headers.get("Origin")
    if origin is not None:
        return origin.lower() == request.host_url.rstrip("/").lower()
    return request.headers.get("Sec-Fetch-Site") in {None, "same-origin", "same-site", "none"}


def _secret():
    from flask import current_app, request, has_request_context

    if has_request_context() and current_app.config.get("CLOUDFLARE"):
        env = request.environ["workers.env"]
        configured = getattr(env, "LIBRARY_SECRET", None)
        if configured:
            return str(configured).encode()
        # Derive a separate signing key from the existing private Worker secret.
        salt = getattr(env, "RECORD_SALT", None)
        if not salt:
            raise RuntimeError("A production library signing secret is required.")
        return hmac.new(str(salt).encode(), b"valuation-library-cookie-v1", hashlib.sha256).digest()
    return os.getenv("LIBRARY_SECRET", "dev-only-library-secret").encode()


def _sign(value):
    return hmac.new(_secret(), value.encode(), hashlib.sha256).hexdigest()


LIBRARY_PATHS = (
    "/api/research", "/research",
    "/api/templates", "/api/history", "/api/share", "/api/watchlist",
    "/watchlist", "/compare", "/api/calculate", "/ddm", "/relative",
)


def anonymous_hash():
    """The signed browser library owner, or None when no valid cookie is present."""
    from flask import request

    raw = request.cookies.get(COOKIE, "")
    if raw and "." in raw:
        identity, signature = raw.split(".", 1)
        if hmac.compare_digest(signature, _sign(identity)):
            return f"lib:{identity}"
    return None


def caller_hash():
    """Stable library owner: a signed-in account, else the browser library."""
    from flask import request, current_app
    from accounts import owner_hash

    account = owner_hash()
    if account:
        return account
    fresh = request.environ.get("lib.new_identity")
    if fresh:
        return f"lib:{fresh}"
    anonymous = anonymous_hash()
    if anonymous:
        return anonymous
    if current_app.config.get("CLOUDFLARE"):
        return request.environ["dcf.client_hash"]
    from datetime import date

    return f"local:{request.remote_addr}:{date.today().isoformat()}"


def ensure_identity():
    """Mint the owner identity before the request so reads and writes share a scope."""
    from flask import request

    if request.path != "/" and not request.path.startswith(LIBRARY_PATHS):
        return
    raw = request.cookies.get(COOKIE, "")
    if raw and "." in raw:
        identity, signature = raw.split(".", 1)
        if hmac.compare_digest(signature, _sign(identity)):
            return
    request.environ["lib.new_identity"] = secrets.token_urlsafe(16)


def persist_identity(response):
    """Set the minted owner cookie on the way out."""
    from flask import request

    fresh = request.environ.get("lib.new_identity")
    if fresh:
        response.set_cookie(
            COOKIE,
            f"{fresh}.{_sign(fresh)}",
            max_age=5 * 365 * 24 * 3600,
            httponly=True,
            secure=True,
            samesite="Lax",
        )
    return response


def _local():
    from storage import Store

    db = sqlite3.connect(Store().path, timeout=5)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    # Local databases created before share controls lack these columns.
    have = {row[1] for row in db.execute("PRAGMA table_info(share_links)")}
    for column in ("expires_at", "revoked_at"):
        if column not in have:
            db.execute(f"ALTER TABLE share_links ADD COLUMN {column} TEXT")
    return db


def is_unique_violation(exc):
    """True for a UNIQUE constraint failure from SQLite or D1."""
    return "UNIQUE constraint failed" in str(exc)


def _fetchall(sql, params=()):
    from flask import request, current_app

    if current_app.config.get("CLOUDFLARE"):
        from pyodide.ffi import run_sync

        result = run_sync(
            request.environ["workers.env"].DB.prepare(sql).bind(*params).all()
        )
        # D1 returns an envelope. Workers may already convert its row array.
        rows = result.results
        if hasattr(rows, "to_py"):
            rows = rows.to_py()
        return [dict(row.to_py()) if hasattr(row, "to_py") else dict(row) for row in rows]
    db = _local()
    try:
        return [dict(r) for r in db.execute(sql, params).fetchall()]
    finally:
        db.close()


def _run(sql, params=()):
    from flask import request, current_app

    if current_app.config.get("CLOUDFLARE"):
        from pyodide.ffi import run_sync

        run_sync(request.environ["workers.env"].DB.prepare(sql).bind(*params).run())
        return
    db = _local()
    try:
        with db:
            db.execute(sql, params)
    finally:
        db.close()


def now():
    return datetime.now(timezone.utc).isoformat()


def save_template(name, method, assumptions):
    if not isinstance(name, str) or not name.strip() or len(name) > 60:
        raise ValueError("Name this template (up to 60 characters).")
    if method not in {"dcf", "ddm", "relative"}:
        raise ValueError("Unknown method.")
    if not isinstance(assumptions, dict) or not assumptions:
        raise ValueError("Template needs an assumptions object.")
    identity = str(uuid.uuid4())
    _run(
        "INSERT OR REPLACE INTO templates"
        "(id,created_at,client_hash,name,method,assumptions_json)"
        " VALUES (?,?,?,?,?,?)",
        (identity, now(), caller_hash(), name.strip(), method,
         json.dumps(assumptions, allow_nan=False)),
    )
    return identity


def list_templates(method=None):
    rows = _fetchall(
        "SELECT id,created_at,name,method,assumptions_json FROM templates"
        " WHERE client_hash=? ORDER BY created_at DESC",
        (caller_hash(),),
    )
    out = []
    for row in rows:
        if method and row["method"] != method:
            continue
        row["assumptions"] = json.loads(row["assumptions_json"])
        del row["assumptions_json"]
        out.append(row)
    return out


def delete_template(identity):
    _run("DELETE FROM templates WHERE id=? AND client_hash=?", (identity, caller_hash()))


def history(ticker=None, limit=20):
    sql = (
        "SELECT id,created_at,ticker,method,intrinsic_value,target_price_12m,"
        "market_price,upside FROM valuations WHERE client_hash=?"
    )
    params: list = [caller_hash()]
    if ticker:
        sql += " AND ticker=?"
        params.append(ticker)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(max(1, min(50, int(limit or 20))))
    return _fetchall(sql, tuple(params))


def _share_expiry(days):
    """ISO expiry for an optional whole-number day count; None means no expiry."""
    if days is None or days == "":
        return None
    if isinstance(days, bool) or (isinstance(days, float) and not days.is_integer()):
        raise ValueError("Expiry must be a whole number of days.")
    try:
        count = int(days)
    except (TypeError, ValueError):
        raise ValueError("Expiry must be a whole number of days.") from None
    if not 1 <= count <= SHARE_MAX_DAYS:
        raise ValueError(f"Expiry must be 1 to {SHARE_MAX_DAYS} days.")
    return (datetime.now(timezone.utc) + timedelta(days=count)).isoformat()


def create_share(valuation_id, expires_in_days=None):
    expires_at = _share_expiry(expires_in_days)
    rows = _fetchall(
        "SELECT id FROM valuations WHERE id=? AND client_hash=?",
        (valuation_id, caller_hash()),
    )
    if not rows:
        raise ValueError("Valuation not found.")
    token = secrets.token_urlsafe(16)
    _run(
        "INSERT INTO share_links(token,valuation_id,created_at,client_hash,expires_at)"
        " VALUES (?,?,?,?,?)",
        (token, valuation_id, now(), caller_hash(), expires_at),
    )
    return token


def list_shares(offset=0):
    """The caller's own share links, newest first, with their status fields."""
    return _fetchall(
        "SELECT token,valuation_id,created_at,expires_at,revoked_at FROM share_links"
        " WHERE client_hash=? ORDER BY created_at DESC,token DESC LIMIT ? OFFSET ?",
        (caller_hash(), SHARE_LIST_LIMIT, offset),
    )


def revoke_share(token):
    """Revoke one of the caller's links. Other owners' links look like missing ones."""
    owner = caller_hash()
    rows = _fetchall(
        "SELECT token FROM share_links WHERE token=? AND client_hash=?", (token, owner)
    )
    if not rows:
        raise ValueError("Share link not found.")
    _run(
        "UPDATE share_links SET revoked_at=? WHERE token=? AND client_hash=?"
        " AND revoked_at IS NULL",
        (now(), token, owner),
    )


def shared_valuation(token):
    """The saved valuation behind a live link; revoked or expired links return None."""
    rows = _fetchall(
        "SELECT v.assumptions_json,v.financials_json,v.result_json"
        " FROM share_links s JOIN valuations v ON v.id=s.valuation_id"
        " WHERE s.token=? AND s.revoked_at IS NULL"
        " AND (s.expires_at IS NULL OR s.expires_at>?)",
        (token, now()),
    )
    if not rows:
        return None
    row = rows[0]
    return {
        "assumptions": json.loads(row["assumptions_json"]),
        "financials": json.loads(row["financials_json"]),
        "result": json.loads(row["result_json"]),
    }


def set_watch(ticker, target, direction):
    from dcf_loader import ticker_symbol

    symbol = ticker_symbol(ticker)
    try:
        level = float(target)
    except (TypeError, ValueError):
        raise ValueError("Alert target must be a number.") from None
    if direction not in {"above", "below"}:
        raise ValueError("Direction is above or below.")
    current = {row["ticker"] for row in _fetchall(
        "SELECT ticker FROM watchlist WHERE client_hash=?", (caller_hash(),))}
    if symbol not in current and len(current) >= WATCH_LIMIT:
        raise ValueError(
            f"Watchlists hold up to {WATCH_LIMIT} tickers. Remove one before adding another."
        )
    _run(
        "INSERT OR REPLACE INTO watchlist"
        "(client_hash,ticker,target,direction,created_at) VALUES (?,?,?,?,?)",
        (caller_hash(), symbol, level, direction, now()),
    )
    return symbol


def list_watch():
    return _fetchall(
        "SELECT ticker,target,direction,created_at FROM watchlist"
        " WHERE client_hash=? ORDER BY created_at DESC",
        (caller_hash(),),
    )


def remove_watch(ticker):
    from dcf_loader import ticker_symbol

    _run(
        "DELETE FROM watchlist WHERE client_hash=? AND ticker=?",
        (caller_hash(), ticker_symbol(ticker)),
    )


def check_watch():
    """Re-price watched tickers with cheap quotes under one shared time budget.

    Quotes come from the provider's one-day chart metadata, so a refresh never
    loads statements, peers or capital costs. The budget is one JsonHTTP
    deadline for the whole refresh; tickers reached after it expires are marked
    unchecked rather than holding the page.
    """
    from dcf_loader import JsonHTTP, ProviderError
    from yahoo_provider import latest_quote

    asof = datetime.now(timezone.utc).date().isoformat()
    http = JsonHTTP(budget=WATCH_BUDGET_SECONDS)
    states = []
    for entry in list_watch():
        state = dict(entry)
        if http.expired():
            state.update(
                price=None,
                breached=False,
                error="Not re-priced in this refresh. Reload to check the rest.",
            )
            states.append(state)
            continue
        try:
            quote = latest_quote(entry["ticker"], asof, http)
            price = quote["price"]
            state["price"] = price
            state["price_as_of"] = quote["price_as_of"]
            state["breached"] = (
                price >= entry["target"]
                if entry["direction"] == "above"
                else price <= entry["target"]
            )
        except (ProviderError, ValueError) as exc:
            state["price"] = None
            state["error"] = str(exc)
            state["breached"] = False
        states.append(state)
    return states
