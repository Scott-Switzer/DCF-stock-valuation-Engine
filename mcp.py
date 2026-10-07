"""Model Context Protocol endpoint: let LLMs value companies directly.

Minimal stateless Streamable-HTTP-compatible JSON-RPC surface:
initialize, tools/list and tools/call with three read-only tools.
Every number comes from the audited engines; the model never computes.
"""

PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "dcf-valuation-engine", "version": "1.0.0"}

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


def _ok(request_id, result):
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _fail(request_id, code, message):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _text(payload):
    import json

    return {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
            "isError": False}


def handle(message):

    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return _fail(None, -32600, "Send a JSON-RPC 2.0 object.")
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}
    if method == "initialize":
        return _ok(request_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
        })
    if method in {"notifications/initialized", "notifications/cancelled"}:
        return None
    if method == "tools/list":
        return _ok(request_id, {"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        try:
            return _ok(request_id, call_tool(name, arguments))
        except ValueError as exc:
            return _ok(request_id, {
                "content": [{"type": "text", "text": str(exc)}], "isError": True,
            })
        except Exception:
            import logging

            logging.getLogger(__name__).error("MCP tool failure", exc_info=True)
            return _ok(request_id, {
                "content": [{"type": "text",
                             "text": "The tool could not complete. Try again."}],
                "isError": True,
            })
    if method == "ping":
        return _ok(request_id, {})
    return _fail(request_id, -32601, f"Unknown method: {method}.")


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
