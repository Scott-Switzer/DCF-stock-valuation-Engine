import json
import sqlite3
from pathlib import Path
from app import assumptions_from_json, evaluate
from dcf_loader import demo_document
from valuation_records import INSERT_SQL, record_values


def test_database_records_preserve_inputs_flag_samples_and_deduplicate():
    db = sqlite3.connect(":memory:")
    db.executescript(Path("migrations/0001_valuations.sql").read_text())
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
