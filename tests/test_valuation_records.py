import pytest
import json
import sqlite3
from pathlib import Path
from app import assumptions_from_json, evaluate
from dcf_loader import demo_document
from valuation_records import INSERT_SQL, record_values


def test_database_records_preserve_inputs_flag_samples_and_deduplicate():
    db = sqlite3.connect(":memory:")
    for migration in sorted(Path("migrations").glob("*.sql")):
        db.executescript(migration.read_text())
    doc = demo_document()
    a = assumptions_from_json(
        {"revenue_growth_rates": [0.05] * 5, "terminal_growth_rate": 0.02, "wacc_override": 0.065}
    )
    result = evaluate(doc, a)
    first = record_values(doc, a, result, "hashed-network")
    second = record_values(doc, a, result, "hashed-network")
    db.execute(INSERT_SQL, first)
    db.execute(INSERT_SQL, second)
    row = db.execute(
        "SELECT is_demo, financials_json, assumptions_json, intrinsic_value FROM valuations"
    ).fetchone()
    assert db.execute("SELECT count(*) FROM valuations").fetchone()[0] == 1
    assert row[0] == 1
    assert json.loads(row[1]) == doc
    assert json.loads(row[2])["wacc_override"] == 0.065
    assert row[3] == result["intrinsic_value"]
    assert "ip" not in {r[1] for r in db.execute("PRAGMA table_info(valuations)")}


def test_distinct_assumptions_are_retained():
    doc = demo_document()
    a = assumptions_from_json(
        {"revenue_growth_rates": [0.05] * 5, "terminal_growth_rate": 0.02, "wacc_override": 0.065}
    )
    original = record_values(doc, a, evaluate(doc, a), "hashed-network")
    a.wacc_override = 0.07
    changed = record_values(doc, a, evaluate(doc, a), "hashed-network")
    assert original[-1] != changed[-1]


def test_large_source_metadata_is_not_copied_into_stored_results():
    doc = demo_document()
    doc["source"]["note"] = "x" * 700_000
    a = assumptions_from_json(
        {"revenue_growth_rates": [0.05] * 5, "terminal_growth_rate": 0.02, "wacc_override": 0.065}
    )
    values = record_values(doc, a, evaluate(doc, a), "hashed-network")
    assert sum(len(v.encode()) for v in values if isinstance(v, str)) < 1_800_000
    assert "document" not in json.loads(values[-3])["metadata"]
    assert json.loads(values[-4])["source"]["note"] == doc["source"]["note"]


def test_method_migration_preserves_existing_dcf_rows():
    db = sqlite3.connect(":memory:")
    db.executescript(Path("migrations/0001_valuations.sql").read_text())
    db.execute(
        "INSERT INTO valuations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "old-id",
            "2026-10-06",
            "cuig-dcf-v1",
            "DEMO",
            "2026-10-06",
            "synthetic",
            1,
            31.45,
            32.24,
            20,
            0.5725,
            "{}",
            "{}",
            "{}",
            "hash",
            "input",
        ),
    )
    db.executescript(Path("migrations/0002_valuation_methods.sql").read_text())
    assert db.execute("SELECT id,method,intrinsic_value FROM valuations").fetchone() == (
        "old-id",
        "dcf",
        31.45,
    )


@pytest.mark.parametrize("method", ["ddm", "relative"])
def test_new_methods_store_their_own_model_version_and_nullable_intrinsic_value(method):
    from suite_models import suite_sample
    from suite_views import suite_assumptions, suite_evaluate

    doc = suite_sample(method)
    raw = (
        {"dividend_growth_rates": [0.05] * 5, "required_return": 0.07, "terminal_growth_rate": 0.02}
        if method == "ddm"
        else {"included_methods": ["ev_revenue", "ev_ebitda", "pe"]}
    )
    a = suite_assumptions(method, raw)
    r = suite_evaluate(method, doc, a)
    db = sqlite3.connect(":memory:")
    for migration in sorted(Path("migrations").glob("*.sql")):
        db.executescript(migration.read_text())
    db.execute(INSERT_SQL, record_values(doc, a, r, "hashed-network"))
    row = db.execute("SELECT method,model_version,intrinsic_value FROM valuations").fetchone()
    assert row[:2] == (method, r["model_version"])
    assert row[2] == r["intrinsic_value"]


def test_semantically_equal_integer_and_float_inputs_deduplicate():
    from suite_models import suite_sample
    from suite_views import suite_assumptions, suite_evaluate, suite_form, suite_form_payload
    from werkzeug.datastructures import MultiDict

    doc = suite_sample("relative")
    a = suite_assumptions("relative", {"included_methods": ["ev_revenue", "ev_ebitda", "pe"]})
    form = {k: str(v) if v is not None else "" for k, v in suite_form("relative").items()}
    replay, b = suite_form_payload("relative", MultiDict(form))
    assert doc == replay
    one = record_values(doc, a, suite_evaluate("relative", doc, a), "hash")
    two = record_values(replay, b, suite_evaluate("relative", replay, b), "hash")
    assert one[-1] == two[-1]


def test_refreshed_metadata_deduplicates_without_discarding_provenance():
    from copy import deepcopy

    doc = demo_document()
    doc["source"].update(retrieved_at="2026-10-06T12:00:00Z", request_id="request-one")
    doc["historical"][0]["provenance"] = {"request_id": "nested-one", "release_id": "release-one"}
    a = assumptions_from_json(
        {"revenue_growth_rates": [0.05] * 5, "terminal_growth_rate": 0.02, "wacc_override": 0.065}
    )
    refreshed = deepcopy(doc)
    refreshed["source"].update(retrieved_at="2026-10-06T13:00:00Z", request_id="request-two")
    refreshed["historical"][0]["provenance"]["request_id"] = "nested-two"
    one = record_values(doc, a, evaluate(doc, a), "hash")
    two = record_values(refreshed, a, evaluate(refreshed, a), "hash")
    assert one[-1] == two[-1]
    assert json.loads(two[-4]) == refreshed
    refreshed["historical"][0]["provenance"]["release_id"] = "release-two"
    assert record_values(refreshed, a, evaluate(refreshed, a), "hash")[-1] != one[-1]
