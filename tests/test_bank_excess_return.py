"""Independent numerical tests for the bank/financial-institution excess-return lane.

Expected values are derived with exact Decimal arithmetic from the textbook
definitions. Includes the cross-model identity: with identical inputs the bank
excess-return value equals the existing residual-income value (they are the
same NPV), and the bank-specific validation layer (tangible basis, sustainable
growth, regulatory retention, credit-drag labeling) is tested separately.
"""

from decimal import Decimal, getcontext
import pytest

from bank_excess_return import bank_excess_return_value

getcontext().prec = 50


def independent_equity(ni, book0, ke, g, payout, drag=None):
    """Exact-rational excess-return chain in Decimal arithmetic."""
    d = Decimal
    book = d(str(book0))
    ke_d, g_d, payout_d = d(str(ke)), d(str(g)), d(str(payout))
    total = book
    last_excess = None
    for t, earnings in enumerate(ni, start=1):
        e = d(str(earnings))
        if drag is not None:
            e -= d(str(drag[t - 1]))
        excess = e - ke_d * book
        total += excess / (Decimal(1) + ke_d) ** t
        book = book + e * (1 - payout_d)
        last_excess = excess
    terminal = last_excess * (Decimal(1) + g_d) / (ke_d - g_d)
    total += terminal / (Decimal(1) + ke_d) ** len(ni)
    return total


def test_baseline_matches_independent_decimal():
    ni = [120.0, 128.0, 136.0, 144.0, 152.0]
    result = bank_excess_return_value(
        ni,
        opening_book=1000.0,
        intangible_assets=0.0,
        cost_of_equity=0.10,
        terminal_growth=0.02,
        shares=100.0,
        payout_ratio=0.40,
    )
    expected = independent_equity(ni, 1000.0, 0.10, 0.02, 0.40)
    assert abs(Decimal(str(result["equity_value"])) - expected) / expected < Decimal("1e-12")
    assert result["valuation_basis"] == "equity"
    assert result["company_type"] == "financial_institution"
    assert result["equity_basis"] == "TANGIBLE_COMMON"
    assert result["equity_value"] / 100.0 == pytest.approx(result["intrinsic_value"])
    # Clean surplus book roll
    assert result["rows"][0]["closing_book"] == pytest.approx(1000.0 + 120.0 * 0.60)


def test_roe_equals_ke_gives_value_equal_to_book():
    """When ROE == cost of equity every excess return is zero: equity == book.

    Earnings must be generated on opening capital (NI_t = ROE x Book_{t-1});
    with a 50% payout the book grows 5%/yr and earnings follow it, so every
    year's excess return and the terminal excess return are exactly zero.
    """
    ke, roe, payout = 0.10, 0.10, 0.5
    ni = []
    book = 1000.0
    for _ in range(5):
        earnings = roe * book
        ni.append(earnings)
        book += earnings * (1 - payout)
    result = bank_excess_return_value(
        ni,
        opening_book=1000.0,
        intangible_assets=0.0,
        cost_of_equity=ke,
        terminal_growth=0.02,
        shares=100.0,
        payout_ratio=payout,
    )
    assert result["equity_value"] == pytest.approx(1000.0, rel=1e-12)
    assert all(abs(r["excess_return"]) < 1e-9 for r in result["rows"])
    assert result["pv_terminal_excess_return"] == pytest.approx(0.0, abs=1e-9)


def test_roe_above_ke_creates_value_above_book():
    ni = [150.0] * 5  # 15% ROE on 1000 book
    result = bank_excess_return_value(
        ni,
        opening_book=1000.0,
        intangible_assets=0.0,
        cost_of_equity=0.10,
        terminal_growth=0.02,
        shares=100.0,
        payout_ratio=0.5,
    )
    assert result["equity_value"] > 1000.0
    assert all(r["excess_return"] > 0 for r in result["rows"])


def test_roe_below_ke_destroys_value_below_book():
    ni = [50.0] * 5  # 5% ROE
    result = bank_excess_return_value(
        ni,
        opening_book=1000.0,
        intangible_assets=0.0,
        cost_of_equity=0.10,
        terminal_growth=0.02,
        shares=100.0,
        payout_ratio=0.5,
    )
    assert result["equity_value"] < 1000.0
    assert all(r["excess_return"] < 0 for r in result["rows"])


