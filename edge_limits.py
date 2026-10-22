"""Edge rate limiting applied in the async Worker entrypoint.

The Flask ``before_request`` hook runs synchronously, so it cannot await the Cloudflare
rate-limit binding and its checks are not enforced. The same rules are applied here,
before the WSGI app runs, where the binding call can be awaited.
"""

import hashlib
import hmac
from datetime import datetime, timezone
from urllib.parse import urlsplit

from workers import Response

REFERENCE_PREFIXES = (
    "/api/references/",
    "/api/guidance/",
    "/api/company/",
    "/api/data/",
    "/api/providers",
    "/api/diag/",
    "/coverage/",
)
MUTATIONS = {"POST", "PUT", "PATCH", "DELETE"}


def request_method(value):
    """Cloudflare's Request exposes an HTTPMethod enum, not the plain string Werkzeug sees."""
    inner = getattr(value, "value", value)
    text = str(inner)
    if not text.isalpha():
        text = text.strip("<>").rsplit(".", 1)[-1]
    return text.upper()


def binding_name(path, method):
    """Return the rate-limit binding that governs this request, or None if unlimited."""
    method = request_method(method)
    if method == "POST" and path.rstrip("/") == "/mcp":
        return "MCP_LIMIT"
    if method == "POST" and path.startswith("/api/preview/"):
        return "PREVIEW_LIMIT"
    if method == "GET" and (
        path.startswith(REFERENCE_PREFIXES)
        or (path.startswith("/research/") and path.endswith("/export/xlsx"))
    ):
        return "REFERENCE_LIMIT"
    if method in MUTATIONS:
        return "WRITE_LIMIT"
    return None


def limited_response():
    return Response(
        "Too many requests. Try again in one minute.",
        status=429,
        headers={
            "Content-Type": "text/plain; charset=utf-8",
            "Retry-After": "60",
            "Cache-Control": "no-store",
        },
    )


def client_key(env, request):
    """Daily salted client key; no IP or credential is stored or returned."""
    client = request.headers.get("CF-Connecting-IP") or "unknown"
    salt = getattr(env, "RECORD_SALT", "") or ""
    digest = hmac.new(
        str(salt).encode(),
        f"{datetime.now(timezone.utc).date()}:edge:{client}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return "dcf:edge:" + digest


async def enforce(env, request):
    """Return a 429 response when this client exceeded its binding, else None.

    A binding that is missing or that errors is treated as unenforced rather than as a
    failure, so a limiter problem never takes the site down; staging logs the reason.
    """
    path = urlsplit(request.url).path
    name = binding_name(path, request_method(request.method))
    if not name:
        return None
    binding = getattr(env, name, None)
    if binding is None:
        return None
    try:
        result = await binding.limit({"key": client_key(env, request)})
    except Exception as error:  # noqa: BLE001 - unenforced is safer than unavailable
        if str(getattr(env, "DEPLOY_ENVIRONMENT", "")) == "staging":
            print("edge_limit_error", name, type(error).__name__, str(error)[:200])
        return None
    if not getattr(result, "success", True):
        return limited_response()
    return None
