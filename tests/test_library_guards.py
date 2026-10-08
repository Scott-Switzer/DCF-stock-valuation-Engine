"""Library write guards: cross-site rejection, watchlist cap, rate-limit coverage."""

import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

import library
from app import app


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("DCF_STATE_PATH", str(tmp_path / "library.sqlite3"))


def client(tmp_path):
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))
    return app.test_client()


def test_cross_site_writes_are_rejected(tmp_path):
    c = client(tmp_path)
    body = {"ticker": "AAPL", "target": 200, "direction": "above"}
    forged = c.post("/api/watchlist", json=body, headers={"Origin": "https://evil.example"})
    assert forged.status_code == 403
    fetch_meta = c.post("/api/watchlist", json=body,
                        headers={"Sec-Fetch-Site": "cross-site"})
    assert fetch_meta.status_code == 403
    assert c.get("/api/watchlist").get_json() == []


def test_same_origin_and_non_browser_writes_are_allowed(tmp_path):
    c = client(tmp_path)
    body = {"ticker": "AAPL", "target": 200, "direction": "above"}
    assert c.post("/api/watchlist", json=body,
                  headers={"Origin": "http://localhost"}).status_code == 200
    assert c.post("/api/watchlist", json={"ticker": "MSFT", "target": 1,
                                          "direction": "below"}).status_code == 200


def test_watchlist_is_capped_per_owner(tmp_path, monkeypatch):
    from storage import Store

    # The cap is under test here, not the local write limiter.
    monkeypatch.setattr(Store, "allow", lambda self, key, maximum=10, window=60: True)
    c = client(tmp_path)
    for i in range(library.WATCH_LIMIT):
        symbol = "A" * 1 + chr(ord("A") + i % 26) + chr(ord("A") + i // 26)
        assert c.post("/api/watchlist", json={"ticker": symbol, "target": 1,
                                              "direction": "above"}).status_code == 200
    over = c.post("/api/watchlist", json={"ticker": "ZZZ", "target": 1,
                                          "direction": "above"})
    assert over.status_code == 400
    # Re-saving an existing ticker is an update, not a new entry.
    again = c.post("/api/watchlist", json={"ticker": "AAA", "target": 2,
                                           "direction": "below"})
    assert again.status_code == 200


def test_watch_refresh_stops_after_time_budget(monkeypatch):
    monkeypatch.setattr(library, "list_watch", lambda: [
        {"ticker": "AAA", "target": 1, "direction": "above", "created_at": "x"},
        {"ticker": "BBB", "target": 1, "direction": "above", "created_at": "x"},
    ])
    import auto_loading
    import time as time_module

    clock = iter([0.0, 0.5, 100.0, 100.0])
    monkeypatch.setattr(time_module, "monotonic", lambda: next(clock))
    calls = []

    def fake_load(method, ticker, asof):
        calls.append(ticker)
        return {"financials": {"market": {"price": 5.0, "price_as_of": "2026-10-06"}}}

    monkeypatch.setattr(auto_loading, "load_method", fake_load)
    states = library.check_watch()
    assert calls == ["AAA"]
    assert states[0]["price"] == 5.0
    assert states[1]["price"] is None and "Reload" in states[1]["error"]


@pytest.mark.parametrize("method,path,binding", [
    ("DELETE", "/api/watchlist", "WRITE_LIMIT"),
    ("DELETE", "/api/templates/abc", "WRITE_LIMIT"),
    ("POST", "/mcp", "MCP_LIMIT"),
])
def test_mutations_and_mcp_use_native_limits(method, path, binding):
    limit = Mock(return_value=SimpleNamespace(success=False))
    env = SimpleNamespace(RECORD_SALT="test-only-salt", DB=Mock(),
                          **{binding: SimpleNamespace(limit=limit)})
    modules = {
        "pyodide": SimpleNamespace(),
        "pyodide.ffi": SimpleNamespace(run_sync=lambda r: r,
                                       to_js=lambda v, **k: v),
        "js": SimpleNamespace(Object=SimpleNamespace(fromEntries=None)),
    }
    from app import limit_expensive_work

    previous = app.config.get("CLOUDFLARE")
    app.config["CLOUDFLARE"] = True
    try:
        with patch.dict(sys.modules, modules), app.test_request_context(
            path, method=method, environ_overrides={"workers.env": env}
        ):
            response = limit_expensive_work()
            assert response is not None and response.status_code == 429
            assert limit.call_count == 1
    finally:
        app.config["CLOUDFLARE"] = previous
