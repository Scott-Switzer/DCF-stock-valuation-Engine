"""MCP endpoint speaks JSON-RPC with three read-only tools."""

from app import app


def rpc(method, params=None, request_id=1):
    return {"jsonrpc": "2.0", "id": request_id, "method": method,
            "params": params or {}}


def client(tmp_path):
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))
    return app.test_client()


def test_initialize_and_list(tmp_path):
    c = client(tmp_path)
    body = c.post("/mcp", json=rpc("initialize")).get_json()
    assert body["result"]["serverInfo"]["name"] == "dcf-valuation-engine"
    assert body["result"]["capabilities"]["tools"]["listChanged"] is False
    tools = c.post("/mcp", json=rpc("tools/list")).get_json()["result"]["tools"]
    assert [t["name"] for t in tools] == [
        "value_company", "reverse_dcf", "search_tickers"]
    assert all(t["inputSchema"]["type"] == "object" for t in tools)


def test_search_tool(tmp_path):
    c = client(tmp_path)
    body = c.post(
        "/mcp",
        json=rpc("tools/call", {"name": "search_tickers",
                                "arguments": {"query": "AAPL"}}),
    ).get_json()
    import json

    assert "AAPL" in body["result"]["content"][0]["text"]
    assert json.loads(body["result"]["content"][0]["text"])


def test_unknown_tool_and_method(tmp_path):
    c = client(tmp_path)
    call = c.post(
        "/mcp", json=rpc("tools/call", {"name": "nope", "arguments": {}})
    ).get_json()
    assert call["result"]["isError"] is True
    missing = c.post("/mcp", json=rpc("bogus/method")).get_json()
    assert missing["error"]["code"] == -32601
    assert c.post("/mcp", json={"nope": True}).get_json()["error"]["code"] == -32600
    assert c.get("/mcp").status_code == 405


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
    body = c.post(
        "/mcp",
        json=rpc("tools/call", {"name": "value_company",
                                "arguments": {"ticker": "DEMO"}}),
    ).get_json()
    import json

    packet = json.loads(body["result"]["content"][0]["text"])
    assert packet["ticker"] == "DEMO"
    assert packet["lanes"][0]["value"] is not None
    assert packet["reverse"]["revenue_growth"]["status"] == "solved"
