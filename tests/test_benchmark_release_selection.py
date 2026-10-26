"""Release-root benchmark selection through the API, and the real curator output.

These live outside ``test_zion_benchmark_chain.py`` because that module skips
wholesale when the sibling DDFI release tree is absent; every case here uses
synthetic bytes only and must run in every checkout and in CI.

The last test is the producer->consumer contract: it runs the actual curator
script (``scripts/build_benchmark_publication_evidence.py``) over a synthetic
release and reads the catalog it writes back through ``load_benchmark``. That is
the check whose absence let the loader and the curator disagree about the
download-time key without any test noticing.
"""

import hashlib
import importlib.util
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SUBJECT = "Software (System & Application)"
SYNTHETIC_SOURCE = b"synthetic fixture source bytes"
SERVER_DATE = "Mon, 05 Jan 2026 12:00:00 GMT"
PUBLISHED = "2026-01-05"
RETRIEVED = "2026-10-14T19:28:12.165271+00:00"
OBSERVED = "2026-10-14T20:50:21.531103+00:00"


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def synthetic_release(root, *, publication_evidence, published_at=PUBLISHED):
    """Write a byte-bound synthetic release exactly as the loader verifies it."""
    data = encoded(
        {
            "schema_version": "damodaran-assumptions-v1",
            "dataset_id": "cost_of_capital",
            "region": "US",
            "records": [
                {
                    "subject": SUBJECT,
                    "measure": "wacc",
                    "value_decimal": "0.08",
                    "unit": "fraction",
                    "source_cell": "SYNTHETIC",
                    "classification": "BENCHMARK_ASSUMPTION_NOT_COMPANY_FACT",
                }
            ],
        }
    )
    manifest = {
        "schema_version": "damodaran-assumptions-v1",
        "dataset_id": "cost_of_capital",
        "region": "US",
        "published_at": published_at,
        "publication_evidence": publication_evidence,
        "source_url": "https://example.invalid/synthetic-wacc.xls",
        "files": {
            "source.bin": hashlib.sha256(SYNTHETIC_SOURCE).hexdigest(),
            "normalized.json": hashlib.sha256(data).hexdigest(),
        },
    }
    release_id = hashlib.sha256(encoded(manifest)).hexdigest()
    manifest["release_id"] = release_id
    folder = root / release_id
    folder.mkdir(parents=True)
    (folder / "manifest.json").write_bytes(encoded(manifest))
    (folder / "normalized.json").write_bytes(data)
    (folder / "source.bin").write_bytes(SYNTHETIC_SOURCE)
    (folder / "retrieval.json").write_bytes(
        json.dumps({"retrieved_at": RETRIEVED}).encode()
    )
    return release_id


def reviewed_evidence():
    return {
        "method": "SERVER_LAST_MODIFIED",
        "source_url": "https://example.invalid/synthetic-wacc.xls",
        "server_last_modified": SERVER_DATE,
        "observed_at": OBSERVED,
        "statement": "synthetic header bound to the exact synthetic bytes",
    }


@pytest.fixture
def releases(tmp_path):
    root = tmp_path / "releases"
    root.mkdir()
    return root


@pytest.fixture
def client(monkeypatch, tmp_path, releases):
    monkeypatch.setenv("DAMODARAN_RELEASE_ROOT", str(releases))
    monkeypatch.setenv("DCF_STATE_PATH", str(tmp_path / "state.sqlite3"))
    from app import app

    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))
    return app.test_client()


def calculate(client, release_id, *, mode="historical", valuation_date=None):
    from dcf_loader import demo_document

    document = demo_document()
    document["valuation_date"] = valuation_date or datetime.now(timezone.utc).date().isoformat()
    return client.post(
        "/api/calculate",
        json={
            "financials": document,
            "assumptions": {"revenue_growth_rates": [0.05] * 5,
                            "terminal_growth_rate": 0.02},
            "benchmark_selections": {
                "wacc_override": {
                    "release_id": release_id,
                    "subject": SUBJECT,
                    "measure": "wacc",
                    "mode": mode,
                    "source": "release",
                }
            },
        },
    )


def adopted_row(response):
    return response.json["metadata"]["document"]["source"]["benchmark_assumptions"]["wacc_override"]


