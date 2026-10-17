"""Numerical, reconciliation and boundary tests for the FCFE equity valuation lane.

Covers the required validation set: no debt, positive net borrowing, net debt
repayment, negative earnings, negative FCFE, high leverage, debt-policy changes,
missing borrowing information, terminal-value instability, diluted share counts,
and FCFF/FCFE assumption consistency. Expected values are computed independently
with Decimal arithmetic, not by calling the implementation against itself.
"""

from decimal import Decimal, getcontext
import pytest

from fcfe_valuation import fcfe_value

getcontext().prec = 50


def rows(**overrides):
    """Five forecast rows with sane defaults; override any component per year."""
    base = []
    for year in range(1, 6):
        row = {
            "Net Income": 100.0,
            "D&A": 20.0,
            "CapEx": 30.0,
            "Change NWC": 5.0,
        }
        for key, value in overrides.items():
            row[key] = value[year - 1] if isinstance(value, list) else value
        base.append(row)
    return base


def independent_equity(projections, ke, g, shares, borrowing):
    """Exact-rational re-derivation of the FCFE chain in Decimal arithmetic."""
    ke_d, g_d = Decimal(str(ke)), Decimal(str(g))
    total = Decimal(0)
    last_fcfe = None
    for t, (proj, nb) in enumerate(zip(projections, borrowing), start=1):
        fcfe = (
            Decimal(str(proj["Net Income"]))
            + Decimal(str(proj["D&A"]))
            - Decimal(str(proj["CapEx"]))
            - Decimal(str(proj["Change NWC"]))
            + Decimal(str(nb))
        )
        total += fcfe / (Decimal(1) + ke_d) ** t
        last_fcfe = fcfe
    terminal = last_fcfe * (Decimal(1) + g_d) / (ke_d - g_d)
    total += terminal / (Decimal(1) + ke_d) ** len(projections)
    return total / Decimal(str(shares))


def test_no_debt_baseline_matches_independent_decimal():
    projections = rows()
    result = fcfe_value(
        projections,
        cost_of_equity=0.10,
        terminal_growth=0.02,
        shares=50.0,
        net_borrowing=None,
        market_price=25.0,
    )
    expected = independent_equity(projections, 0.10, 0.02, 50.0, [0.0] * 5)
    assert abs(Decimal(str(result["intrinsic_value"])) - expected) / expected < Decimal("1e-12")
    assert result["valuation_basis"] == "equity"
    assert result["net_borrowing_policy"] == "ZERO_NET_BORROWING_ASSUMED"
    # Explicit forecast PV + terminal PV partition the equity value exactly
    assert result["pv_explicit_forecast"] + result["pv_terminal"] == pytest.approx(
        result["equity_value"]
    )
    assert result["equity_value"] / 50.0 == pytest.approx(result["intrinsic_value"])
    assert result["upside"] == pytest.approx(result["intrinsic_value"] / 25.0 - 1)


def test_positive_net_borrowing_raises_equity_value():
    base = fcfe_value(
        rows(), cost_of_equity=0.10, terminal_growth=0.02, shares=50.0, net_borrowing=None
    )
    levered = fcfe_value(
        rows(), cost_of_equity=0.10, terminal_growth=0.02, shares=50.0, net_borrowing=10.0
    )
    assert levered["equity_value"] > base["equity_value"]
    assert levered["net_borrowing_policy"] == "CONSTANT_NET_BORROWING"
    expected = independent_equity(rows(), 0.10, 0.02, 50.0, [10.0] * 5)
    assert abs(Decimal(str(levered["intrinsic_value"])) - expected) / expected < Decimal("1e-12")
    assert any("higher leverage" in w for w in levered["warnings"])


def test_net_debt_repayment_lowers_equity_value():
    base = fcfe_value(
        rows(), cost_of_equity=0.10, terminal_growth=0.02, shares=50.0, net_borrowing=None
    )
    repaying = fcfe_value(
        rows(), cost_of_equity=0.10, terminal_growth=0.02, shares=50.0, net_borrowing=-15.0
    )
    assert repaying["equity_value"] < base["equity_value"]
    assert all(r["net_borrowing"] == -15.0 for r in repaying["rows"])


