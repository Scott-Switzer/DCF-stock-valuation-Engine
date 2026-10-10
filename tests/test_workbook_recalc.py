"""Recalculate exported workbooks with an independent formula engine.

The `formulas` package evaluates the exported XLSX formulas. Expected values come
from the Python calculation engines and from a closed-form identity, never from
the export code. Overrides change the workbook's input cells, and the expected
values are computed from the matching changed assumptions.
"""

from copy import deepcopy
from dataclasses import asdict, replace

import formulas
import pytest

from app import evaluate
from dcf_code import DCFAssumptions
from dcf_loader import demo_document
from suite_models import DDMAssumptions, RelativeAssumptions, suite_sample
from suite_views import suite_evaluate
from xlsx_export import dcf_workbook, ddm_workbook, relative_workbook

REL = 1e-9
NAME = "book.xlsx"
DELTAS = [-0.01, -0.005, 0, 0.005, 0.01]
SENS = [("Sensitivity", f"{c}{r}") for r in range(2, 7) for c in "BCDEF"]
YEARS = "BCDEF"


def recalc(tmp_path, body, cells, overrides=None):
    """Write the workbook, recalculate it with `formulas`, and return live values."""
    path = tmp_path / NAME
    path.write_bytes(body)
    model = formulas.ExcelModel().loads(str(path)).finish()

    def key(sheet, cell):
        return f"'[{NAME}]{sheet.upper()}'!{cell}"

    outs = {(s, c): key(s, c) for s, c in cells}
    kwargs = {"outputs": list(outs.values())}
    if overrides:
        kwargs["inputs"] = {key(s, c): v for (s, c), v in overrides.items()}
    sol = model.calculate(**kwargs)
    return {sc: _plain(sol[k].value[0][0]) for sc, k in outs.items()}


def _plain(value):
    return value if isinstance(value, str) else float(value)


def assert_cell(got, expected):
    if expected is None:
        assert got == "n/a"
    else:
        assert got == pytest.approx(expected, rel=REL)


def dcf_base():
    return DCFAssumptions(
        revenue_growth_rates=[0.05] * 5,
        terminal_growth_rate=0.02,
        wacc_override=0.065,
        terminal_mode="template",
        ebit_margins=[0.25] * 5,
        da_margins=[0.05] * 5,
        capex_margins=[0.06] * 5,
        nwc_margins=[0.02] * 5,
        tax_rates=[0.21] * 5,
        net_income_margins=[0.18] * 5,
        book_value_margins=[0.5] * 5,
    )


def check_dcf(tmp_path, doc, exported, overrides=None, effective=None):
    effective = effective or exported
    body = dcf_workbook(doc, asdict(exported), evaluate(doc, exported))
    cells = [("Model", "B25"), ("Model", "B35"), ("Model", "B14"), ("Model", "B16")]
    cells += [("Model", f"{c}10") for c in YEARS] + [("Model", f"{c}12") for c in YEARS]
    got = recalc(tmp_path, body, cells + SENS, overrides)

    r = evaluate(doc, effective)
    assert_cell(got[("Model", "B25")], r["intrinsic_value"])
    assert_cell(got[("Model", "B35")], r["target_price_12m"])
    for c, p in zip(YEARS, r["projections"]):
        assert_cell(got[("Model", f"{c}10")], p["UFCF"])
        assert_cell(got[("Model", f"{c}12")], p["PV UFCF"])

    w0, g0 = effective.wacc_override, effective.terminal_growth_rate
    for i, dw in enumerate(DELTAS):
        for j, dg in enumerate(DELTAS):
            try:
                expected = evaluate(
                    doc, replace(effective, wacc_override=w0 + dw, terminal_growth_rate=g0 + dg)
                )["intrinsic_value"]
            except ValueError:
                expected = None
            assert_cell(got[SENS[i * 5 + j]], expected)


def test_dcf_template_base_matches_engine(tmp_path):
    check_dcf(tmp_path, demo_document(), dcf_base())


def test_dcf_normalized_terminal_matches_engine(tmp_path):
    a = replace(dcf_base(), terminal_mode="normalized", terminal_roic=0.12)
    check_dcf(tmp_path, demo_document(), a)


def test_dcf_claims_bridge_matches_engine(tmp_path):
    doc = demo_document()
    doc["bridge"].update(
        short_term_debt=40.0,
        long_term_debt=600.0,
        cash=250.0,
        preferred_equity=200.0,
        minority_interest=150.0,
        other_nonoperating_assets=30.0,
    )
    check_dcf(tmp_path, doc, dcf_base())


def test_dcf_input_change_recalculates_like_engine(tmp_path):
    overrides = {("Assumptions", "B2"): 0.075, ("Assumptions", "B3"): 0.025}
    effective = replace(dcf_base(), wacc_override=0.075, terminal_growth_rate=0.025)
    check_dcf(tmp_path, demo_document(), dcf_base(), overrides, effective)


def ddm_sample():
    return suite_sample("ddm")


