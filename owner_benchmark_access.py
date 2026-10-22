"""Owner authorization for private benchmark lookup, separate from upstream credentials.

Local offline research retains its existing behavior. Hosted/production requests
must supply the owner's incoming bearer or a short, account-bound browser grant.
No email, account role, server credential or public login implies owner access.
"""

import base64
import hashlib
import hmac
import json
import time

from flask import current_app, g, has_app_context, has_request_context, jsonify, request

GRANT_COOKIE = "__Host-dcf_owner_benchmarks"
GRANT_SECONDS = 15 * 60


class OwnerBenchmarkAuthRequired(Exception):
    """Intentionally not ValueError: public calculation handlers must not swallow this."""


def _bearer_valid(provider):
    expected = provider("ZION_OWNER_DATA_TOKEN") or ""
    incoming = request.headers.get("Authorization", "")
    if (not expected or not incoming.startswith("Bearer ") or len(incoming) > 4096
            or any(ord(c) < 33 or ord(c) == 127 for c in incoming[7:])):
        return False
    return hmac.compare_digest(incoming[7:].encode(), expected.encode())


def _same_origin():
    from library import same_origin_request

    return same_origin_request() and request.headers.get("Sec-Fetch-Site") not in {
        "cross-site", "same-site"
    }


def _grant_key(provider):
    salt = provider("RECORD_SALT") or ""
    owner = provider("ZION_OWNER_DATA_TOKEN") or ""
    if not salt or not owner:
        return None
    # Domain separation and owner credential rotation both invalidate old grants.
    context = b"dcf-owner-benchmark-grant-v1:" + hashlib.sha256(owner.encode()).digest()
    return hmac.new(salt.encode(), context, hashlib.sha256).digest()


def _grant_valid(provider):
    raw = request.cookies.get(GRANT_COOKIE, "")
    key = _grant_key(provider)
    if not raw or len(raw) > 2048 or key is None or not _same_origin():
        return False
    try:
        body, signature = raw.split(".")
        expected = hmac.new(key, body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return False
        payload = json.loads(base64.urlsafe_b64decode(body))
        now = int(time.time())
        if (payload.get("v") != 1 or type(payload.get("exp")) is not int
                or not now < payload["exp"] <= now + GRANT_SECONDS):
            return False
        from accounts import current_user

        user = current_user()
        return bool(user and payload.get("user_id") == user["id"])
    except (ValueError, KeyError, TypeError, UnicodeError):
        return False


def require_owner_benchmark_access(provider):
    """Run before either remote/local source resolution, including their caches."""
    protected = bool(has_app_context() and current_app.config.get("CLOUDFLARE")) or (
        (provider("DEPLOY_ENVIRONMENT") or "").lower() in {"production", "prod"}
    )
    if not protected:
        return
    if not has_request_context():
        raise OwnerBenchmarkAuthRequired()
    # An explicitly invalid bearer cannot fall back to a cookie grant.
    authorized = _bearer_valid(provider) if request.headers.get("Authorization") else (
        _grant_valid(provider)
    )
    if not authorized:
        raise OwnerBenchmarkAuthRequired()
    g.owner_benchmark_private_response = True


def install_owner_benchmark_access(app, provider):
    """Attach a minimal grant endpoint and sanitized auth/cache policy handlers."""
    @app.errorhandler(OwnerBenchmarkAuthRequired)
    def unauthorized(error):
        response = jsonify(
            code="OWNER_BENCHMARK_AUTH_REQUIRED",
            error="Owner authorization is required for private benchmark inputs.",
        )
        response.status_code = 401
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["WWW-Authenticate"] = 'Bearer realm="owner-benchmarks"'
        return response

    @app.after_request
    def private_response(response):
        if getattr(g, "owner_benchmark_private_response", False):
            response.headers["Cache-Control"] = "private, no-store"
            response.vary.add("Authorization")
            response.vary.add("Cookie")
        return response

    @app.post("/api/account/data-access")
    def grant():
        if not _same_origin():
            return jsonify(error="Cross-site writes are not allowed."), 403
        from accounts import current_user

        user = current_user()
        if not user or not _bearer_valid(provider):
            raise OwnerBenchmarkAuthRequired()
        key = _grant_key(provider)
        if key is None:
            return jsonify(code="OWNER_GRANT_UNAVAILABLE", error="Owner grant unavailable."), 503
        expiry = int(time.time()) + GRANT_SECONDS
        payload = dict(v=1, user_id=user["id"], exp=expiry)
        body = base64.urlsafe_b64encode(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).decode()
        token = body + "." + hmac.new(key, body.encode(), hashlib.sha256).hexdigest()
        response = jsonify(owner_benchmark_access=True, expires_at=expiry)
        response.set_cookie(
            GRANT_COOKIE, token, max_age=GRANT_SECONDS, secure=True, httponly=True,
            samesite="Strict", path="/",
        )
        g.owner_benchmark_private_response = True
        return response


    @app.delete("/api/account/data-access")
    def revoke():
        # Revocation is available even after logout or loss/rotation of the owner key.
        # Preserve the same origin boundary used to mint the grant.
        if not _same_origin():
            response = jsonify(error="Cross-site writes are not allowed.")
            response.status_code = 403
            response.headers["Cache-Control"] = "private, no-store"
            return response
        response = jsonify(owner_benchmark_access=False)
        response.delete_cookie(
            GRANT_COOKIE, secure=True, httponly=True, samesite="Strict", path="/",
        )
        g.owner_benchmark_private_response = True
        return response