def test_tangible_basis_requires_explicit_intangibles():
    with pytest.raises(ValueError, match="explicit intangible_assets"):
        bank_excess_return_value(
            [100.0] * 5,
            opening_book=1000.0,
            cost_of_equity=0.10,
            terminal_growth=0.02,
            shares=100.0,
        )
    result = bank_excess_return_value(
        [100.0] * 5,
        opening_book=1000.0,
        intangible_assets=200.0,
        cost_of_equity=0.10,
        terminal_growth=0.02,
        shares=100.0,
    )
    assert result["opening_tangible_book"] == pytest.approx(800.0)
    assert result["equity_basis"] == "TANGIBLE_COMMON"

    # Total-book basis is labeled distinctly, never silently mixed
    total = bank_excess_return_value(
        [100.0] * 5,
        opening_book=1000.0,
        equity_basis="TOTAL_BOOK",
        cost_of_equity=0.10,
        terminal_growth=0.02,
        shares=100.0,
    )
    assert total["equity_basis"] == "TOTAL_BOOK"
    assert total["equity_value"] != pytest.approx(result["equity_value"])


def test_negative_equity_rejected():
    with pytest.raises(ValueError, match="positive after the tangible adjustment"):
        bank_excess_return_value(
            [100.0] * 5,
            opening_book=150.0,
            intangible_assets=200.0,
            cost_of_equity=0.10,
            terminal_growth=0.02,
            shares=100.0,
        )


def test_missing_forecast_year_fails_explicitly():
    with pytest.raises(ValueError, match="substituted zero"):
        bank_excess_return_value(
            [100.0, None, 100.0, 100.0, 100.0],
            opening_book=1000.0,
            intangible_assets=0.0,
            cost_of_equity=0.10,
            terminal_growth=0.02,
            shares=100.0,
        )


def test_terminal_growth_sustainability_check():
    # Constant NI 50 on a growing book: terminal-year ROE = 50/1100 ~ 4.55%,
    # retention 50% -> sustainable growth ~2.27%; 3% terminal growth is rejected.
    ni = [50.0] * 5
    expected_sustainable = 0.5 * 50.0 / 1100.0
    with pytest.raises(ValueError, match="TERMINAL_GROWTH_NOT_SUSTAINABLE"):
        bank_excess_return_value(
            ni,
            opening_book=1000.0,
            intangible_assets=0.0,
            cost_of_equity=0.10,
            terminal_growth=0.03,
            shares=100.0,
            payout_ratio=0.5,
        )
    result = bank_excess_return_value(
        ni,
        opening_book=1000.0,
        intangible_assets=0.0,
        cost_of_equity=0.10,
        terminal_growth=0.03,
        shares=100.0,
        payout_ratio=0.5,
        allow_unsustainable_terminal_growth=True,
    )
    assert any("exceeds sustainable growth" in w for w in result["warnings"])
    assert result["sustainable_growth"] == pytest.approx(expected_sustainable)
    # A terminal growth within sustainable growth passes without an override
    within = bank_excess_return_value(
        ni,
        opening_book=1000.0,
        intangible_assets=0.0,
        cost_of_equity=0.10,
        terminal_growth=0.02,
        shares=100.0,
        payout_ratio=0.5,
    )
    assert within["sustainable_growth"] > within["terminal_growth"]


def test_regulatory_minimum_retention_constraint():
    ni = [150.0] * 5
    with pytest.raises(ValueError, match="CAPITAL_CONSTRAINT_VIOLATION"):
        bank_excess_return_value(
            ni,
            opening_book=1000.0,
            intangible_assets=0.0,
            cost_of_equity=0.10,
            terminal_growth=0.02,
            shares=100.0,
            payout_ratio=0.8,  # retention 20% < required 40%
            minimum_retention=0.40,
        )
    result = bank_excess_return_value(
        ni,
        opening_book=1000.0,
        intangible_assets=0.0,
        cost_of_equity=0.10,
        terminal_growth=0.02,
        shares=100.0,
        payout_ratio=0.5,
        minimum_retention=0.40,
        regulatory_capital={"cet1_ratio": 12.5, "total_risk_based_capital_ratio": 14.0},
    )
    assert result["regulatory_capital_metadata"]["cet1_ratio"] == 12.5
    assert any("Regulatory capital constraint enforced" in w for w in result["warnings"])


