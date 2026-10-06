"""Independently interpret the supplied DDM/RV formula text, not engine equations."""

import ast
import json
from pathlib import Path
import re
import pytest
from test_cuig_reconciliation import WorkbookArithmetic
from suite_models import DDMModel, DDMAssumptions, RelativeModel, RelativeAssumptions, suite_sample


class SuiteWorkbook(WorkbookArithmetic):
    def __init__(self, sheet, inputs):
        self.inputs = inputs
        raw = json.loads(Path("tests/fixtures/cuig-suite-formulas.json").read_text())[sheet]
        raw = {k: v.replace("'Relative Valuation'!", "") for k, v in raw.items()}
        self.formulas = {
            k: re.sub(
                r"(?<![<>=])=(?!=)",
                "==",
                re.sub(r"'DCF - GGM'!([A-Z]+\d+)", r"DCF_\1", v.lstrip("=")).replace(
                    "DDM!", "DDM_"
                ),
            )
            for k, v in raw.items()
        }

    def node(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Compare):
            assert len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq)
            return self.node(node.left) == self.node(node.comparators[0])
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "IF":
                return self.node(node.args[1] if self.node(node.args[0]) else node.args[2])
            if node.func.id == "ISBLANK":
                return self.node(node.args[0]) is None
            if node.func.id == "AVERAGE":
                values = [self.node(arg) for arg in node.args]
                values = [v for v in values if v is not None]
                return sum(values) / len(values)
            if node.func.id == "COUNTIF":
                args = [self.node(arg) for arg in node.args]
                return sum(v == args[-1] for v in args[:-1])
        return super().node(node)


@pytest.mark.parametrize("growths", [[0.05] * 5, [0.08, 0.06, 0.04, 0.03, 0.02]])
def test_ddm_current_and_12m_match_workbook_cells(growths):
    doc = suite_sample("ddm")
    a = DDMAssumptions(growths, 0.07, 0.02)
    inputs = {"E17": 100, "C25": 0.07, "C40": 0.02, "C52": 100}
    for i, c in enumerate("FGHIJ"):
        inputs[c + "18"] = growths[i]
        inputs[c + "29"] = i + 1
    book = SuiteWorkbook("DDM", inputs)
    r = DDMModel(doc, a).calculate()
    assert r["intrinsic_value"] == pytest.approx(book.cell("C54"), rel=1e-12)
    assert r["target_price_12m"] == pytest.approx(book.cell("I54"), rel=1e-12)
    for c, p in zip("FGHIJ", r["projections"]):
        assert p["dividends"] == pytest.approx(book.cell(c + "17"))


@pytest.mark.parametrize("selected", [["ev_revenue", "ev_ebitda", "pe"], ["ev_ebit", "pb"]])
def test_relative_selection_and_forward_target_match_workbook_cells(selected):
    doc = suite_sample("relative")
    a = RelativeAssumptions(selected)
    inputs = {
        "DCF_C74": 100,
        "DCF_C80": 100,
        "DDM_F20": None,
        "DCF_F11": 1050,
        "DCF_F20": 241.5,
        "DCF_F14": 210,
        "DCF_F17": 157.5,
        "DCF_F32": 525,
    }
    for col, key in zip("CDEFG", ["ev_revenue", "ev_ebitda", "ev_ebit", "pe", "pb"]):
        inputs[col + "13"] = "Yes" if key in selected else "No"
        for i, p in enumerate(doc["comparables"]):
            inputs[f"{col}{i + 6}"] = p["multiples"][key]
    book = SuiteWorkbook("Relative Valuation", inputs)
    r = RelativeModel(doc, a).calculate()
    assert r["target_price_12m"] == pytest.approx(book.cell("C15"), rel=1e-12)
    for col, row in zip("CDEFG", r["multiples"]):
        assert row["implied_price"] == pytest.approx(book.cell(col + "12"))
