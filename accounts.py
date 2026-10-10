"""Email and password accounts with server-side sessions on D1 or local SQLite.

Passwords: PBKDF2-HMAC-SHA256 at 100,000 iterations, the maximum Cloudflare
Workers WebCrypto accepts (a larger count throws at runtime). Session tokens
are 256-bit random values held only in an HttpOnly, Secure cookie; the
database stores their SHA-256 digest.

Limitation: no verification or reset email is sent yet, so an account proves
a password, not control of the mailbox.
"""

import base64
import hashlib
import hmac
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import library

ITERATIONS = 100_000
SESSION_COOKIE = "dcf_session"
SESSION_DAYS = 14
MIN_PASSWORD = 12
MAX_PASSWORD_BYTES = 256
FAILURE = "Email or password is incorrect."
_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[^@\s]{2,24}$")
_dummy = None


def normalize_email(raw):
    if not isinstance(raw, str):
        raise ValueError("Enter an email address.")
    email = raw.strip().lower()
    if len(email) > 254 or not _EMAIL.match(email):
        raise ValueError("Enter a valid email address.")
    return email


def new_password_bytes(raw):
    if not isinstance(raw, str):
        raise ValueError("Enter a password.")
    if len(raw) < MIN_PASSWORD:
        raise ValueError(f"Use at least {MIN_PASSWORD} characters.")
    encoded = raw.encode()
    if len(encoded) > MAX_PASSWORD_BYTES:
        raise ValueError(f"Use at most {MAX_PASSWORD_BYTES} bytes.")
    return encoded


def _b64(data):
    return base64.b64encode(data).decode()


