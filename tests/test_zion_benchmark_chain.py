"""End-to-end DDFI -> Zion -> DCF chain tests (10 acceptance points).

Runs the production DCF request path (/api/calculate -> resolve_benchmark_selections
-> zion_benchmark_provider -> apply_benchmarks -> evaluate) against the REAL
DDFI assumption releases in data/ddfi/registry/assumption_releases. The local
Zion stub replays the documented Zion benchmark_context wire contract from those
real release bytes; the same contract is exercised against the deployed staging
service by data/ddfi/scripts/e2e_ddfi_zion_dcf_acceptance.py --live.

Acceptance points:
 1. a real industry benchmark is selected           -> test_chain_..._through_zion
 2. retrieved through Zion                          -> request log assertions
 3. actual release and source identified            -> release_id/source_url/sha256
 4. assumption adopted explicitly in the DCF model  -> wacc == expected cell value
 5. numerical calculation runs                      -> full /api/calculate result
 6. issuer financial statement facts unchanged      -> identical minus provenance
 7. evidence lineage retained                       -> benchmark_evidence in result
 8. future-release requests rejected                -> BENCHMARK_VINTAGE_UNAVAILABLE
 9. missing benchmark fails explicitly              -> no silent substitution
10. independent expected result                     -> explicit-assumption path equality
"""

import hashlib
import json as jsonlib
from datetime import datetime, timezone
from pathlib import Path

import pytest

RELEASES_ROOT = Path(__file__).resolve().parents[2] / "data/ddfi/registry/assumption_releases"

# Independently captured from the source workbook cell (Damodaran cost-of-capital
# workbook, Industry Averages sheet, Cost of Capital column, Software row), and
# pinned here so a drifting release fails this test instead of silently moving.
EXPECTED_WACC_SOFTWARE = "0.09344048072400105"
SUBJECT = "Software (System & Application)"

pytestmark = pytest.mark.skipif(
    not RELEASES_ROOT.exists(),
    reason="real DDFI releases are not present in this checkout",
)


def index():
    return jsonlib.loads((RELEASES_ROOT / "index.json").read_bytes())


def release_entry(dataset_id):
    candidates = [e for e in index()["releases"] if e["dataset_id"] == dataset_id]
    assert candidates, f"no built release for {dataset_id}"
    return max(candidates, key=lambda e: e["published_at"])


def today():
    return datetime.now(timezone.utc).date().isoformat()


@pytest.fixture(autouse=True)
def _isolated_state(monkeypatch, tmp_path):
    """Per-test state store so the app's rate limiter does not bleed across tests."""
    from app import app

    monkeypatch.setenv("DCF_STATE_PATH", str(tmp_path / "library.sqlite3"))
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.content = jsonlib.dumps(payload).encode()

    def json(self):
        return self._payload


