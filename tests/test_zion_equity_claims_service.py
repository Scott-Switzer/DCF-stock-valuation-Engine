"""The integrated DCF-side flow: internal service binding, verified claims, saved bridge.

The runtime seams exercised here are the transport's `dispatch` and the async `sync`
bridge; everything above them -- credential headers, contract verification, release
pinning, bridge arithmetic and the saved record -- is the real production code path.
"""

import asyncio
import json
import sqlite3
from pathlib import Path

import pytest

import zion_equity_claims_service as service
from app import app
from dcf_loader import ProviderError
from storage import Store

MIGRATIONS = sorted((Path(__file__).resolve().parents[1] / "migrations").glob("*.sql"))


class BoundResponse:
    """The subset of a Cloudflare Response the transport reads."""

    def __init__(self, status, body):
        self.status = status
        self._body = body

    async def text(self):
        return self._body


class BoundTransport(service.ServiceBindingHTTP):
    """A binding double; `dispatch` is the only step that touches the runtime."""

    def __init__(self, response, *, timeout_ms=1000):
        super().__init__(object(), timeout_ms=timeout_ms)
        self.response = response
        self.calls = []

    async def dispatch(self, target, headers):
        self.calls.append((target, headers))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


@pytest.fixture(autouse=True)
def drive(monkeypatch):
    monkeypatch.setattr(service, "sync", lambda awaitable: asyncio.run(awaitable))


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("DCF_STATE_PATH", str(tmp_path / "claims.sqlite3"))
    monkeypatch.setattr(Store, "allow", lambda *args, **kwargs: True)
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "limits.sqlite3"))


def bridge_record(cik="0001652044", ticker="GOOGL"):
    return {
        "ticker": ticker, "cik": cik, "valuation_date": "2026-10-14",
        "primary_scenario": "AS_CONVERTED_MAX_RATE", "enterprise_scenario_value": 2.5e12,
        "primary": {"status": "AVAILABLE", "equity_value": 2.311761e12,
                    "value_per_share": 188.19, "missing": []},
        "source": {"release_id": "a" * 64, "member_sha256": "b" * 64},
    }


def test_transport_refuses_refusals_non_json_and_nonfinite_bodies():
    refusal = BoundTransport(BoundResponse(401, json.dumps({"error": {"code": "UNAUTHORIZED"}})))
    with pytest.raises(ProviderError) as excinfo:
        refusal.get("https://zion.internal/private/v1/equity-claims")
    assert "HTTP 401" in str(excinfo.value) and "UNAUTHORIZED" in str(excinfo.value)

    with pytest.raises(ProviderError, match="not JSON"):
        BoundTransport(BoundResponse(200, "<html>no</html>")).get("https://zion.internal/x")

    with pytest.raises(ProviderError, match="nonfinite"):
        BoundTransport(BoundResponse(200, '{"value": NaN}')).get("https://zion.internal/x")

    with pytest.raises(ProviderError, match="JSON object"):
        BoundTransport(BoundResponse(200, "[1, 2]")).get("https://zion.internal/x")


def test_transport_times_out_instead_of_returning_a_partial_answer():
    class Slow(service.ServiceBindingHTTP):
        async def dispatch(self, target, headers):
            await asyncio.sleep(5)

    with pytest.raises(ProviderError, match="did not answer within 10 ms"):
        Slow(object(), timeout_ms=10).get("https://zion.internal/x")


def test_transport_without_a_binding_never_issues_a_request():
    with pytest.raises(ProviderError, match="no internal service binding"):
        service.ServiceBindingHTTP(None).get("https://zion.internal/x")


def test_claims_without_a_configured_binding_fail_closed(monkeypatch):
    monkeypatch.setattr(service, "service_binding", lambda: None)
    monkeypatch.setenv("ZION_SERVICE_TOKEN", "scoped-test-token")
    with pytest.raises(ProviderError, match="no internal service binding"):
        service.load_claims("GOOGL", "2026-10-14", cik="0001652044")
    # Without the scoped credential the contract is refused before a request is built.
    monkeypatch.delenv("ZION_SERVICE_TOKEN")
    with pytest.raises(ProviderError, match="credential"):
        service.load_claims("GOOGL", "2026-10-14", cik="0001652044")


