"""MCP endpoint: dual-era Streamable HTTP with three read-only tools."""

import base64
import json

import pytest

from app import app

MODERN = "2026-07-28"
LEGACY = "2025-06-18"


def rpc(method, params=None, request_id=1):
    return {"jsonrpc": "2.0", "id": request_id, "method": method,
            "params": params or {}}


def client(tmp_path):
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))
    return app.test_client()


def modern(c, method, params=None, *, headers=None, request_id=1):
    """POST a modern request with the headers and _meta the spec requires."""
    params = dict(params or {})
    params["_meta"] = {
        "io.modelcontextprotocol/protocolVersion": MODERN,
        "io.modelcontextprotocol/clientInfo": {"name": "test", "version": "1"},
        "io.modelcontextprotocol/clientCapabilities": {},
    }
    sent = {"MCP-Protocol-Version": MODERN, "Mcp-Method": method}
    if method == "tools/call":
        sent["Mcp-Name"] = params.get("name", "")
    for key, value in (headers or {}).items():
        if value is None:
            sent.pop(key, None)
        else:
            sent[key] = value
    return c.post("/mcp", json=rpc(method, params, request_id), headers=sent)


def legacy(c, method, params=None, request_id=1):
    return c.post(
        "/mcp", json=rpc(method, params, request_id),
        headers={"MCP-Protocol-Version": LEGACY},
    )


def test_legacy_initialize_then_list(tmp_path):
    c = client(tmp_path)
    init = c.post("/mcp", json=rpc("initialize", {"protocolVersion": LEGACY})).get_json()
    assert init["result"]["protocolVersion"] == LEGACY
    assert init["result"]["serverInfo"]["name"] == "dcf-valuation-engine"
    assert init["result"]["capabilities"]["tools"]["listChanged"] is False
    tools = legacy(c, "tools/list").get_json()["result"]
    assert "resultType" not in tools
    assert [t["name"] for t in tools["tools"]] == [
        "value_company", "reverse_dcf", "search_tickers"]
    assert all(t["inputSchema"]["type"] == "object" for t in tools["tools"])


def test_modern_discover_lists_versions(tmp_path):
    c = client(tmp_path)
    res = modern(c, "server/discover").get_json()["result"]
    assert res["resultType"] == "complete"
    assert MODERN in res["supportedVersions"]
    assert res["_meta"]["io.modelcontextprotocol/serverInfo"]["name"] == "dcf-valuation-engine"
    assert res["cacheScope"] == "public" and res["ttlMs"] > 0


def test_modern_tools_list_is_cacheable(tmp_path):
    c = client(tmp_path)
    res = modern(c, "tools/list").get_json()["result"]
    assert res["resultType"] == "complete"
    assert res["ttlMs"] == 300_000 and res["cacheScope"] == "public"
    assert [t["name"] for t in res["tools"]] == [
        "value_company", "reverse_dcf", "search_tickers"]


def test_modern_search_tool_with_matching_name_header(tmp_path):
    c = client(tmp_path)
    body = modern(c, "tools/call", {"name": "search_tickers",
                                    "arguments": {"query": "AAPL"}}).get_json()
    assert body["result"]["resultType"] == "complete"
    assert json.loads(body["result"]["content"][0]["text"])


def test_mcp_name_accepts_base64_sentinel(tmp_path):
    c = client(tmp_path)
    encoded = "=?base64?" + base64.b64encode(b"search_tickers").decode() + "?="
    res = modern(c, "tools/call", {"name": "search_tickers", "arguments": {"query": "A"}},
                 headers={"Mcp-Name": encoded})
    assert res.status_code == 200


@pytest.mark.parametrize("headers, code", [
    ({"Mcp-Method": None}, -32020),
    ({"Mcp-Method": "tools/call"}, -32020),
    ({"Mcp-Name": "value_company"}, -32020),
])
def test_modern_header_mismatches_are_rejected(tmp_path, headers, code):
    c = client(tmp_path)
    if "Mcp-Name" in headers:
        res = modern(c, "tools/call", {"name": "search_tickers", "arguments": {"query": "A"}},
                     headers=headers)
    else:
        res = modern(c, "tools/list", headers=headers)
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == code