class StubZion:
    """Replays the Zion benchmark_context contract from real release bytes."""

    def __init__(self, *, missing=False, error=None, serve_release=None):
        self.missing, self.error, self.serve_release = missing, error, serve_release
        self.requests = []

    def post(self, url, headers=None, json=None):
        body = json
        assert url.endswith("/private/v1/query"), url
        assert headers.get("Authorization", "").startswith("Bearer ")
        self.requests.append(body)
        if self.error is not None:
            return FakeResponse(self.error[1], {"error": {
                "code": self.error[0], "message": self.error[2], "retryable": False}})
        release_id = self.serve_release or body["release_id"]
        entry = next(e for e in index()["releases"] if e["release_id"] == release_id)
        manifest = jsonlib.loads((RELEASES_ROOT / release_id / "manifest.json").read_bytes())
        data = jsonlib.loads((RELEASES_ROOT / release_id / "normalized.json").read_bytes())
        as_of = body.get("as_of")
        if as_of is not None and manifest["published_at"] > as_of[:10]:
            return FakeResponse(404, {"error": {
                "code": "BENCHMARK_VINTAGE_UNAVAILABLE",
                "message": f"release published {manifest['published_at']} after {as_of[:10]}",
                "retryable": False}})
        observations = []
        for record in data["records"]:
            if record["subject"] != body["subject"] or record["measure"] not in body["measures"]:
                continue
            observation = {k: record[k] for k in record if k != "subject_type"} | {
                "subject_type": record["subject_type"]}
            if self.missing:
                observation["value_decimal"] = None
                observation["missing"] = True
                observation["missing_reason"] = "WORKBOOK_ERROR"
                observation["workbook_error"] = "#N/A"
                observation["quarantined"] = True
            observations.append(observation)
        return FakeResponse(200, {
            "schema_version": "zion-private-query-v1",
            "request_id": "stub-req",
            "operation": "benchmark_context",
            "release": {
                "serving_release_id": "ddfi-benchmarks:" + release_id,
                "ddfi_release_id": release_id,
                "dataset_id": entry["dataset_id"],
                "region": entry["region"],
                "subject_type": entry["subject_type"],
                "published_at": manifest["published_at"],
                "selection_mode": "HISTORICAL_AS_OF" if as_of else "EXACT_PINNED",
                "provider": manifest["provider"],
                "source_url": manifest["source_url"],
                "source_sha256": manifest["files"]["source.bin"],
                "normalized_sha256": manifest["files"]["normalized.json"],
                "ingested_bundle": manifest["lineage"]["ingested_bundle"],
                "retrieved_at": manifest["lineage"]["retrieved_at"],
                "stated_publication_date": manifest["lineage"]["stated_publication_date"],
                "index_sha256": "0" * 64,
                "rights": manifest["rights"],
            },
            "data": {
                "subject": body["subject"],
                "subject_type": data["subject_type"],
                "dataset_id": entry["dataset_id"],
                "region": entry["region"],
                "observations": observations,
                "missing_count": 1 if self.missing else 0,
                "definitions": data.get("definitions", {}),
                "unit_definitions": data.get("unit_definitions", {}),
            },
            "coverage": {
                "status": "PARTIAL" if self.missing else "AVAILABLE",
                "as_of": as_of,
                "live_provider_calls": 0,
                "source_bytes_served": False,
            },
        })


def calculate(client, *, benchmark, stub, valuation_date=None, assumptions=None):
    from dcf_loader import demo_document

    doc = demo_document()
    doc["valuation_date"] = valuation_date or today()
    body = {
        "financials": doc,
        "assumptions": assumptions or {"revenue_growth_rates": [0.05] * 5,
                                       "terminal_growth_rate": 0.02},
    }
    if benchmark is not None:
        body["benchmark_selections"] = benchmark
    monkey = pytest.MonkeyPatch()
    monkey.setattr("requests.post", stub.post)
    try:
        return client.post("/api/calculate", json=body)
    finally:
        monkey.undo()


def adopted_row(response_json):
    """The provenance-bearing row from the result's embedded document source."""
    return response_json["metadata"]["document"]["source"]["benchmark_assumptions"]["wacc_override"]


def strip_provenance(value):
    """Remove only benchmark provenance and record ids, keeping every fact."""
    if isinstance(value, dict):
        return {k: strip_provenance(v) for k, v in value.items()
                if k not in ("benchmark_assumptions", "saved_record_id")}
    if isinstance(value, list):
        return [strip_provenance(v) for v in value]
    return value


def client_and_env(monkeypatch):
    from app import app

    monkeypatch.setenv("ZION_BENCHMARK_BASE_URL", "https://zion-stub.invalid")
    monkeypatch.setenv("ZION_BENCHMARK_TOKEN", "stub-token")
    return app.test_client()


def selection(entry, *, mode="historical", source="zion"):
    return {"wacc_override": {
        "release_id": entry["release_id"], "subject": SUBJECT, "measure": "wacc",
        "mode": mode, "source": source}}