def check_ddm(tmp_path, doc, exported, overrides=None, effective=None):
    effective = effective or exported
    body = ddm_workbook(doc, asdict(exported), suite_evaluate("ddm", doc, exported))
    cells = [("Model", "B10"), ("Model", "B16"), ("Model", "B5"), ("Model", "B14")] + SENS
    got = recalc(tmp_path, body, cells, overrides)

    r = suite_evaluate("ddm", doc, effective)
    assert_cell(got[("Model", "B10")], r["intrinsic_value"])
    assert_cell(got[("Model", "B16")], r["target_price_12m"])
    assert_cell(got[("Model", "B5")], r["stage1_pv"])
    assert_cell(got[("Model", "B14")], r["equity_value_12m"])
    for i, row in enumerate(r["sensitivity"]["rows"]):
        for j, value in enumerate(row["values"]):
            assert_cell(got[SENS[i * 5 + j]], value)


def test_ddm_base_matches_engine(tmp_path):
    check_ddm(tmp_path, ddm_sample(), DDMAssumptions([0.05] * 5, 0.07, 0.02))


def test_ddm_future_shares_matches_engine(tmp_path):
    a = DDMAssumptions([0.05] * 5, 0.07, 0.02, future_shares=120.0)
    check_ddm(tmp_path, ddm_sample(), a)


def test_ddm_input_change_recalculates_like_engine(tmp_path):
    overrides = {("Assumptions", "B2"): 0.08, ("Assumptions", "B3"): 0.03}
    check_ddm(
        tmp_path,
        ddm_sample(),
        DDMAssumptions([0.05] * 5, 0.07, 0.02),
        overrides,
        DDMAssumptions([0.05] * 5, 0.08, 0.03),
    )


def test_ddm_zero_growth_matches_closed_form(tmp_path):
    # With zero growth, PV of five years plus a Gordon terminal equals D / Ke exactly.
    doc = ddm_sample()
    a = DDMAssumptions([0.0] * 5, 0.10, 0.0)
    body = ddm_workbook(doc, asdict(a), suite_evaluate("ddm", doc, a))
    got = recalc(tmp_path, body, [("Model", "B10")])
    expected = doc["base_common_dividends"] / 0.10 / doc["market"]["diluted_shares"]
    assert got[("Model", "B10")] == pytest.approx(expected, rel=REL)


def rv_sample(edit=None):
    doc = deepcopy(suite_sample("relative"))
    if edit:
        edit(doc)
    return doc


def check_rv(tmp_path, doc, exported, overrides=None, effective=None):
    effective = effective or exported
    body = relative_workbook(doc, asdict(exported), suite_evaluate("relative", doc, exported))
    cells = [("Model", f"D{row}") for row in range(2, 7)] + [("Model", "B9")]
    got = recalc(tmp_path, body, cells, overrides)

    r = suite_evaluate("relative", doc, effective)
    for row, multiple in zip(range(2, 7), r["multiples"]):
        assert_cell(got[("Model", f"D{row}")], multiple["implied_price"])
    assert_cell(got[("Model", "B9")], r["target_price_12m"])


def test_rv_base_matches_engine(tmp_path):
    check_rv(
        tmp_path,
        rv_sample(),
        RelativeAssumptions(["ev_revenue", "ev_ebitda", "pe"]),
    )


def test_rv_all_methods_match_engine(tmp_path):
    from suite_models import MULTIPLES

    check_rv(tmp_path, rv_sample(), RelativeAssumptions(list(MULTIPLES)))


def test_rv_missing_and_negative_peers_match_engine(tmp_path):
    def edit(doc):
        doc["comparables"][0]["multiples"]["pe"] = None
        doc["comparables"][1]["multiples"]["ev_ebit"] = -4.0

    check_rv(tmp_path, rv_sample(edit), RelativeAssumptions(["ev_ebitda", "pe", "ev_ebit"]))


def test_rv_negative_implied_price_floors_at_zero(tmp_path):
    def edit(doc):
        doc["bridge"]["long_term_debt"] = 90000.0

    check_rv(tmp_path, rv_sample(edit), RelativeAssumptions(["ev_revenue", "pe"]))


def test_rv_preferred_and_minority_claims_match_engine(tmp_path):
    def edit(doc):
        doc["bridge"]["preferred_equity"] = 200.0
        doc["bridge"]["minority_interest"] = 150.0

    check_rv(tmp_path, rv_sample(edit), RelativeAssumptions(["ev_revenue", "ev_ebitda", "pb"]))


def test_rv_method_change_in_workbook_changes_target(tmp_path):
    # Row 5 is P / E. Marking it "no" in the sheet must drop it from the target.
    exported = RelativeAssumptions(["ev_revenue", "ev_ebitda", "pe"])
    check_rv(
        tmp_path,
        rv_sample(),
        exported,
        overrides={("Model", "E5"): "no"},
        effective=RelativeAssumptions(["ev_revenue", "ev_ebitda"]),
    )
