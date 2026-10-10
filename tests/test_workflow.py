from app import app


def fake_field(ticker, asof=None, dcf_assumptions=None, http=None):
    return {
        "ticker": ticker,
        "company_name": "Demo Inc",
        "market_price": 100.0,
        "lanes": [{"label": "DCF intrinsic (today)", "value": 120.0, "upside": 0.2}],
    }


def test_compare_batch_demo_and_bad_ticker(monkeypatch):
    monkeypatch.setattr("app.football_field", fake_field)
    c = app.test_client()
    r = c.post("/api/compare/batch", json={"tickers": ["DEMO", "!!!"]})
    assert r.status_code == 200
    body = r.get_json()
    assert body["asof"]
    assert len(body["results"]) == 2
    assert body["results"][0]["lanes"]
    assert "error" in body["results"][1]


def test_compare_batch_dedupes_tickers_and_keeps_order(monkeypatch):
    calls = []

    def counting_field(ticker, asof=None, dcf_assumptions=None, http=None):
        calls.append(ticker)
        return fake_field(ticker, asof, dcf_assumptions, http)

    monkeypatch.setattr("app.football_field", counting_field)
    body = app.test_client().post(
        "/api/compare/batch", json={"tickers": ["DEMO", "aapl", "DEMO"]}
    ).get_json()
    assert [r["ticker"] for r in body["results"]] == ["DEMO", "AAPL", "DEMO"]
    assert calls == ["DEMO", "AAPL"]
    assert [r["status"] for r in body["results"]] == ["complete"] * 3


def test_compare_batch_deadline_marks_unfinished_tickers(monkeypatch):
    import app as app_module
    import dcf_loader
    from dcf_loader import ProviderError
    from fake_clock import FakeClock

    clock = FakeClock()
    monkeypatch.setattr(dcf_loader, "time", clock.module())
    # Each ticker advances the fake clock 0.3 s against a 0.45 s budget.
    monkeypatch.setattr(app_module, "BATCH_BUDGET_SECONDS", 0.45)

    def slow_field(ticker, asof=None, dcf_assumptions=None, http=None):
        clock.advance(0.3)
        if http.expired():
            raise ProviderError("Data provider exceeded its request deadline.")
        return fake_field(ticker, asof, dcf_assumptions, http)

    monkeypatch.setattr("app.football_field", slow_field)
    body = app.test_client().post(
        "/api/compare/batch", json={"tickers": ["DEMO", "AAPL", "MSFT"]}
    ).get_json()
    statuses = [r["status"] for r in body["results"]]
    assert statuses == ["complete", "timed_out", "not_started"]
    assert "deadline" in body["results"][2]["error"]


def test_compare_batch_rejects_bad_shape():
    c = app.test_client()
    assert c.post("/api/compare/batch", json={"tickers": []}).status_code == 400
    assert c.post("/api/compare/batch", json={"tickers": ["A"] * 9}).status_code == 400
    assert c.post("/api/compare/batch", json={}).status_code == 400


def test_providers_page_and_manifest():
    c = app.test_client()
    page = c.get("/providers")
    assert page.status_code == 200
    assert "Custom company API" in page.get_data(as_text=True)
    manifest = c.get("/.well-known/mcp.json").get_json()
    assert manifest["endpoint"] == "/mcp"
    assert [t["name"] for t in manifest["tools"]] == [
        "value_company", "reverse_dcf", "search_tickers"]