def test_negative_earnings_and_negative_fcfe():
    projections = rows(**{"Net Income": [-40.0] * 5})
    # Persistently negative equity cash flow: Gordon terminal is refused, not fabricated
    with pytest.raises(ValueError, match="TERMINAL_FCFE_NOT_POSITIVE"):
        fcfe_value(
            projections, cost_of_equity=0.10, terminal_growth=0.02, shares=50.0,
            net_borrowing=None,
        )
    # Early losses with a positive terminal year value fine but carry the warning
    projections = rows(**{"Net Income": [-40.0, -20.0, 40.0, 90.0, 140.0]})
    result = fcfe_value(
        projections, cost_of_equity=0.10, terminal_growth=0.02, shares=50.0,
        net_borrowing=None,
    )
    assert result["rows"][0]["fcfe"] < 0
    assert any("negative FCFE" in w for w in result["warnings"])


def test_negative_fcfe_years_recover_through_financing():
    # Early losses funded by borrowing; later years profitable. Terminal positive.
    projections = rows(**{"Net Income": [-50.0, 20.0, 90.0, 120.0, 150.0]})
    result = fcfe_value(
        projections,
        cost_of_equity=0.10,
        terminal_growth=0.02,
        shares=50.0,
        net_borrowing=[60.0, 30.0, 0.0, -10.0, -10.0],
    )
    assert result["rows"][0]["fcfe"] < 0 < result["rows"][-1]["fcfe"]
    assert result["net_borrowing_policy"] == "EXPLICIT_ANNUAL_NET_BORROWING"
    expected = independent_equity(
        projections, 0.10, 0.02, 50.0, [60.0, 30.0, 0.0, -10.0, -10.0]
    )
    assert abs(Decimal(str(result["intrinsic_value"])) - expected) / expected < Decimal("1e-12")


def test_high_leverage_constant_borrowing_is_reported():
    result = fcfe_value(
        rows(**{"Net Income": [10.0] * 5}),
        cost_of_equity=0.12,
        terminal_growth=0.02,
        shares=50.0,
        net_borrowing=200.0,
    )
    # Value is dominated by financing, and the warning names the leverage effect
    assert result["pv_explicit_forecast"] > 0
    assert any("higher leverage" in w for w in result["warnings"])
    assert any("debt repayment" in w for w in result["warnings"])


def test_missing_borrowing_information_is_explicit():
    result = fcfe_value(
        rows(), cost_of_equity=0.10, terminal_growth=0.02, shares=50.0, net_borrowing=None
    )
    assert result["net_borrowing_policy"] == "ZERO_NET_BORROWING_ASSUMED"
    assert any("zero net borrowing" in w for w in result["warnings"])
    # ...and a malformed policy is refused rather than coerced
    with pytest.raises(ValueError, match="Net borrowing must be"):
        fcfe_value(
            rows(), cost_of_equity=0.10, terminal_growth=0.02, shares=50.0,
            net_borrowing=[1.0, 2.0],
        )


def test_terminal_value_instability_rejected():
    with pytest.raises(ValueError, match="TERMINAL_GROWTH_NOT_FEASIBLE"):
        fcfe_value(
            rows(), cost_of_equity=0.02, terminal_growth=0.02, shares=50.0, net_borrowing=None
        )
    with pytest.raises(ValueError, match="TERMINAL_GROWTH_NOT_FEASIBLE"):
        fcfe_value(
            rows(), cost_of_equity=0.02, terminal_growth=0.03, shares=50.0, net_borrowing=None
        )
    result = fcfe_value(
        rows(), cost_of_equity=0.10, terminal_growth=0.02, shares=50.0, net_borrowing=None
    )
    assert result["pv_terminal"] > 0
    assert result["terminal_value"] == pytest.approx(
        result["terminal_fcfe"] / (0.10 - 0.02)
    )