def test_chain_selects_real_industry_benchmark_through_zion(monkeypatch):
    entry = release_entry("cost_of_capital")
    stub = StubZion()
    client = client_and_env(monkeypatch)
    response = calculate(client, benchmark=selection(entry), stub=stub)
    assert response.status_code == 200, response.json
    # 2: retrieved through Zion's private query contract
    assert stub.requests and stub.requests[0]["operation"] == "benchmark_context"
    assert stub.requests[0]["release_id"] == entry["release_id"]
    assert stub.requests[0]["as_of"] == today()
    # 3: actual release and source identified
    row = adopted_row(response.json)
    assert row["release_id"] == entry["release_id"]
    assert row["dataset_id"] == "cost_of_capital"
    assert "stern.nyu.edu" in row["source_url"]
    assert row["source_sha256"] == hashlib.sha256(
        (RELEASES_ROOT / entry["release_id"] / "source.bin").read_bytes()).hexdigest()
    assert row["published_at"] == entry["published_at"]
    # 4: adopted explicitly in the DCF model
    assert row["value_decimal"] == EXPECTED_WACC_SOFTWARE
    assert response.json["wacc"] == pytest.approx(float(EXPECTED_WACC_SOFTWARE))
    # 5: a real numerical calculation ran
    assert response.json["enterprise_value"] > 0
    assert row["classification"] == "BENCHMARK_ASSUMPTION_NOT_COMPANY_FACT"
    assert row["selection_mode"] == "HISTORICAL_PUBLISHED"


def test_calculation_matches_independent_explicit_assumption_path(monkeypatch):
    """Points 6 + 10: benchmark adoption is numerically identical to typing the
    same value in by hand, and issuer facts are untouched."""
    entry = release_entry("cost_of_capital")
    stub = StubZion()
    client = client_and_env(monkeypatch)
    via_benchmark = calculate(client, benchmark=selection(entry), stub=stub)
    stub2 = StubZion()
    explicit = calculate(
        client, benchmark=None, stub=stub2,
        assumptions={"revenue_growth_rates": [0.05] * 5, "terminal_growth_rate": 0.02,
                     "wacc_override": float(EXPECTED_WACC_SOFTWARE)})
    assert via_benchmark.status_code == explicit.status_code == 200
    # 6: every issuer fact and calculation output is identical
    assert strip_provenance(via_benchmark.json) == strip_provenance(explicit.json)
    left_doc = via_benchmark.json["metadata"]["document"]
    right_doc = explicit.json["metadata"]["document"]
    assert left_doc["historical"] == right_doc["historical"]  # issuer statement facts
    assert left_doc["market"] == right_doc["market"]
    assert left_doc["bridge"] == right_doc["bridge"]
    # ...and the evidence lives only in provenance
    assert "benchmark_assumptions" in left_doc["source"]
    assert "benchmark_assumptions" not in right_doc["source"]


def test_result_retains_benchmark_evidence_lineage(monkeypatch):
    entry = release_entry("cost_of_capital")
    stub = StubZion()
    client = client_and_env(monkeypatch)
    response = calculate(client, benchmark=selection(entry), stub=stub)
    row = adopted_row(response.json)
    evidence = row["benchmark_evidence"]
    assert evidence["via"] == "zion_private_benchmark_context"
    assert evidence["release"]["ddfi_release_id"] == entry["release_id"]
    assert evidence["release"]["rights"]["redistribution_policy"] == "PROHIBITED_PENDING_REVIEW"
    assert evidence["coverage"]["live_provider_calls"] == 0
    assert evidence["request"]["measures"] == ["wacc"]
    manifest = jsonlib.loads((RELEASES_ROOT / entry["release_id"] / "manifest.json").read_bytes())
    assert row["ingested_bundle"] == manifest["lineage"]["ingested_bundle"]


def test_future_release_request_is_rejected(monkeypatch):
    """Point 8: a request pinned before the release date fails with the typed
    vintage error — never a silent newest-release fallback."""
    entry = release_entry("cost_of_capital")
    stub = StubZion()
    client = client_and_env(monkeypatch)
    before = "2026-01-01"
    assert entry["published_at"] > before
    response = calculate(client, benchmark=selection(entry), stub=stub,
                         valuation_date=before)
    assert response.status_code == 400
    assert "BENCHMARK_VINTAGE_UNAVAILABLE" in response.json["error"]
    assert stub.requests[0]["as_of"] == before


def test_missing_benchmark_fails_explicitly(monkeypatch):
    """Point 9: a quarantined observation errors out; no substitution occurs."""
    entry = release_entry("cost_of_capital")
    stub = StubZion(missing=True)
    client = client_and_env(monkeypatch)
    response = calculate(client, benchmark=selection(entry), stub=stub)
    assert response.status_code == 400
    assert "missing or quarantined" in response.json["error"]
    assert "WORKBOOK_ERROR" in response.json["error"]
    assert set(response.json) == {"error"}  # no partial result, no substituted value


