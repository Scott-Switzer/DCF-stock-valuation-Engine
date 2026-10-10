"""Residual income: value = opening book + PV(NI - ke x opening book) + PV(terminal)."""

import pytest

from residual_income import residual_income_value


def test_full_payout_keeps_book_flat_and_residuals_zero():
    # NI equals ke x book every year, so residual income is zero and value is book.
    value = residual_income_value(
        net_income=[10.0] * 5,
        opening_book=100.0,
        cost_of_equity=0.10,
        terminal_growth=0.0,
        shares=2.0,
        payout_ratio=1.0,
    )
    assert value["intrinsic_value"] == pytest.approx(50.0)
    assert [row["residual_income"] for row in value["rows"]] == pytest.approx([0.0] * 5)
    assert [row["book_value"] for row in value["rows"]] == pytest.approx([100.0] * 5)


def test_retained_earnings_match_independent_reference_value():
    # Reference computed by hand: book 100 -> 120 -> ... -> 200, residuals 10, 8, 6, 4, 2,
    # terminal residual 2 / (0.10 - 0) discounted five years.
    value = residual_income_value(
        net_income=[20.0] * 5,
        opening_book=100.0,
        cost_of_equity=0.10,
        terminal_growth=0.0,
        shares=1.0,
        payout_ratio=0.0,
    )
    assert value["intrinsic_value"] == pytest.approx(136.602691, rel=1e-6)
    assert [row["book_value"] for row in value["rows"]] == pytest.approx(
        [120.0, 140.0, 160.0, 180.0, 200.0]
    )


def test_payout_reduces_book_by_distributed_earnings():
    value = residual_income_value(
        net_income=[20.0] * 5,
        opening_book=100.0,
        cost_of_equity=0.10,
        terminal_growth=0.0,
        shares=1.0,
        payout_ratio=0.5,
    )
    # Book grows by half of net income each year under clean surplus.
    assert [row["book_value"] for row in value["rows"]] == pytest.approx(
        [110.0, 120.0, 130.0, 140.0, 150.0]
    )


@pytest.mark.parametrize(
    "change",
    [
        {"cost_of_equity": 0.02, "terminal_growth": 0.02},  # ke must exceed growth
        {"shares": 0.0},
        {"net_income": [1.0] * 4},  # five forecast years are required
        {"payout_ratio": 1.5},
        {"payout_ratio": -0.1},
    ],
)
def test_rejects_invalid_inputs(change):
    args = dict(
        net_income=[10.0] * 5,
        opening_book=100.0,
        cost_of_equity=0.10,
        terminal_growth=0.02,
        shares=1.0,
        payout_ratio=0.0,
    )
    args.update(change)
    with pytest.raises(ValueError):
        residual_income_value(**args)


def test_result_reports_assumptions_and_clean_surplus_warning():
    value = residual_income_value(
        net_income=[20.0] * 5,
        opening_book=100.0,
        cost_of_equity=0.10,
        terminal_growth=0.02,
        shares=1.0,
        payout_ratio=0.0,
    )
    assert value["cost_of_equity"] == 0.10
    assert value["terminal_growth"] == 0.02
    assert any("clean surplus" in w.lower() for w in value["warnings"])