def test_an_unapproved_internal_caller_is_refused_before_any_request(monkeypatch):
    monkeypatch.setenv("ZION_EQUITY_CLAIMS_CALLER", "some-other-worker")
    transport = BoundTransport(BoundResponse(200, "{}"))
    with pytest.raises(ProviderError, match="not an approved caller"):
        service.load_claims("GOOGL", "2026-10-14", cik="0001652044", http=transport)
    assert transport.calls == []


def test_status_route_reports_configuration_without_exposing_credentials():
    body = app.test_client().get("/api/equity-claims/status").get_json()
    assert body["binding"] == "ZION_FINANCIAL_QUERY"
    assert body["configured"] is False
    assert body["caller"] == "dcf-valuation-engine" and body["caller_approved"] is True
    assert body["service_credential_configured"] is False
    assert body["credentials_exposed"] is False
    assert body["route"] == "/private/v1/equity-claims"
    assert "token" not in json.dumps(body).lower()


def test_bridge_route_validates_the_request_before_using_the_binding():
    client = app.test_client()
    assert client.post("/api/equity-claims/bridge", json={"ticker": "GOOGL"}).status_code == 400
    # A syntactically complete request without an attested bundle is rejected, so the
    # internal dependency is never consulted for an unverified enterprise value.
    response = client.post("/api/equity-claims/bridge", json={
        "ticker": "GOOGL", "cik": "0001652044", "valuation_date": "2026-10-14",
        "financials": {}, "revenue_growth_rates": [0.05] * 5, "terminal_growth": 0.02,
        "terminal_roic": 0.15, "suitable": True})
    assert response.status_code == 400
    assert client.post("/api/equity-claims/bridge", json={
        "ticker": "GOOGL", "cik": "1652044", "valuation_date": "2026-10-14",
        "financials": {}}).status_code == 400


def test_cross_site_writes_to_the_bridge_route_are_refused():
    response = app.test_client().post("/api/equity-claims/bridge", json={},
                                      headers={"Origin": "https://evil.example"})
    assert response.status_code == 403


def test_saved_bridge_round_trips_through_the_api_and_exports():
    client = app.test_client()
    client.get("/api/equity-claims/bridges")  # mints this browser's library identity
    cookie = client.get_cookie("lib_id")
    with app.test_request_context("/api/equity-claims/bridges",
                                  headers={"Cookie": f"lib_id={cookie.value}"}):
        saved = service.save_bridge(bridge_record())
    assert saved["value_per_share"] == 188.19
    assert saved["release_id"] == "a" * 64

    detail = client.get(f"/api/equity-claims/bridges/{saved['id']}").get_json()
    assert detail["receipt"]["cik"] == "0001652044"

    listing = client.get("/api/equity-claims/bridges?ticker=GOOGL").get_json()
    assert [row["id"] for row in listing] == [saved["id"]]
    assert client.get("/api/equity-claims/bridges?ticker=MSFT").get_json() == []

    export = client.get(f"/api/equity-claims/bridges/{saved['id']}/export/json")
    assert export.status_code == 200
    assert "GOOGL-equity-claims-" in export.headers["Content-Disposition"]
    assert json.loads(export.get_data())["receipt"]["source"]["release_id"] == "a" * 64

    assert client.get("/api/equity-claims/bridges/missing").status_code == 404


def test_a_bridge_record_without_a_release_pin_is_not_saved():
    record = bridge_record()
    del record["source"]["release_id"]
    with app.test_request_context("/api/equity-claims/bridges"):
        with pytest.raises(ProviderError, match="without a release pin"):
            service.save_bridge(record)


def test_migration_0009_creates_the_bridge_table(tmp_path):
    database = sqlite3.connect(tmp_path / "migrated.sqlite3")
    for index, path in enumerate(MIGRATIONS):
        database.executescript(path.read_text())
        database.execute(f"PRAGMA user_version = {index + 1}")
    columns = {row[1] for row in database.execute("PRAGMA table_info(equity_claims_bridges)")}
    assert {"id", "client_hash", "ticker", "cik", "release_id", "receipt_json"} <= columns
    assert database.execute("PRAGMA user_version").fetchone()[0] == len(MIGRATIONS)