def _pbkdf2(password, salt, iterations):
    from flask import current_app, has_request_context

    if has_request_context() and current_app.config.get("CLOUDFLARE"):
        # WebCrypto is native and keeps CPU time low on Workers.
        import js
        from pyodide.ffi import run_sync, to_js

        key = run_sync(
            js.crypto.subtle.importKey(
                "raw", js.Uint8Array.new(to_js(list(password))), "PBKDF2", False,
                to_js(["deriveBits"]),
            )
        )
        params = to_js(
            {
                "name": "PBKDF2",
                "hash": "SHA-256",
                "salt": js.Uint8Array.new(to_js(list(salt))),
                "iterations": iterations,
            },
            dict_converter=js.Object.fromEntries,
        )
        bits = run_sync(js.crypto.subtle.deriveBits(params, key, 256))
        return bytes(js.Uint8Array.new(bits).to_py())
    return hashlib.pbkdf2_hmac("sha256", password, salt, iterations, 32)


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = _pbkdf2(password, salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${_b64(salt)}${_b64(digest)}"


def verify_password(password, stored):
    try:
        scheme, raw_iterations, salt_b64, digest_b64 = stored.split("$")
        iterations = int(raw_iterations)
        salt = base64.b64decode(salt_b64, validate=True)
        expected = base64.b64decode(digest_b64, validate=True)
    except (ValueError, TypeError):
        return False
    if scheme != "pbkdf2_sha256" or not 1 <= iterations <= ITERATIONS:
        return False
    return hmac.compare_digest(_pbkdf2(password, salt, iterations), expected)


def _dummy_hash():
    """Spend the same hashing time for unknown emails as for real ones."""
    global _dummy
    if _dummy is None:
        _dummy = hash_password(secrets.token_bytes(16))
    return _dummy


def _digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _now():
    return datetime.now(timezone.utc)


def signup(email_raw, password_raw, anonymous=None):
    email = normalize_email(email_raw)
    password = new_password_bytes(password_raw)
    if library._fetchall("SELECT id FROM users WHERE email=?", (email,)):
        raise ValueError("That email already has an account. Sign in instead.")
    user_id = str(uuid.uuid4())
    try:
        library._run(
            "INSERT INTO users(id,email,password_hash,created_at) VALUES (?,?,?,?)",
            (user_id, email, hash_password(password), library.now()),
        )
    except Exception as exc:
        # Two concurrent signups can both pass the SELECT above; the UNIQUE
        # constraint then decides. Only that failure becomes the friendly message.
        if library.is_unique_violation(exc):
            raise ValueError("That email already has an account. Sign in instead.") from None
        raise
    claim_anonymous(anonymous, f"user:{user_id}")
    return user_id, email


def login(email_raw, password_raw, anonymous=None):
    try:
        email = normalize_email(email_raw)
    except ValueError:
        email = ""
    raw = password_raw if isinstance(password_raw, str) else ""
    if len(raw.encode()) > MAX_PASSWORD_BYTES:
        raise ValueError(FAILURE)
    rows = library._fetchall("SELECT id,email,password_hash FROM users WHERE email=?", (email,))
    stored = rows[0]["password_hash"] if rows else _dummy_hash()
    ok = verify_password(raw.encode(), stored)
    if not rows or not ok:
        raise ValueError(FAILURE)
    user = rows[0]
    claim_anonymous(anonymous, f"user:{user['id']}")
    return user["id"], user["email"]


def change_password(user_id, current_raw, new_raw):
    """Rotate the password and revoke every other session for this account."""
    new = new_password_bytes(new_raw)
    current = current_raw.encode() if isinstance(current_raw, str) else b""
    if len(current) > MAX_PASSWORD_BYTES:
        raise ValueError("Current password is incorrect.")
    rows = library._fetchall("SELECT password_hash FROM users WHERE id=?", (user_id,))
    if not rows or not verify_password(current, rows[0]["password_hash"]):
        raise ValueError("Current password is incorrect.")
    library._run(
        "UPDATE users SET password_hash=? WHERE id=?", (hash_password(new), user_id)
    )
    library._run(
        "DELETE FROM sessions WHERE user_id=? AND token_hash<>?",
        (user_id, current_token_digest() or ""),
    )


def current_token_digest():
    """Digest of this request's session cookie, or None when absent."""
    from flask import request

    token = request.cookies.get(SESSION_COOKIE, "")
    return _digest(token) if token and len(token) <= 200 else None


def start_session(user_id):
    token = secrets.token_urlsafe(32)
    now = _now()
    library._run("DELETE FROM sessions WHERE expires_at<?", (now.isoformat(),))
    library._run(
        "INSERT INTO sessions(token_hash,user_id,created_at,expires_at) VALUES (?,?,?,?)",
        (_digest(token), user_id, now.isoformat(),
         (now + timedelta(days=SESSION_DAYS)).isoformat()),
    )
    return token


def current_user():
    """The signed-in account for this request, cached per request."""
    from flask import has_request_context, request

    if not has_request_context():
        return None
    cached = request.environ.get("dcf.account")
    if cached is not None:
        return cached or None
    token = request.cookies.get(SESSION_COOKIE, "")
    user = None
    if token and len(token) <= 200:
        rows = library._fetchall(
            "SELECT u.id,u.email,u.created_at,s.expires_at FROM sessions s"
            " JOIN users u ON u.id=s.user_id WHERE s.token_hash=?",
            (_digest(token),),
        )
        if rows and rows[0]["expires_at"] > _now().isoformat():
            user = {k: rows[0][k] for k in ("id", "email", "created_at")}
    request.environ["dcf.account"] = user or False
    return user


def owner_hash():
    """Library owner for signed-in requests; no database read without a cookie."""
    from flask import request

    if not request.cookies.get(SESSION_COOKIE):
        return None
    user = current_user()
    return f"user:{user['id']}" if user else None


def end_session():
    from flask import request

    token = request.cookies.get(SESSION_COOKIE, "")
    if token and len(token) <= 200:
        library._run("DELETE FROM sessions WHERE token_hash=?", (_digest(token),))
    request.environ["dcf.account"] = False


def claim_anonymous(anonymous, owner):
    """Move an unclaimed browser library into the account; conflicts stay put."""
    if not anonymous or not owner or anonymous == owner:
        return
    for table in ("valuations", "templates", "watchlist", "share_links"):
        library._run(
            f"UPDATE OR IGNORE {table} SET client_hash=? WHERE client_hash=?",
            (owner, anonymous),
        )


def set_session_cookie(response, token):
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_DAYS * 24 * 3600,
        path="/",
        httponly=True,
        secure=True,
        samesite="Lax",
    )
    return response


def clear_session_cookie(response):
    response.delete_cookie(
        SESSION_COOKIE, path="/", httponly=True, secure=True, samesite="Lax"
    )
    return response