def test_modern_body_meta_must_match_version_header(tmp_path):
    c = client(tmp_path)
    res = c.post(
        "/mcp",
        json=rpc("tools/list", {"_meta": {
            "io.modelcontextprotocol/protocolVersion": LEGACY}}),
        headers={"MCP-Protocol-Version": MODERN, "Mcp-Method": "tools/list"},
    )
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == -32020


def test_unsupported_version_lists_supported_versions(tmp_path):
    c = client(tmp_path)
    res = c.post("/mcp", json=rpc("tools/list"),
                 headers={"MCP-Protocol-Version": "1900-01-01"})
    assert res.status_code == 400
    error = res.get_json()["error"]
    assert error["code"] == -32022
    assert error["data"]["supported"] == [MODERN, LEGACY]


def test_headerless_non_initialize_request_is_rejected(tmp_path):
    c = client(tmp_path)
    res = c.post("/mcp", json=rpc("tools/list"))
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == -32020


def test_unknown_method_status_depends_on_era(tmp_path):
    c = client(tmp_path)
    modern_missing = modern(c, "bogus/method")
    assert modern_missing.status_code == 404
    assert modern_missing.get_json()["error"]["code"] == -32601
    legacy_missing = legacy(c, "bogus/method")
    assert legacy_missing.get_json()["error"]["code"] == -32601


def test_origin_rules(tmp_path, monkeypatch):
    c = client(tmp_path)
    monkeypatch.setenv("MCP_ALLOWED_ORIGINS", "https://claude.example")
    evil = c.post("/mcp", json=rpc("ping"), headers={
        "MCP-Protocol-Version": LEGACY, "Origin": "https://evil.example"})
    assert evil.status_code == 403
    same = c.post("/mcp", json=rpc("ping"), headers={
        "MCP-Protocol-Version": LEGACY, "Origin": "http://localhost"})
    assert same.status_code == 200
    absent = c.post("/mcp", json=rpc("ping"), headers={"MCP-Protocol-Version": LEGACY})
    assert absent.status_code == 200


def test_notifications_return_202_without_body(tmp_path):
    c = client(tmp_path)
    res = c.post("/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                 headers={"MCP-Protocol-Version": LEGACY})
    assert res.status_code == 202 and res.data == b""


def test_batches_and_bad_envelopes_are_rejected(tmp_path):
    c = client(tmp_path)
    batch = c.post("/mcp", json=[rpc("ping")], headers={"MCP-Protocol-Version": LEGACY})
    assert batch.status_code == 400
    bad = c.post("/mcp", json={"nope": True}, headers={"MCP-Protocol-Version": LEGACY})
    assert bad.status_code == 400 and bad.get_json()["error"]["code"] == -32600


def test_get_and_delete_are_not_supported(tmp_path):
    c = client(tmp_path)
    assert c.get("/mcp").status_code == 405
    assert c.delete("/mcp").status_code == 405


def test_unknown_tool_is_tool_error(tmp_path):
    c = client(tmp_path)
    call = modern(c, "tools/call", {"name": "nope", "arguments": {}}).get_json()
    assert call["result"]["isError"] is True


def test_value_tool_against_demo_snapshot(monkeypatch, tmp_path):
    from dcf_loader import demo_document
    import auto_loading
    from copy import deepcopy

    doc = demo_document()

    def fake_load(method, ticker, asof=None, **kwargs):
        return {"financials": deepcopy(doc), "form": {}, "warnings": [],
                "load_summary": {"capital_costs": {"wacc": 0.065,
                                                  "cost_of_equity": 0.07},
                                 "elapsed_seconds": 0.1, "peer_count": 0}}

    monkeypatch.setattr(auto_loading, "load_method", fake_load)
    c = client(tmp_path)
    body = modern(c, "tools/call", {"name": "value_company",
                                    "arguments": {"ticker": "DEMO"}}).get_json()
    packet = json.loads(body["result"]["content"][0]["text"])
    assert packet["ticker"] == "DEMO"
    assert packet["lanes"][0]["value"] is not None
    assert packet["reverse"]["revenue_growth"]["status"] == "solved"
