from dataclasses import fields
import pytest
from dcf_code import FinancialData, DCFModel, DCFAssumptions
from app import validate_growth_rate


def financial_data():
    vals = {
        f.name: [0.0, 0.0, 0.0]
        for f in fields(FinancialData)
        if f.name
        in {
            "revenue",
            "ebit",
            "ebitda",
            "net_income",
            "effective_tax_rate",
            "interest_expense",
            "current_assets",
            "current_liabilities",
            "cash_and_equivalents",
            "short_term_debt",
            "long_term_debt",
            "total_debt",
            "total_assets",
            "total_liabilities",
            "property_plant_equipment_net",
            "preferred_equity",
            "d_and_a",
            "capex",
            "preferred_dividends",
        }
    }
    vals.update(
        years=["2023", "2024", "2025"],
        revenue=[1000.0] * 3,
        ebit=[200.0] * 3,
        net_income=[150.0] * 3,
        ebitda=[230.0] * 3,
        d_and_a=[30.0] * 3,
        capex=[50.0] * 3,
        effective_tax_rate=[0.25] * 3,
        current_assets=[300.0] * 3,
        current_liabilities=[150.0] * 3,
        cash_and_equivalents=[100.0] * 3,
        short_term_debt=[50.0] * 3,
        long_term_debt=[150.0] * 3,
        total_debt=[200.0] * 3,
        interest_expense=[10.0] * 3,
        shares_outstanding=100.0,
        beta=1.0,
        stock_price=20.0,
        market_cap=2000.0,
        risk_free_rate=0.04,
        market_return_rate=0.10,
    )
    return FinancialData(**vals)


@pytest.mark.parametrize("value", ["abc", "NaN", "inf", 5, -0.9])
def test_bad_growth_is_rejected_instead_of_changed(value):
    with pytest.raises(ValueError):
        validate_growth_rate(value)


def test_invalid_terminal_growth_stops_valuation():
    with pytest.raises(ValueError, match="growth"):
        DCFModel(financial_data(), DCFAssumptions([0.05] * 5, 0.15)).calculate_intrinsic_value()


def test_zero_revenue_stops_valuation():
    d = financial_data()
    d.revenue = [0.0] * 3
    with pytest.raises(ValueError, match="revenue"):
        DCFModel(d, DCFAssumptions([0.05] * 5, 0.02)).calculate_intrinsic_value()


def test_zero_shares_stops_valuation():
    d = financial_data()
    d.shares_outstanding = 0
    with pytest.raises(ValueError, match="shares"):
        DCFModel(d, DCFAssumptions([0.05] * 5, 0.02)).calculate_intrinsic_value()


def test_present_value_is_the_headline_not_twelve_month_price():
    # Independent Excel-equivalent calculation for fixture, WACC 9.431818%.
    assert DCFModel(
        financial_data(), DCFAssumptions([0.05] * 5, 0.02)
    ).calculate_intrinsic_value() == pytest.approx(18.51976860220612, abs=1e-5)