def test_release_mismatch_is_rejected(monkeypatch):
    entry = release_entry("cost_of_capital")
    other = release_entry("industry_betas")
    stub = StubZion(serve_release=other["release_id"])
    client = client_and_env(monkeypatch)
    response = calculate(client, benchmark=selection(entry), stub=stub)
    assert response.status_code == 400
    assert "release mismatch" in response.json["error"]


def test_server_error_envelope_is_structured(monkeypatch):
    entry = release_entry("cost_of_capital")
    stub = StubZion(error=("HISTORICAL_COVERAGE_UNAVAILABLE", 404,
                           "no cost_of_capital benchmark was published on or before 2025-01-01"))
    client = client_and_env(monkeypatch)
    response = calculate(client, benchmark=selection(entry), stub=stub,
                         valuation_date="2025-01-01")
    assert response.status_code == 400
    assert "HISTORICAL_COVERAGE_UNAVAILABLE" in response.json["error"]


def test_release_source_selection_still_works_without_zion(monkeypatch):
    """The standalone loader remains available for isolated testing (additive)."""
    entry = release_entry("cost_of_capital")
    monkeypatch.setenv("DAMODARAN_RELEASE_ROOT", str(RELEASES_ROOT))
    from app import app

    client = app.test_client()
    response = calculate(client, benchmark=selection(entry, source="release"),
                         stub=StubZion())
    assert response.status_code == 200, response.json
    assert response.json["wacc"] == pytest.approx(float(EXPECTED_WACC_SOFTWARE))


def test_providers_advertises_zion_benchmarks_without_secrets(monkeypatch):
    monkeypatch.setenv("ZION_BENCHMARK_BASE_URL", "https://zion-stub.invalid")
    monkeypatch.setenv("ZION_BENCHMARK_TOKEN", "stub-token")
    from app import app

    response = app.test_client().get("/api/providers")
    body = response.get_json()
    assert body["providers"]["zion_benchmarks"]["kind"] == "private_benchmark_reference"
    assert body["providers"]["zion_benchmarks"]["configured"] is True
    text = response.get_data(as_text=True)
    assert "stub-token" not in text
    assert "Bearer" not in text


def test_default_source_unchanged_and_unknown_source_rejected(monkeypatch):
    """No 'source' key keeps the original release-root behavior; garbage fails."""
    entry = release_entry("cost_of_capital")
    monkeypatch.setenv("DAMODARAN_RELEASE_ROOT", str(RELEASES_ROOT))
    from app import app

    client = app.test_client()
    legacy = {"wacc_override": {"release_id": entry["release_id"], "subject": SUBJECT,
                                "measure": "wacc", "mode": "historical"}}
    response = calculate(client, benchmark=legacy, stub=StubZion())
    assert response.status_code == 200, response.json
    bogus = {"wacc_override": {"release_id": entry["release_id"], "subject": SUBJECT,
                               "measure": "wacc", "mode": "historical", "source": "random"}}
    response = calculate(client, benchmark=bogus, stub=StubZion())
    assert response.status_code == 400
    assert "Unknown benchmark source" in response.json["error"]


def test_provider_sends_one_selector_and_asserts_the_dataset():
    """The private contract accepts exactly one of release_id/dataset_id.

    The caller pins the release, so dataset_id must be asserted against the
    served release instead of being sent as a competing selector.
    """
    from zion_benchmark_provider import BenchmarkProviderError, fetch_benchmark_row

    entry = release_entry("cost_of_capital")
    stub = StubZion()
    row = fetch_benchmark_row(
        base="https://zion-stub.invalid", token="stub-token", subject=SUBJECT, measure="wacc",
        release_id=entry["release_id"], mode="historical", valuation_date=today(),
        http=stub, dataset_id="cost_of_capital")
    assert "dataset_id" not in stub.requests[0]
    assert row["dataset_id"] == "cost_of_capital"

    with pytest.raises(BenchmarkProviderError, match="dataset mismatch"):
        fetch_benchmark_row(
            base="https://zion-stub.invalid", token="stub-token", subject=SUBJECT, measure="wacc",
            release_id=entry["release_id"], mode="historical", valuation_date=today(),
            http=StubZion(), dataset_id="industry_betas")
