from app import app


def test_providers_status_has_no_secrets():
    c = app.test_client()
    r = c.get("/api/providers")
    assert r.status_code == 200
    body = r.get_json()
    assert body["providers"]["zion"]["label"].startswith("Custom company API")
    assert body["providers"]["zion"]["kind"] == "custom_private_api"
    text = r.get_data(as_text=True)
    assert "Bearer" not in text
    assert "configured" in text
    # Unconfigured by default in test env.
    assert body["providers"]["zion"]["configured"] is False


def test_ready_uses_server_provider_config(monkeypatch):
    monkeypatch.setenv("ZION_API_BASE_URL", "https://example.com")
    c = app.test_client()
    assert c.get("/ready").get_json()["zion_configured"] is True