def test_credit_provision_drag_is_explicit_and_labeled():
    ni = [120.0] * 5
    without = bank_excess_return_value(
        ni,
        opening_book=1000.0,
        intangible_assets=0.0,
        cost_of_equity=0.10,
        terminal_growth=0.02,
        shares=100.0,
        payout_ratio=0.4,
    )
    assert without["credit_provision_mode"] == "NOT_MODELED"
    assert any("NOT modeled" in w for w in without["warnings"])
    with_drag = bank_excess_return_value(
        ni,
        opening_book=1000.0,
        intangible_assets=0.0,
        cost_of_equity=0.10,
        terminal_growth=0.02,
        shares=100.0,
        payout_ratio=0.4,
        credit_provision_drag=[30.0] * 5,
    )
    assert with_drag["credit_provision_mode"] == "EXPLICIT_SCHEDULE"
    assert with_drag["equity_value"] < without["equity_value"]
    expected = independent_equity(ni, 1000.0, 0.10, 0.02, 0.4, drag=[30.0] * 5)
    assert abs(Decimal(str(with_drag["equity_value"])) - expected) / expected < Decimal("1e-12")


def test_preferred_claims_rejected():
    with pytest.raises(ValueError, match="Preferred claims"):
        bank_excess_return_value(
            [100.0] * 5,
            opening_book=1000.0,
            intangible_assets=0.0,
            cost_of_equity=0.10,
            terminal_growth=0.02,
            shares=100.0,
            preferred_equity=50.0,
        )


def test_terminal_instability_rejected():
    with pytest.raises(ValueError, match="TERMINAL_GROWTH_NOT_FEASIBLE"):
        bank_excess_return_value(
            [100.0] * 5,
            opening_book=1000.0,
            intangible_assets=0.0,
            cost_of_equity=0.02,
            terminal_growth=0.02,
            shares=100.0,
        )


def test_cross_model_identity_with_residual_income():
    """Bank excess returns and residual income are the same NPV: with identical
    inputs the two engines must agree exactly."""
    from residual_income import residual_income_value

    ni = [120.0, 128.0, 136.0, 144.0, 152.0]
    bank = bank_excess_return_value(
        ni,
        opening_book=1000.0,
        intangible_assets=0.0,
        cost_of_equity=0.10,
        terminal_growth=0.02,
        shares=100.0,
        payout_ratio=0.4,
    )
    ri = residual_income_value(
        net_income=ni,
        opening_book=1000.0,
        cost_of_equity=0.10,
        terminal_growth=0.02,
        shares=100.0,
        payout_ratio=0.4,
    )
    assert bank["equity_value"] == pytest.approx(ri["equity_value"], rel=1e-12)
    assert bank["intrinsic_value"] == pytest.approx(ri["intrinsic_value"], rel=1e-12)


def test_api_endpoint_returns_bank_lane():
    from app import app
    from dcf_loader import demo_document

    doc = demo_document()
    client = app.test_client()
    response = client.post(
        "/api/calculate/bank-excess-return",
        json={
            "financials": doc,
            "net_income": [150.0, 158.0, 166.0, 174.0, 182.0],
            "cost_of_equity": 0.11,
            "terminal_growth": 0.02,
            "payout_ratio": 0.35,
            "equity_basis": "TANGIBLE_COMMON",
            "intangible_assets": 0.0,
            "regulatory_capital": {"cet1_ratio": 13.2},
        },
    )
    assert response.status_code == 200, response.json
    body = response.json
    assert body["method"] == "bank_excess_return"
    assert body["valuation_basis"] == "equity"
    assert body["company_type"] == "financial_institution"
    assert body["equity_value"] == pytest.approx(
        body["opening_tangible_book"]
        + body["pv_explicit_excess_returns"]
        + body["pv_terminal_excess_return"]
    )
    assert body["credit_provision_mode"] == "NOT_MODELED"
    assert body["regulatory_capital_metadata"]["cet1_ratio"] == 13.2
