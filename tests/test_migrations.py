"""Migrations apply in order to a fresh database and keep existing valuations."""

import sqlite3
from pathlib import Path

import pytest

MIGRATIONS = sorted((Path(__file__).resolve().parents[1] / "migrations").glob("*.sql"))


def migrate_up_to(db, last_name):
    # Apply each pending migration exactly once, tracked by PRAGMA user_version.
    names = [path.name for path in MIGRATIONS]
    if last_name not in names:
        raise AssertionError(f"migration not found: {last_name}")
    applied = db.execute("PRAGMA user_version").fetchone()[0]
    for index in range(applied, names.index(last_name) + 1):
        db.executescript(MIGRATIONS[index].read_text())
        db.execute(f"PRAGMA user_version = {index + 1}")


def insert_valuation(db, id_, method=None):
    columns = (
        "id, created_at, model_version, ticker, valuation_date, source_kind, is_demo, "
        "intrinsic_value, target_price_12m, market_price, upside, assumptions_json, "
        "financials_json, result_json, client_hash, input_hash"
    )
    values = (id_, "2026-10-09T00:00:00Z", "v", "AAPL", "2026-10-09", "api", 0,
              10.0, 11.0, 9.0, 0.1, "{}", "{}", "{}", "client", f"input-{id_}")
    if method is None:
        db.execute(f"INSERT INTO valuations ({columns}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
    else:
        db.execute(
            f"INSERT INTO valuations ({columns}, method) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (*values, method),
        )


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()


def test_legacy_rows_survive_and_residual_is_accepted(db):
    migrate_up_to(db, "0006_share_controls.sql")
    insert_valuation(db, "legacy-dcf")  # created before the method column existed
    db.commit()

    migrate_up_to(db, "0007_residual_method.sql")

    methods = dict(db.execute("SELECT id, method FROM valuations").fetchall())
    assert methods == {"legacy-dcf": "dcf"}
    insert_valuation(db, "new-residual", method="residual")
    assert db.execute(
        "SELECT method FROM valuations WHERE id = 'new-residual'"
    ).fetchone() == ("residual",)


def test_unknown_method_is_still_rejected(db):
    migrate_up_to(db, "0007_residual_method.sql")
    with pytest.raises(sqlite3.IntegrityError):
        insert_valuation(db, "bad", method="gordon-magic")


def test_every_valuation_index_is_recreated(db):
    migrate_up_to(db, "0007_residual_method.sql")
    indexes = {
        row[1]
        for row in db.execute("PRAGMA index_list('valuations')").fetchall()
    }
    assert {
        "valuations_ticker_date",
        "valuations_method_date",
        "valuations_owner_created",
    } <= indexes
