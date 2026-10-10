"""Independent reconciliation of an AAPL DCF on SEC-sourced FY2023-FY2025 inputs.

The expected values in reconciliation/aapl_2026-10-09.json come from a standalone
calculation written from the documented formulas. The test recomputes them here
without importing dcf_code, then checks the app's engine and the exported workbook.
"""

import json
from dataclasses import asdict
from pathlib import Path

import formulas
import pytest

from app import evaluate
from compare import coerce_dcf_assumptions
from dcf_loader import parse_document
from xlsx_export import dcf_workbook

FIXTURE = Path(__file__).resolve().parent.parent / "reconciliation" / "aapl_2026-10-09.json"
REL = 1e-9


def load_fixture():
    return json.loads(FIXTURE.read_text())


def independent_dcf(doc, wacc, growth, terminal_growth, shares_millions):
    """Five-year FCFF DCF from the document's three historical years.

    Ratios are three-year averages; tax is the latest effective rate; NWC is
    (current assets - cash) - (current liabilities - short-term debt), in USD millions.
    """
    rows = doc["historical"]
    bridge = doc["bridge"]
    m = 1e6

    def avg(fn):
        return sum(fn(r) for r in rows) / len(rows)

    m_ebit = avg(lambda r: r["ebit"] / r["revenue"])
    m_da = avg(lambda r: r["d_and_a"] / r["revenue"])
    m_capex = avg(lambda r: r["capex"] / r["revenue"])
    m_nwc = avg(lambda r: r["nwc"] / r["revenue"])
    tax = rows[-1]["tax_rate"]

    rev = rows[-1]["revenue"]
    prev_nwc = rows[-1]["nwc"]
    flows = []
    for _ in range(5):
        rev *= 1 + growth
        ebit = rev * m_ebit
        ufcf = ebit - ebit * tax + rev * m_da - rev * m_capex - (rev * m_nwc - prev_nwc)
        flows.append(ufcf / m)
        prev_nwc = rev * m_nwc

    tv = flows[-1] * (1 + terminal_growth) / (wacc - terminal_growth)
    ev = sum(f / (1 + wacc) ** (i + 1) for i, f in enumerate(flows)) + tv / (1 + wacc) ** 5
    debt = (bridge["short_term_debt"] + bridge["long_term_debt"]) / m
    cash = bridge["cash"] / m
    equity = ev - debt + cash
    ev12 = sum(f / (1 + wacc) ** i for i, f in enumerate(flows[1:], start=1)) + tv / (
        1 + wacc
    ) ** 4
    equity12 = ev12 - debt + cash
    return {
        "ufcf": flows,
        "tv": tv,
        "ev": ev,
        "equity": equity,
        "intrinsic": max(0, equity) / shares_millions,
        "ev12": ev12,
        "equity12": equity12,
        "target12": max(0, equity12) / shares_millions,
        "drivers": {
            "ebit_margin": m_ebit,
            "da_margin": m_da,
            "capex_margin": m_capex,
            "nwc_margin": m_nwc,
            "tax_rate": tax,
        },
    }


def test_fixture_document_is_valid_for_the_engine():
    fixture = load_fixture()
    parse_document(json.loads(json.dumps(fixture["document"])))


def test_independent_calculation_matches_fixture_expectations():
    fixture = load_fixture()
    shared = fixture["shared_inputs"]
    got = independent_dcf(
        fixture["document"],
        shared["wacc"],
        shared["revenue_growth"][0],
        shared["terminal_growth"],
        shared["shares_millions"],
    )
    want = fixture["expected"]
    assert got["ufcf"] == pytest.approx(want["ufcf_millions"], rel=REL)
    assert got["tv"] == pytest.approx(want["terminal_value_millions"], rel=REL)
    assert got["ev"] == pytest.approx(want["enterprise_value_millions"], rel=REL)
    assert got["equity"] == pytest.approx(want["equity_value_millions"], rel=REL)
    assert got["intrinsic"] == pytest.approx(want["intrinsic_value_per_share"], rel=REL)
    assert got["ev12"] == pytest.approx(want["enterprise_value_12m_millions"], rel=REL)
    assert got["equity12"] == pytest.approx(want["equity_value_12m_millions"], rel=REL)
    assert got["target12"] == pytest.approx(want["target_price_12m"], rel=REL)
    for key, value in want["historical_avg_drivers"].items():
        assert got["drivers"][key] == pytest.approx(value, rel=REL)


def test_app_engine_matches_independent_reconciliation():
    fixture = load_fixture()
    doc = fixture["document"]
    assumptions, custom = coerce_dcf_assumptions(doc, None, fixture["shared_inputs"]["wacc"])
    assert custom is False
    result = evaluate(doc, assumptions)
    want = fixture["expected"]

    assert result["intrinsic_value"] == pytest.approx(want["intrinsic_value_per_share"], rel=REL)
    assert result["target_price_12m"] == pytest.approx(want["target_price_12m"], rel=REL)
    assert result["enterprise_value"] / 1e6 == pytest.approx(want["enterprise_value_millions"], rel=REL)
    assert result["equity_value"] / 1e6 == pytest.approx(want["equity_value_millions"], rel=REL)
    for row, expected in zip(result["projections"], want["ufcf_millions"]):
        assert row["UFCF"] / 1e6 == pytest.approx(expected, rel=REL)


def test_exported_workbook_recalculates_to_the_same_snapshot(tmp_path):
    fixture = load_fixture()
    doc = fixture["document"]
    assumptions, _ = coerce_dcf_assumptions(doc, None, fixture["shared_inputs"]["wacc"])
    result = evaluate(doc, assumptions)
    body = dcf_workbook(doc, asdict(assumptions), result)
    path = tmp_path / "AAPL-dcf.xlsx"
    path.write_bytes(body)

    model = formulas.ExcelModel().loads(str(path)).finish()

    def cell(address):
        key = f"'[{path.name}]MODEL'!{address}"
        return float(model.calculate(outputs=[key])[key].value[0][0])

    want = fixture["expected"]
    assert cell("B25") == pytest.approx(want["intrinsic_value_per_share"], rel=REL)
    assert cell("B35") == pytest.approx(want["target_price_12m"], rel=REL)
    for col, expected in zip("BCDEF", want["ufcf_millions"]):
        assert cell(f"{col}10") / 1e6 == pytest.approx(expected, rel=REL)
