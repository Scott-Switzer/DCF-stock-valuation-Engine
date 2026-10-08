"""Model Context Protocol endpoint: let LLMs value companies directly.

Dual-era Streamable HTTP JSON-RPC server with three read-only tools.

- Modern revision 2026-07-28: stateless. Every POST carries
  MCP-Protocol-Version, Mcp-Method (and Mcp-Name for tools/call) plus
  matching _meta. server/discover reports capabilities and versions.
- Legacy revision 2025-06-18: an initialize handshake, then requests carry
  MCP-Protocol-Version: 2025-06-18 and are served statelessly.

Every number comes from the audited engines; the model never computes.
"""

import base64
import binascii
import json
import logging

PROTOCOL_VERSION = "2026-07-28"
LEGACY_VERSION = "2025-06-18"
SUPPORTED_VERSIONS = [PROTOCOL_VERSION, LEGACY_VERSION]
SERVER_INFO = {"name": "dcf-valuation-engine", "version": "1.0.0"}
META_VERSION = "io.modelcontextprotocol/protocolVersion"
META_SERVER_INFO = "io.modelcontextprotocol/serverInfo"
LIST_TTL_MS = 300_000
INSTRUCTIONS = (
    "Value companies with the audited DCF, DDM and relative engines. Quote tool "
    "output as-is; never recompute valuations or infer missing financials."
)

INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
HEADER_MISMATCH = -32020
UNSUPPORTED_VERSION = -32022

TOOLS = [
    {
        "name": "value_company",
        "title": "Value a company",
        "description": (
            "Run a baseline DCF football-field valuation for a stock ticker: "
            "DCF intrinsic and 12-month target, DDM lanes when dividends exist, "
            "relative target from peers, bear/base/bull band, reverse-DCF "
            "implied growth, and top assumption drivers. All figures use "
            "audited server-side models on sourced snapshots."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker, e.g. AAPL or BRK-B",
                }
            },
            "required": ["ticker"],
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "reverse_dcf",
        "title": "Reverse DCF",
        "description": (
            "Solve for the uniform revenue growth or EBIT margin the market "
            "price implies, holding other DCF assumptions fixed. Reports "
            "below_range/above_range/unsolvable explicitly."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker"},
                "driver": {
                    "type": "string",
                    "description": "revenue_growth or ebit_margin",
                },
            },
            "required": ["ticker"],
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "search_tickers",
        "title": "Search tickers",
        "description": "Find supported ticker symbols by company name or symbol prefix.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Name or symbol fragment"},
            },
            "required": ["query"],
        },
        "annotations": {"readOnlyHint": True},
    },
]