def test_diluted_share_count_scaling():
    one = fcfe_value(
        rows(), cost_of_equity=0.10, terminal_growth=0.02, shares=1.0, net_borrowing=None
    )
    many = fcfe_value(
        rows(), cost_of_equity=0.10, terminal_growth=0.02, shares=250.0, net_borrowing=None
    )
    assert one["equity_value"] == pytest.approx(many["equity_value"])
    assert one["intrinsic_value"] == pytest.approx(many["intrinsic_value"] * 250.0)
    for bad in (0.0, -5.0, float("nan")):
        with pytest.raises(ValueError):
            fcfe_value(
                rows(), cost_of_equity=0.10, terminal_growth=0.02, shares=bad,
                net_borrowing=None,
            )


def test_debt_policy_change_between_years():
    grow = fcfe_value(
        rows(), cost_of_equity=0.10, terminal_growth=0.02, shares=50.0,
        net_borrowing=[0.0, 0.0, 0.0, 0.0, 0.0],
    )
    switch = fcfe_value(
        rows(), cost_of_equity=0.10, terminal_growth=0.02, shares=50.0,
        net_borrowing=[0.0, 0.0, 0.0, 0.0, 200.0],
    )
    assert switch["equity_value"] > grow["equity_value"]
    assert switch["rows"][4]["fcfe"] - grow["rows"][4]["fcfe"] == pytest.approx(200.0)


def test_fcff_fcfe_reconciliation_identity():
    """With no interest-bearing debt and no net borrowing, FCFE equals UFCF and
    the equity value equals the enterprise value discounted at the same rate."""
    from dcf_code import discount_fcff

    projections = rows()
    ke = 0.10
    g = 0.02
    fcfe = fcfe_value(
        projections, cost_of_equity=ke, terminal_growth=g, shares=1.0, net_borrowing=None
    )
    ufcf_rows = [
        {"Year": i + 1, "UFCF": r["Net Income"] + r["D&A"] - r["CapEx"] - r["Change NWC"],
         "NOPAT": r["Net Income"]}
        for i, r in enumerate(projections)
    ]
    fcff = discount_fcff(ufcf_rows, ke, g)
    assert fcfe["equity_value"] == pytest.approx(fcff["enterprise_value"], rel=1e-12)
    # ...but with net borrowing, the two bases deliberately diverge
    levered = fcfe_value(
        projections, cost_of_equity=ke, terminal_growth=g, shares=1.0, net_borrowing=25.0
    )
    assert levered["equity_value"] != pytest.approx(fcff["enterprise_value"], rel=1e-6)
    assert levered["valuation_basis"] == "equity"


def test_api_returns_equity_basis_and_never_subtracts_net_debt():
    from app import app
    from dcf_loader import demo_document

    doc = demo_document()
    client = app.test_client()
    response = client.post(
        "/api/calculate/fcfe",
        json={
            "financials": doc,
            "assumptions": {
                "revenue_growth_rates": [0.05] * 5,
                "terminal_growth_rate": 0.02,
                "ebit_margins": [0.2] * 5,
                "da_margins": [0.03] * 5,
                "capex_margins": [0.05] * 5,
                "nwc_margins": [0.1] * 5,
                "tax_rates": [0.25] * 5,
                "net_income_margins": [0.15] * 5,
            },
            "cost_of_equity": 0.09,
            "net_borrowing": 0.0,
        },
    )
    assert response.status_code == 200, response.json
    body = response.json
    assert body["method"] == "fcfe"
    assert body["valuation_basis"] == "equity"
    assert body["equity_value"] == pytest.approx(
        body["pv_explicit_forecast"] + body["pv_terminal"]
    )
    assert body["intrinsic_value"] == pytest.approx(
        body["equity_value"] / doc["market"]["diluted_shares"]
    )
    # The equity value already reflects financing: no net-debt bridge is applied.
    assert "equity_bridge" not in body
    assert any("net debt is not subtracted" in w for w in body["warnings"])
    assert body["cost_of_equity_source"] == "explicit"
    assert body["model_limitations"]