def test_reviewed_evidence_serves_a_historical_selection(client, releases):
    release_id = synthetic_release(releases, publication_evidence=reviewed_evidence())
    response = calculate(client, release_id)
    assert response.status_code == 200, response.json
    assert response.json["wacc"] == pytest.approx(0.08)
    row = adopted_row(response)
    assert row["selection_mode"] == "HISTORICAL_PUBLISHED"
    assert row["published_at"] == PUBLISHED
    assert row["publication_evidence"]["method"] == "SERVER_LAST_MODIFIED"


def test_cutoff_before_publication_is_refused(client, releases):
    release_id = synthetic_release(releases, publication_evidence=reviewed_evidence())
    before = (date.fromisoformat(PUBLISHED) - timedelta(days=1)).isoformat()
    response = calculate(client, release_id, valuation_date=before)
    assert response.status_code == 400, response.json
    assert "published after cutoff" in response.json["error"]


def test_release_without_evidence_fails_closed(client, releases):
    release_id = synthetic_release(releases, publication_evidence=None)
    response = calculate(client, release_id)
    assert response.status_code == 400, response.json
    assert "NO_REVIEWED_PUBLICATION_EVIDENCE" in response.json["error"]


def test_current_mode_still_serves_without_evidence(client, releases):
    release_id = synthetic_release(releases, publication_evidence=None)
    response = calculate(client, release_id, mode="current")
    assert response.status_code == 200, response.json
    assert adopted_row(response)["selection_mode"] == "CURRENT_EXPLICIT_SELECTION"


def load_curator():
    path = REPO_ROOT / "scripts/build_benchmark_publication_evidence.py"
    spec = importlib.util.spec_from_file_location("benchmark_evidence_curator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_curator_output_resolves_through_the_loader(releases, tmp_path, monkeypatch):
    """Run the real curator; feed its catalog to the real loader."""
    from valuation_benchmarks import load_benchmark, load_publication_evidence

    release_id = synthetic_release(releases, publication_evidence=None)

    evidence_root = tmp_path / "ddfi"
    evidence_dir = evidence_root / "evidence"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "synthetic-wacc.xls").write_bytes(SYNTHETIC_SOURCE)
    source_sha = hashlib.sha256(SYNTHETIC_SOURCE).hexdigest()
    report = {
        "downloads": [
            {
                "sha256": source_sha,
                "last_modified_server": SERVER_DATE,
                "evidence_path": "evidence/synthetic-wacc.xls",
                "fetched_at": OBSERVED,
            }
        ]
    }
    (evidence_root / "registry").mkdir()
    (evidence_root / "registry/pilot_ingest_report.json").write_bytes(
        json.dumps(report).encode()
    )
    (evidence_root / "registry/assumption_releases").mkdir()
    (evidence_root / "registry/assumption_releases/index.json").write_bytes(
        json.dumps({"releases": [{"source_sha256": source_sha,
                                  "stated_publication_date": PUBLISHED}]}).encode()
    )

    curator = load_curator()
    # Keep every write inside tmp_path: the curator puts the catalog beside the
    # releases and its review copy/receipt under ROOT.
    isolated_root = tmp_path / "curator-root"
    isolated_root.mkdir()
    monkeypatch.setattr(curator, "ROOT", isolated_root)
    monkeypatch.setattr(curator, "workspace_root", lambda: tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        ["build_benchmark_publication_evidence.py",
         "--releases", str(releases),
         "--evidence-root", str(evidence_root)],
    )
    curator.main()

    catalog = load_publication_evidence(releases)
    assert list(catalog) == [release_id]
    entry = catalog[release_id]
    assert entry["download_retrieved_at"] == RETRIEVED
    assert entry["published_at"] == PUBLISHED
    assert entry["source_sha256"] == source_sha

    row = load_benchmark(releases, release_id, SUBJECT, "wacc", as_of="2026-09-01")
    assert row["selection_mode"] == "HISTORICAL_PUBLISHED"
    assert row["publication_evidence"]["method"] == "SERVER_LAST_MODIFIED"

    # A cutoff before the catalog's date is still refused. The manifest here
    # carries a date and no evidence, like the real registry releases, so this
    # also proves the catalog is consulted instead of the bare manifest date.
    with pytest.raises(ValueError, match="published after cutoff"):
        load_benchmark(releases, release_id, SUBJECT, "wacc", as_of="2026-01-04")
