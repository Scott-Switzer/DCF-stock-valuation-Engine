"""Owner authorization precedes every private benchmark source/cache lookup."""

import pytest

import app as views


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setitem(views.app.config, "TESTING", True)
    monkeypatch.setitem(views.app.config, "CLOUDFLARE", False)
    monkeypatch.setitem(views.app.config, "STATE_PATH", str(tmp_path / "state.sqlite"))
    monkeypatch.setenv("DCF_STATE_PATH", str(tmp_path / "library.sqlite"))
    monkeypatch.setenv("DEPLOY_ENVIRONMENT", "production")
    monkeypatch.setenv("ZION_HISTORY_TOKEN", "owner-test-secret")
    monkeypatch.setenv("ZION_BENCHMARK_TOKEN", "upstream-only-secret")
    monkeypatch.setenv("RECORD_SALT", "test-signing-salt")
    return views.app.test_client()


def selection(source="release"):
    return {"wacc": {"release_id": "a" * 64, "subject": "Synthetic", "measure": "wacc",
                     "mode": "historical", "source": source}}


@pytest.mark.parametrize("source", ["zion", "release"])
@pytest.mark.parametrize("authorization", [None, "Bearer wrong", "Bearer upstream-only-secret"])
def test_no_private_source_or_cache_lookup_without_incoming_owner(
    client, monkeypatch, source, authorization
):
    calls = []
    monkeypatch.setattr("valuation_benchmarks.load_benchmark", lambda *a, **k: calls.append(a))
    monkeypatch.setattr("zion_benchmark_provider.fetch_benchmark_row", lambda *a, **k: calls.append(a))
    from owner_benchmark_access import OwnerBenchmarkAuthRequired

    headers = {"Authorization": authorization} if authorization else {}
    with views.app.test_request_context("/api/calculate", headers=headers):
        with pytest.raises(OwnerBenchmarkAuthRequired):
            views.resolve_benchmark_selections(selection(source), "2026-10-19")
    assert not calls


def test_valid_owner_bearer_can_read_local_private_release(client, monkeypatch):
    monkeypatch.setenv("DAMODARAN_RELEASE_ROOT", "/unused")
    monkeypatch.setattr("valuation_benchmarks.load_benchmark", lambda *a, **k: {"value_decimal": "0.1"})
    with views.app.test_request_context("/api/calculate", headers={
        "Authorization": "Bearer owner-test-secret"
    }):
        assert views.resolve_benchmark_selections(selection(), "2026-10-19") == {
            "wacc": {"value_decimal": "0.1"}
        }


def test_public_route_returns_explicit_401_before_source_read(client, monkeypatch):
    def never(*args, **kwargs):
        raise AssertionError("Private source must not be read")

    monkeypatch.setattr("valuation_benchmarks.load_benchmark", never)
    response = client.get("/api/assumptions/damodaran/" + "a" * 64 + "?subject=x&measure=wacc")
    assert response.status_code == 401
    assert response.get_json()["code"] == "OWNER_BENCHMARK_AUTH_REQUIRED"
    assert "secret" not in response.get_data(as_text=True)
    assert "no-store" in response.headers["Cache-Control"]


def test_manual_numeric_dcf_remains_public(client):
    from dcf_loader import demo_document

    response = client.post("/api/calculate", json={
        "financials": demo_document(),
        "assumptions": {"revenue_growth_rates": [0.05] * 5, "terminal_growth_rate": 0.02,
                        "wacc_override": 0.10},
    })
    assert response.status_code == 200, response.get_json()
    assert "intrinsic_value" in response.get_json()


def test_public_sec_packet_remains_public(client, monkeypatch):
    packet = {"source": "public-sec", "ticker": "TEST"}
    monkeypatch.setattr("ppe_provider.load_packet", lambda *a, **k: packet)
    response = client.get("/api/company/TEST")
    assert response.status_code == 200
    assert response.get_json() == packet


def test_browser_grant_requires_login_owner_bearer_and_same_origin(client, monkeypatch):
    monkeypatch.setattr("accounts.current_user", lambda: None)
    assert client.post("/api/account/data-access", headers={
        "Authorization": "Bearer owner-test-secret"
    }).status_code == 401
    monkeypatch.setattr("accounts.current_user", lambda: {"id": "account-1"})
    assert client.post("/api/account/data-access").status_code == 401
    assert client.post("/api/account/data-access", headers={
        "Authorization": "Bearer owner-test-secret", "Origin": "https://other.test"
    }).status_code == 403
    response = client.post("/api/account/data-access", headers={
        "Authorization": "Bearer owner-test-secret", "Origin": "http://localhost"
    })
    assert response.status_code == 200
    cookie = response.headers["Set-Cookie"]
    assert "HttpOnly" in cookie and "Secure" in cookie and "SameSite=Strict" in cookie
    assert "owner-test-secret" not in cookie
    monkeypatch.setenv("DAMODARAN_RELEASE_ROOT", "/unused")
    monkeypatch.setattr("valuation_benchmarks.load_benchmark", lambda *a, **k: {"value_decimal": "0.1"})
    path = "/api/assumptions/damodaran/" + "a" * 64 + "?subject=x&measure=wacc"
    assert client.get(path).status_code == 200
    monkeypatch.setattr("accounts.current_user", lambda: {"id": "different-account"})
    assert client.get(path).status_code == 401
    monkeypatch.setattr("accounts.current_user", lambda: None)
    assert client.get(path).status_code == 401


def test_browser_grant_expires_and_owner_token_rotation_revokes(client, monkeypatch):
    import owner_benchmark_access as access

    monkeypatch.setattr("accounts.current_user", lambda: {"id": "account-1"})
    monkeypatch.setattr(access.time, "time", lambda: 1000000)
    assert client.post("/api/account/data-access", headers={
        "Authorization": "Bearer owner-test-secret"
    }).status_code == 200
    path = "/api/assumptions/damodaran/" + "a" * 64 + "?subject=x&measure=wacc"
    monkeypatch.setattr(access.time, "time", lambda: 1000000 + access.GRANT_SECONDS + 1)
    assert client.get(path).status_code == 401
    monkeypatch.setattr(access.time, "time", lambda: 1000000)
    monkeypatch.setenv("ZION_HISTORY_TOKEN", "rotated-owner-secret")
    assert client.get(path).status_code == 401


def test_local_offline_resolution_remains_available_without_request_context(monkeypatch):
    monkeypatch.delenv("DEPLOY_ENVIRONMENT", raising=False)
    monkeypatch.setenv("DAMODARAN_RELEASE_ROOT", "/unused")
    monkeypatch.setattr("valuation_benchmarks.load_benchmark", lambda *a, **k: {"value_decimal": "0.1"})
    assert views.resolve_benchmark_selections(selection(), "2026-10-19")["wacc"] == {
        "value_decimal": "0.1"
    }


def test_cloudflare_hosting_requires_owner_even_without_production_environment(client, monkeypatch):
    from owner_benchmark_access import OwnerBenchmarkAuthRequired, require_owner_benchmark_access

    monkeypatch.setitem(views.app.config, "CLOUDFLARE", True)
    with views.app.test_request_context("/api/calculate"):
        with pytest.raises(OwnerBenchmarkAuthRequired):
            require_owner_benchmark_access(lambda name: "")
