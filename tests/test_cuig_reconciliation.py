"""Independent interpretation of the supplied workbook's formula text.

This does not claim native Excel recalculation. Only arithmetic, SUM and zero-
payment PV are needed for the referenced DCF cells. No executable eval is used.
"""

import ast
import json
import operator
from pathlib import Path
import re
import pytest
from dcf_code import DCFModel, DCFAssumptions
from test_regressions import financial_data


class WorkbookArithmetic:
    def __init__(self, inputs):
        self.inputs = inputs
        self.formulas = json.loads(
            (Path(__file__).parent / "fixtures/cuig-formulas.json").read_text()
        )["formulas"]

    def cell(self, key):
        if key in self.inputs:
            return self.inputs[key]
        formula = self.formulas[key].lstrip("=").replace("$", "")

        def expand(match):
            col1, row1, col2, row2 = match.groups()
            assert col1 == col2 or row1 == row2
            cells = [
                f"{chr(col)}{row}"
                for col in range(ord(col1), ord(col2) + 1)
                for row in range(int(row1), int(row2) + 1)
            ]
            return ",".join(cells)

        formula = re.sub(r"([A-Z])(\d+):([A-Z])(\d+)", expand, formula)
        return self.node(ast.parse(formula, mode="eval").body)

    def node(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name):
            return self.cell(node.id)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -self.node(node.operand)
        if isinstance(node, ast.BinOp):
            return {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
            }[type(node.op)](self.node(node.left), self.node(node.right))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            args = [self.node(arg) for arg in node.args]
            if node.func.id == "SUM":
                return sum(args)
            if node.func.id == "PV":
                rate, periods, payment, future, timing = args
                assert payment == 0 and timing == 0
                return -future / (1 + rate) ** periods
        raise AssertionError(f"Unsupported reference formula {ast.dump(node)}")


@pytest.mark.parametrize("growths", [[0.05] * 5, [0.12, 0.08, 0.06, 0.04, 0.03]])
def test_current_and_twelve_month_values_match_supplied_cuig_formulas(growths):
    inputs = {
        "E11": 1000.0,
        "E29": 100.0,
        "I3": 0.065,
        "C58": 0.02,
        "C71": 50.0,
        "C72": 150.0,
        "C73": 100.0,
        "C80": 100.0,
        "F9": 1,
    }
    # Vary each driver's later-year assumption to catch accidental constant use.
    ebit = [0.20, 0.22, 0.24, 0.23, 0.21]
    tax = [0.25, 0.24, 0.23, 0.22, 0.21]
    capex = [0.05, 0.06, 0.06, 0.05, 0.04]
    da = [0.03, 0.04, 0.04, 0.03, 0.03]
    nwc = [0.10, 0.11, 0.12, 0.10, 0.09]
    for i, column in enumerate("FGHIJ"):
        for row, value in [
            (12, growths[i]),
            (15, ebit[i]),
            (24, capex[i]),
            (27, da[i]),
            (30, nwc[i]),
            (35, tax[i]),
        ]:
            inputs[f"{column}{row}"] = value
    workbook = WorkbookArithmetic(inputs)
    model = DCFModel(
        financial_data(),
        DCFAssumptions(
            growths,
            0.02,
            wacc_override=0.065,
            ebit_margins=ebit,
            tax_rates=tax,
            capex_margins=capex,
            da_margins=da,
            nwc_margins=nwc,
        ),
    )
    result = model.calculate()
    assert result["intrinsic_value"] == pytest.approx(workbook.cell("C82"), rel=1e-12)
    assert result["target_price_12m"] == pytest.approx(workbook.cell("I82"), rel=1e-12)
    for column, forecast in zip("FGHIJ", result["projections"]):
        assert forecast["UFCF"] == pytest.approx(workbook.cell(f"{column}46"))
        assert forecast["PV UFCF"] == pytest.approx(workbook.cell(f"{column}47"))
