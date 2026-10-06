import pytest
from dcf_code import DCFAssumptions, DCFModel
from test_regressions import financial_data


def test_cuig_explicit_wacc_current_and_twelve_month_formulas():
    # Independent Excel-equivalent literals (end-year timing, unchanged net debt).
    model = DCFModel(financial_data(), DCFAssumptions([0.05] * 5, 0.02, wacc_override=0.065))
    result = model.calculate()
    assert result["intrinsic_value"] == pytest.approx(31.4459549352739, abs=1e-6)
    assert result["target_price_12m"] == pytest.approx(32.2399420060667, abs=1e-6)
    assert result["enterprise_value_12m"] == pytest.approx(
        result["enterprise_value"] * 1.065 - result["projections"][0]["UFCF"]
    )


def test_preferred_claim_is_deducted_from_common_equity():
    d = financial_data()
    d.preferred_equity = [100.0] * 3
    r = DCFModel(d, DCFAssumptions([0.05] * 5, 0.02, wacc_override=0.065)).calculate()
    assert r["intrinsic_value"] == pytest.approx(30.4459549352739, abs=1e-6)


def test_year_specific_operating_drivers_and_future_share_count():
    a = DCFAssumptions(
        [0.0] * 5,
        0.02,
        wacc_override=0.1,
        ebit_margins=[0.1, 0.2, 0.3, 0.4, 0.5],
        future_shares=200,
    )
    r = DCFModel(financial_data(), a).calculate()
    assert [x["EBIT"] for x in r["projections"]] == [100, 200, 300, 400, 500]
    assert r["future_bridge"]["shares"] == 200
    assert r["target_price_12m"] == pytest.approx(max(0, r["equity_value_12m"]) / 200)


def test_sensitivity_invalid_cells_are_null_not_zero():
    m = DCFModel(financial_data(), DCFAssumptions([0.05] * 5, 0.06, wacc_override=0.065))
    m.calculate()
    gs, rows = m.generate_sensitivity_table()
    assert rows[0][1][-1] is None
    assert rows[2][1][2] == pytest.approx(m.result["intrinsic_value"])


def test_normalized_terminal_reinvestment_uses_growth_over_roic():
    a = DCFAssumptions(
        [0.05] * 5, 0.02, wacc_override=0.1, terminal_mode="normalized", terminal_roic=0.1
    )
    r = DCFModel(financial_data(), a).calculate()
    assert r["terminal_fcff"] == pytest.approx(156.21686325)


@pytest.mark.parametrize(
    "changes",
    [
        {"revenue_growth_rates": [0.1] * 4},
        {"tax_rates": [1.1] * 5},
        {"terminal_mode": "normalized", "terminal_roic": 0.01},
        {"future_shares": 0},
    ],
)
def test_invalid_forecast_assumptions_are_rejected(changes):
    kwargs = {
        "revenue_growth_rates": [0.05] * 5,
        "terminal_growth_rate": 0.02,
        "wacc_override": 0.065,
    }
    kwargs.update(changes)
    with pytest.raises(ValueError):
        DCFModel(financial_data(), DCFAssumptions(**kwargs)).calculate()