def _decode_header(value):
    """Mcp-Name / Mcp-Param values may use the Base64 sentinel form."""
    if value is None:
        return None
    if value.startswith("=?base64?") and value.endswith("?="):
        try:
            return base64.b64decode(value[len("=?base64?"):-2], validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            return None
    return value


def origin_allowed(origin, host_origin, allowlist=()):
    """Missing Origin is a non-browser client. Present Origin must be trusted."""
    if origin is None:
        return True
    trusted = {host_origin.lower(), *(o.strip().lower() for o in allowlist if o.strip())}
    return origin.strip().lower() in trusted


def _ok(request_id, result):
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _fail(request_id, code, message, data=None):
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def _text(payload):
    return {
        "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
        "isError": False,
    }


def serve(message, headers, *, origin=None, host_origin="", allowed_origins=()):
    """Validate HTTP-level rules, then dispatch. Returns (status, body or None)."""
    if not origin_allowed(origin, host_origin, allowed_origins):
        return 403, _fail(None, INVALID_REQUEST, "Origin is not allowed for this endpoint.")
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or not isinstance(
        message.get("method"), str
    ):
        return 400, _fail(None, INVALID_REQUEST, "Send a JSON-RPC 2.0 request.")
    method = message["method"]
    request_id = message.get("id")
    if "id" not in message:
        # Notifications (for example notifications/initialized) need no response body.
        return 202, None
    params = message.get("params") if isinstance(message.get("params"), dict) else {}
    version = headers.get("mcp-protocol-version")

    if method == "initialize":
        # Legacy handshake: no version header yet; negotiate the one legacy revision.
        return 200, _ok(request_id, {
            "protocolVersion": LEGACY_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
            "instructions": INSTRUCTIONS,
        })
    if version is None:
        return 400, _fail(request_id, HEADER_MISMATCH,
                          "The MCP-Protocol-Version header is required.")
    if version not in SUPPORTED_VERSIONS:
        return 400, _fail(request_id, UNSUPPORTED_VERSION, "Unsupported protocol version.",
                          {"supported": SUPPORTED_VERSIONS, "requested": version})
    if version == LEGACY_VERSION:
        return _dispatch(method, request_id, params, modern=False)

    # Modern revision: every header must agree with the body.
    meta = params.get("_meta")
    if not isinstance(meta, dict) or META_VERSION not in meta:
        return 400, _fail(request_id, INVALID_PARAMS,
                          "Modern requests must carry _meta protocolVersion.")
    if meta[META_VERSION] != version:
        return 400, _fail(request_id, HEADER_MISMATCH,
                          "The _meta protocolVersion does not match the header.")
    if headers.get("mcp-method") is None:
        return 400, _fail(request_id, HEADER_MISMATCH, "The Mcp-Method header is required.")
    if headers["mcp-method"] != method:
        return 400, _fail(request_id, HEADER_MISMATCH,
                          "The Mcp-Method header does not match the request method.")
    if method == "tools/call":
        if _decode_header(headers.get("mcp-name")) != params.get("name"):
            return 400, _fail(request_id, HEADER_MISMATCH,
                              "The Mcp-Name header does not match the tool name.")
    return _dispatch(method, request_id, params, modern=True)


def _dispatch(method, request_id, params, *, modern):
    if method == "server/discover" and modern:
        return 200, _ok(request_id, {
            "resultType": "complete",
            "supportedVersions": SUPPORTED_VERSIONS,
            "capabilities": {"tools": {"listChanged": False}},
            "_meta": {META_SERVER_INFO: SERVER_INFO},
            "instructions": INSTRUCTIONS,
            "ttlMs": 3_600_000,
            "cacheScope": "public",
        })
    if method == "ping":
        return 200, _ok(request_id, {})
    if method == "tools/list":
        result = {"tools": TOOLS}
        if modern:
            result.update(resultType="complete", ttlMs=LIST_TTL_MS, cacheScope="public")
        return 200, _ok(request_id, result)
    if method == "tools/call":
        try:
            result = call_tool(params.get("name"), params.get("arguments") or {})
        except ValueError as exc:
            result = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        except Exception:
            logging.getLogger(__name__).error("MCP tool failure", exc_info=True)
            result = {"content": [{"type": "text", "text": "The tool could not complete. Try again."}],
                      "isError": True}
        if modern:
            result["resultType"] = "complete"
        return 200, _ok(request_id, result)
    # Unknown methods: modern clients get 404 per the transport spec.
    return (404 if modern else 200), _fail(request_id, METHOD_NOT_FOUND,
                                            f"Unknown method: {method}.")


def call_tool(name, arguments):
    from dcf_loader import ProviderError, ticker_symbol

    asof = __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc).date().isoformat()
    if name == "search_tickers":
        from app import tickers

        query = str(arguments.get("query", "")).strip().upper()[:50]
        matches = [r for r in tickers()
                   if query in r["symbol"] or query in r["shortname"].upper()]
        matches.sort(key=lambda r: (r["symbol"] != query, r["symbol"]))
        return _text(matches[:12])
    if name == "value_company":
        from compare import football_field

        try:
            packet = football_field(
                ticker_symbol(arguments.get("ticker", "")), asof)
        except (ProviderError, ValueError) as exc:
            raise ValueError(str(exc)) from None
        return _text({
            "ticker": packet["ticker"],
            "company": packet["company_name"],
            "market_price": packet["market_price"],
            "lanes": [
                {"label": lane["label"], "value": lane["value"],
                 "upside": lane.get("upside"), "detail": lane["detail"],
                 "band": lane.get("band")}
                for lane in packet["lanes"]
            ],
            "reverse": packet.get("reverse"),
            "drivers": packet.get("drivers"),
            "method_notes": packet.get("method_notes"),
            "using_baselines": not packet.get("custom"),
        })
    if name == "reverse_dcf":
        from auto_loading import load_method
        from compare import coerce_dcf_assumptions
        from reverse_dcf import solve

        try:
            symbol = ticker_symbol(arguments.get("ticker", ""))
            bundle = load_method("dcf", symbol, asof)
            doc = bundle["financials"]
            wacc = bundle["load_summary"].get("capital_costs", {}).get("wacc") or 0.065
            assumptions, _ = coerce_dcf_assumptions(doc, None, wacc)
            driver = arguments.get("driver") or "revenue_growth"
            return _text(solve(doc, assumptions, doc["market"]["price"], driver))
        except (ProviderError, ValueError) as exc:
            raise ValueError(str(exc)) from None
    raise ValueError(f"Unknown tool: {name}.")
