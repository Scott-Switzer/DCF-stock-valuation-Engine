"""Independent arithmetic and honest evidence boundaries for real-company QA."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from app import assumptions_from_json, evaluate
from dcf_loader import demo_document
from financial_qa import QA_UNIVERSE, audit_snapshot, capital_cost_check, source_receipts
from reconciliation.reference_dcf import compare_result, reference_dcf
from scripts.validate_universe import ASSUMPTIONS, audit_entry, markdown_report


def aapl():
    return json.loads((Path(__file__).resolve().parents[1] / "reconciliation/aapl_2026-10-09.json").read_text())["document"]


def test_universe_is_exactly_25_unique_companies_with_special_accounting_cases():
    assert len(QA_UNIVERSE) == len(set(QA_UNIVERSE)) == 25
    assert {"JPM", "BAC", "GS", "MRX", "O"} <= set(QA_UNIVERSE)


@pytest.mark.parametrize("overrides", [
    {}, {"wacc_override": 0.08}, {"wacc_override": 0.14},
    {"revenue_growth_rates": [-0.02, 0.01, 0.05, 0.10, 0.03]},
    {"ebit_margins": [0.2, 0.25, 0.3, 0.35, 0.4]},
    {"capex_margins": [0.04] * 5, "da_margins": [0.02] * 5},
    {"nwc_margins": [-0.1, -0.08, -0.06, -0.04, -0.02]},
    {"tax_rates": [0.15, 0.18, 0.2, 0.22, 0.24]},
    {"terminal_growth_rate": 0.03},
    {"terminal_mode": "normalized", "terminal_roic": 0.15},
    {"future_debt": 0, "future_cash": 0, "future_shares": 16e9,
     "future_preferred": 123e6, "future_minority": 456e6, "future_other_assets": 789e6},
])
def test_reference_reconciles_all_flows_and_bridges_across_sensitivities(overrides):
    doc = aapl()
    doc["bridge"].update(preferred_equity=10e6, minority_interest=20e6, other_nonoperating_assets=30e6)
    assumptions = {**deepcopy(ASSUMPTIONS), **overrides}
    expected = reference_dcf(doc, assumptions)
    actual = evaluate(doc, assumptions_from_json(assumptions))
    assert compare_result(expected, actual) == []


def test_reference_has_no_production_engine_dependencies():
    import ast

    source = Path(__file__).resolve().parents[1] / "reconciliation/reference_dcf.py"
    imports = [node for node in ast.walk(ast.parse(source.read_text()))
               if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert all(isinstance(node, ast.Import) and all(name.name == "math" for name in node.names)
               for node in imports)


def test_mismatch_missing_and_nonfinite_outputs_are_failures():
    doc = aapl()
    expected = reference_dcf(doc, ASSUMPTIONS)
    actual = evaluate(doc, assumptions_from_json(ASSUMPTIONS))
    actual["projections"][2]["UFCF"] *= 1.1
    actual["intrinsic_value"] = float("nan")
    del actual["terminal_value"]
    assert {d["field"] for d in compare_result(expected, actual)} == {"ufcf.3", "intrinsic_value", "terminal_value"}


def test_arithmetic_pass_does_not_promote_source_quality_or_unrun_methods():
    result = audit_entry({"ticker": "AAPL", "bundle": {"financials": aapl()}})
    assert result["status"] == "PARTIAL"
    assert result["methods"]["dcf"]["calculation_check"] == "PASS"
    assert result["methods"]["dcf"]["status"] == "PARTIAL"
    assert result["methods"]["ddm"]["status"] == "BLOCKED"
    assert all(not row["independently_source_verified"] for row in result["observations"])
    assert "filing_reconciliation_pending" in {i["code"] for i in result["issues"]}


def test_financial_firm_is_blocked_without_attempting_fcff(monkeypatch):
    doc = aapl()
    doc["source"]["classification"] = {"status": "confirmed", "sic": "6200"}
    monkeypatch.setattr("scripts.validate_universe.reconcile", lambda *_: pytest.fail("Must not run industrial DCF"))
    result = audit_entry({"ticker": "AAPL", "bundle": {"financials": doc}})
    assert result["methods"]["dcf"]["status"] == "BLOCKED"
    assert result["methods"]["dcf"]["calculation_check"] == "NOT_RUN"


def test_missing_financial_observation_fails_without_zero_filling():
    doc = demo_document()
    doc["historical"][0]["capex"] = None
    before = deepcopy(doc)
    result = audit_snapshot(doc)
    assert result["status"] == "FAIL"
    assert result["issues"][0]["code"] == "invalid_contract"
    assert doc == before


def test_future_field_availability_is_integrity_failure():
    doc = aapl()
    period = doc["historical"][0]["period_end"]
    doc["source"]["field_coverage"] = [{"field": f"historical.{period}.revenue", "status": "PPE", "available_at": "2099-01-01"}]
    report = audit_snapshot(doc)
    assert report["status"] == "FAIL"
    assert any(i["code"] == "future_observation" and i["field"].endswith("revenue") for i in report["issues"])


def test_receipts_preserve_values_provenance_and_derived_ebitda_definition():
    doc = aapl()
    period = doc["historical"][0]["period_end"]
    provenance = {"accession": "TEST-ACCESSION", "tag": "OperatingIncomeLoss"}
    doc["source"]["field_coverage"] = [{"field": f"historical.{period}.ebit", "status": "PPE", "provenance": provenance}]
    receipts = {r["field"]: r for r in source_receipts(doc)}
    assert receipts[f"historical.{period}.ebit"]["provenance"] == provenance
    assert receipts[f"historical.{period}.ebit"]["value"] == doc["historical"][0]["ebit"]
    assert "not adjusted EBITDA" in receipts[f"historical.{period}.ebitda"]["provenance"]["definition"]


def test_load_failure_remains_named_block_not_zero_price():
    result = audit_entry({"ticker": "JPM", "error": "Provider lacks annual D&A"})
    assert result["status"] == "BLOCKED"
    assert all(m["status"] == "BLOCKED" for m in result["methods"].values())
    assert "Provider lacks annual D&A" in markdown_report({"captured_at": "test", "companies": [result]})


def test_yahoo_receipts_retain_raw_sign_and_provider_metric():
    doc = aapl()
    doc["historical"][0]["provenance"] = {"CapitalExpenditure": {"metric": "annualCapitalExpenditure", "value": -10959000000}}
    receipt = next(r for r in source_receipts(doc) if r["field"].endswith("2023-09-30.capex"))
    assert receipt["value"] == 10959000000
    assert receipt["provenance"]["provider_records"][0]["value"] == -10959000000


def test_wacc_component_check_distinguishes_parity_mismatch_and_missing():
    doc = aapl()
    assert capital_cost_check(doc)["status"] == "BLOCKED"
    costs = {"risk_free_rate": 0.04, "beta": 1.2, "equity_risk_premium": 0.05,
             "equity_market_value": 800, "debt": 200, "cost_of_debt": 0.06,
             "tax_rate": 0.25, "preferred_equity": 0, "wacc": 0.089}
    doc["source"]["capital_costs"] = costs
    assert capital_cost_check(doc)["status"] == "PASS"
    costs["wacc"] = 0.08
    assert capital_cost_check(doc)["status"] == "FAIL"
    costs["beta"] = None
    assert capital_cost_check(doc)["status"] == "BLOCKED"
