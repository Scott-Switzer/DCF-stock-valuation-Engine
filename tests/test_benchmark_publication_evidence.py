"""Publication-evidence and coverage-preflight contract for benchmark releases.

``published_at`` must come from source evidence (the provider's HTTP
Last-Modified of the exact bytes, bound to the preserved evidence sha256) —
never download time or a guessed vintage label. Historical cutoffs before
supported availability must fail closed, and releases without publication
evidence stay unavailable historically while current-mode selection is
unchanged. No test asserts a benchmark value beyond the fixture's own numbers.
"""

import hashlib
import json

import pytest

from valuation_benchmarks import (
    AVAILABLE,
    UNAVAILABLE,
    coverage_catalog,
    load_benchmark,
    load_publication_evidence,
    resolve_publication,
    validate_publication,
)

SERVER_DATE = "Mon, 12 Jan 2026 13:41:41 GMT"
OBSERVED = "2026-10-14T20:50:21.531103+00:00"
SOURCE_URL = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/wacc.xls"


def encoded(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def evidence(**overrides):
    record = {
        "method": "SERVER_LAST_MODIFIED",
        "source_url": SOURCE_URL,
        "server_last_modified": SERVER_DATE,
        "observed_at": OBSERVED,
        "statement": "HTTP Last-Modified of the exact source bytes, bound to evidence_sha256",
    }
    record.update(overrides)
    return record


def release(tmp_path, *, value="0.08", source_sha=None):
    data = encoded(
        {
            "schema_version": "damodaran-assumptions-v1",
            "dataset_id": "cost_of_capital",
            "region": "US",
            "records": [
                {
                    "subject": "Software",
                    "measure": "wacc",
                    "value_decimal": value,
                    "unit": "fraction",
                    "classification": "BENCHMARK_ASSUMPTION_NOT_COMPANY_FACT",
                    "source_cell": "K3",
                },
                {
                    "subject": "Banks (Regional)",
                    "measure": "wacc",
                    "value_decimal": None,
                    "unit": "fraction",
                    "classification": "BENCHMARK_ASSUMPTION_NOT_COMPANY_FACT",
                },
            ],
        }
    )
    raw = b"public source"
    manifest = {
        "schema_version": "damodaran-assumptions-v1",
        "dataset_id": "cost_of_capital",
        "region": "US",
        "published_at": None,
        "source_url": SOURCE_URL,
        "files": {
            "source.bin": hashlib.sha256(raw).hexdigest(),
            "normalized.json": hashlib.sha256(data).hexdigest(),
        },
    }
    rid = hashlib.sha256(encoded(manifest)).hexdigest()
    manifest["release_id"] = rid
    path = tmp_path / rid
    path.mkdir()
    (path / "manifest.json").write_bytes(encoded(manifest))
    (path / "normalized.json").write_bytes(data)
    (path / "source.bin").write_bytes(raw)
    return rid, source_sha or manifest["files"]["source.bin"]


def catalog(tmp_path, entries):
    body = json.dumps(
        {"schema_version": "damodaran-publication-evidence-v1", "releases": entries},
        indent=2,
        sort_keys=True,
    ).encode()
    (tmp_path / "publication_evidence.json").write_bytes(body)
    return body


def entry(rid, source_sha, published="2026-01-12", record=None):
    return {
        "release_id": rid,
        "dataset_id": "cost_of_capital",
        "region": "US",
        "source_sha256": source_sha,
        "published_at": published,
        "publication_evidence": evidence() if record is None else record,
        "retrieved_at": OBSERVED,
        "historical_availability": AVAILABLE if published else UNAVAILABLE,
    }


class TestPublicationEvidenceContract:
    def test_server_last_modified_date_is_the_only_usable_publication_date(self):
        recorded = validate_publication("2026-01-12", evidence(), OBSERVED)
        assert recorded["server_last_modified"] == SERVER_DATE

    @pytest.mark.parametrize(
        "published,record",
        [
            # download time instead of the provider's timestamp for the bytes
            ("2026-10-14", evidence()),
            # a guessed year from a stated vintage label
            ("2026-01-01", evidence()),
            ("2026-01-12", "evidence as a bare string"),
            ("2026-01-12", evidence(method="GUESSED_VINTAGE_LABEL")),
            ("2026-01-12", evidence(source_url="http://pages.stern.nyu.edu/wacc.xls")),
            ("2026-01-12", evidence(observed_at="2026-01-11T00:00:00+00:00")),
            ("2026-01-12", evidence(statement="  ")),
        ],
    )
    def test_unsupported_publication_evidence_is_rejected_not_stored(self, published, record):
        with pytest.raises(ValueError):
            validate_publication(published, record, OBSERVED)

    def test_missing_evidence_with_a_date_is_rejected(self):
        with pytest.raises(ValueError):
            validate_publication("2026-01-12", None, OBSERVED)

    def test_unavailable_release_needs_no_evidence(self):
        assert validate_publication(None, None, OBSERVED) is None


class TestFailClosedResolution:
    def test_bare_manifest_date_stays_unavailable_without_evidence(self):
        published, record, availability = resolve_publication("a" * 64, "sha", "2026-01-08", None)
        assert (published, record, availability) == ("2026-01-08", None, UNAVAILABLE)

    def test_evidence_for_other_bytes_fails_closed(self):
        published, record, availability = resolve_publication(
            "a" * 64, "actual-bytes-sha", None, entry("a" * 64, "different-bytes-sha")
        )
        assert (published, record, availability) == (None, None, UNAVAILABLE)

    def test_invalid_evidence_entry_fails_closed(self):
        bad = entry("a" * 64, "sha", published="2026-10-14", record=evidence())
        assert resolve_publication("a" * 64, "sha", None, bad) == (None, None, UNAVAILABLE)

    def test_unevidenced_entry_stays_unavailable(self):
        bare = entry("a" * 64, "sha", published=None, record=None)
        assert resolve_publication("a" * 64, "sha", None, bare) == (None, None, UNAVAILABLE)


class TestHistoricalSelection:
    def test_cutoff_before_publication_is_refused(self, tmp_path):
        rid, sha = release(tmp_path)
        catalog(tmp_path, [entry(rid, sha)])
        with pytest.raises(ValueError, match="Benchmark vintage unavailable at historical cutoff"):
            load_benchmark(tmp_path, rid, "Software", "wacc", as_of="2026-01-11")

    def test_cutoff_on_publication_date_serves_the_evidence_backed_vintage(self, tmp_path):
        rid, sha = release(tmp_path)
        catalog(tmp_path, [entry(rid, sha)])
        row = load_benchmark(tmp_path, rid, "Software", "wacc", as_of="2026-01-12")
        assert row["published_at"] == "2026-01-12"
        assert row["publication_evidence"]["method"] == "SERVER_LAST_MODIFIED"
        assert row["selection_mode"] == "HISTORICAL_PUBLISHED"
        assert row["historical_availability"] == AVAILABLE

    def test_unevidenced_release_refuses_every_historical_cutoff(self, tmp_path):
        rid, sha = release(tmp_path)
        catalog(tmp_path, [entry(rid, sha, published=None, record=None)])
        for cutoff in ("2026-01-12", "2026-10-14", "2026-12-31"):
            with pytest.raises(ValueError, match="Benchmark vintage unavailable"):
                load_benchmark(tmp_path, rid, "Software", "wacc", as_of=cutoff)

    def test_current_mode_is_unchanged_without_any_publication_metadata(self, tmp_path):
        rid, _ = release(tmp_path)
        row = load_benchmark(tmp_path, rid, "Software", "wacc")
        assert row["value_decimal"] == "0.08"
        assert row["published_at"] is None
        assert row["selection_mode"] == "CURRENT_EXPLICIT_SELECTION"
        assert row["historical_availability"] == UNAVAILABLE

    def test_catalog_evidence_lifting_historical_needs_byte_binding(self, tmp_path):
        rid, _ = release(tmp_path)
        catalog(tmp_path, [entry(rid, "sha-of-other-bytes")])
        with pytest.raises(ValueError, match="Benchmark vintage unavailable"):
            load_benchmark(tmp_path, rid, "Software", "wacc", as_of="2026-12-31")

    def test_curator_written_catalog_serves_historical_selection(self, tmp_path):
        # scripts/build_benchmark_publication_evidence.py discloses the download
        # time as ``download_retrieved_at``; a catalog it writes must resolve.
        rid, sha = release(tmp_path)
        produced = entry(rid, sha)
        produced["download_retrieved_at"] = produced.pop("retrieved_at")
        catalog(tmp_path, [produced])
        row = load_benchmark(tmp_path, rid, "Software", "wacc", as_of="2026-06-01")
        assert row["selection_mode"] == "HISTORICAL_PUBLISHED"
        assert row["published_at"] == "2026-01-12"

    def test_catalog_entry_without_a_download_time_still_fails_closed(self, tmp_path):
        rid, sha = release(tmp_path)
        undeclared = entry(rid, sha)
        del undeclared["retrieved_at"]
        catalog(tmp_path, [undeclared])
        with pytest.raises(ValueError, match="Benchmark vintage unavailable"):
            load_benchmark(tmp_path, rid, "Software", "wacc", as_of="2026-06-01")

    def test_evidence_observed_after_the_recorded_download_still_resolves(self, tmp_path):
        # The curator records the ingest download time while binding headers
        # re-checked later; the two are independent collection events.
        rid, sha = release(tmp_path)
        produced = entry(rid, sha)
        produced["download_retrieved_at"] = produced.pop("retrieved_at")
        produced["download_retrieved_at"] = "2026-10-14T19:28:12.165271+00:00"
        catalog(tmp_path, [produced])
        row = load_benchmark(tmp_path, rid, "Software", "wacc", as_of="2026-09-01")
        assert row["selection_mode"] == "HISTORICAL_PUBLISHED"

    def test_publication_date_after_the_recorded_download_is_still_refused(self):
        with pytest.raises(ValueError, match="publication date cannot follow retrieval"):
            validate_publication("2026-10-20", evidence(), OBSERVED)

    def test_date_only_retrieval_is_accepted_at_day_precision(self):
        # A lineage record states the day, not an instant; it must not be
        # upgraded, but it is still a usable ordering bound.
        recorded = validate_publication("2026-01-12", evidence(), "2026-10-14")
        assert recorded["method"] == "SERVER_LAST_MODIFIED"

    def test_publication_after_a_date_only_retrieval_is_refused(self):
        with pytest.raises(ValueError, match="publication date cannot follow retrieval"):
            validate_publication("2026-01-12", evidence(), "2026-01-11")


class TestCoverageCatalog:
    def test_lists_only_pairs_a_selection_would_serve(self, tmp_path):
        rid, sha = release(tmp_path)
        catalog(tmp_path, [entry(rid, sha)])
        listing = coverage_catalog(tmp_path)
        assert len(listing) == 1
        assert listing[0]["subject_measure_pairs"] == [{"subject": "Software", "measure": "wacc"}]
        assert listing[0]["unavailable_pair_count"] == 1
        assert listing[0]["target_measures_available"] == ["wacc"]
        assert listing[0]["published_at"] == "2026-01-12"

    def test_reports_fail_closed_status_for_unevidenced_releases(self, tmp_path):
        rid, sha = release(tmp_path)
        catalog(tmp_path, [entry(rid, sha, published=None, record=None)])
        listing = coverage_catalog(tmp_path)
        assert listing[0]["published_at"] is None
        assert listing[0]["historical_availability"] == UNAVAILABLE

    def test_malformed_catalog_is_refused_loudly(self, tmp_path):
        rid, _ = release(tmp_path)
        (tmp_path / "publication_evidence.json").write_bytes(
            json.dumps({"schema_version": "something-else", "releases": []}).encode()
        )
        with pytest.raises(ValueError, match="Publication evidence schema mismatch"):
            load_publication_evidence(tmp_path)
