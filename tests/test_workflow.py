from app import app


def fake_field(ticker, asof=None, dcf_assumptions=None):
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
