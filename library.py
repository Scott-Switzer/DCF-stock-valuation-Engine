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
from datetime import datetime, timezone

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
 client_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS watchlist (
 client_hash TEXT NOT NULL, ticker TEXT NOT NULL, target REAL NOT NULL,
 direction TEXT NOT NULL CHECK(direction IN ('above','below')),
 created_at TEXT NOT NULL, PRIMARY KEY (client_hash, ticker));
"""


COOKIE = "lib_id"


def _secret():
    return os.getenv("LIBRARY_SECRET", "dev-only-library-secret").encode()


def _sign(value):
    return hmac.new(_secret(), value.encode(), hashlib.sha256).hexdigest()


LIBRARY_PATHS = (
    "/api/templates", "/api/history", "/api/share", "/api/watchlist",
    "/watchlist", "/compare",
)


def caller_hash():
    """Stable per-browser library owner; falls back to the legacy scope."""
    from flask import request, current_app

    fresh = request.environ.get("lib.new_identity")
    if fresh:
        return f"lib:{fresh}"
    raw = request.cookies.get(COOKIE, "")
    if raw and "." in raw:
        identity, signature = raw.split(".", 1)
        if hmac.compare_digest(signature, _sign(identity)):
            return f"lib:{identity}"
    if current_app.config.get("CLOUDFLARE"):
        return request.environ["dcf.client_hash"]
    from datetime import date

    return f"local:{request.remote_addr}:{date.today().isoformat()}"


def ensure_identity():
    """Mint the owner identity before the request so reads and writes share a scope."""
    from flask import request

    if not request.path.startswith(LIBRARY_PATHS):
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
    return db


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


def create_share(valuation_id):
    rows = _fetchall(
        "SELECT id FROM valuations WHERE id=? AND client_hash=?",
        (valuation_id, caller_hash()),
    )
    if not rows:
        raise ValueError("Valuation not found.")
    token = secrets.token_urlsafe(16)
    _run(
        "INSERT INTO share_links(token,valuation_id,created_at,client_hash)"
        " VALUES (?,?,?,?)",
        (token, valuation_id, now(), caller_hash()),
    )
    return token


def shared_valuation(token):
    rows = _fetchall(
        "SELECT v.assumptions_json,v.financials_json,v.result_json"
        " FROM share_links s JOIN valuations v ON v.id=s.valuation_id"
        " WHERE s.token=?",
        (token,),
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
    """Lazily re-price every watched ticker; never raises per-ticker."""
    from auto_loading import load_method
    from dcf_loader import ProviderError

    asof = datetime.now(timezone.utc).date().isoformat()
    states = []
    for entry in list_watch():
        state = dict(entry)
        try:
            bundle = load_method("dcf", entry["ticker"], asof)
            price = bundle["financials"]["market"]["price"]
            state["price"] = price
            state["price_as_of"] = bundle["financials"]["market"]["price_as_of"]
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
