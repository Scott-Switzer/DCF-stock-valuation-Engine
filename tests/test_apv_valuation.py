"""Independent numerical and boundary tests for the APV valuation lane.

Expected values are derived with exact Decimal arithmetic from the textbook
definitions, not by calling the implementation against itself. Includes the
APV/WACC reconciliation identity where the assumptions permit it: with a fixed
debt schedule, shields discounted at the pre-tax cost of debt (MM fixed-debt
convention), and no distress costs, APV equals the WACC-based firm value when
WACC is built from the same capital structure, cost of debt and tax rate.
"""

from decimal import Decimal, getcontext
import pytest

from apv_valuation import apv_value

getcontext().prec = 50


def rows(ufcf=100.0, ebit=150.0):
    return [{"UFCF": ufcf, "EBIT": ebit, "Year": y} for y in range(1, 6)]


def independent_unlevered(projections, rho, g):
    rho_d, g_d = Decimal(str(rho)), Decimal(str(g))
    total = Decimal(0)
    for t, proj in enumerate(projections, start=1):
        total += Decimal(str(proj["UFCF"])) / (Decimal(1) + rho_d) ** t
    terminal = Decimal(str(projections[-1]["UFCF"])) * (Decimal(1) + g_d) / (rho_d - g_d)
    total += terminal / (Decimal(1) + rho_d) ** len(projections)
    return total


def test_no_debt_apv_equals_unlevered_value():
    result = apv_value(
        rows(),
        unlevered_cost_of_capital=0.10,
        terminal_growth=0.02,
        tax_rate=0.25,
        debt_schedule=None,
        shield_discount_convention="fixed_debt_kd",
        distress_scenarios=None,
    )
    expected = independent_unlevered(rows(), 0.10, 0.02)
    assert abs(Decimal(str(result["adjusted_firm_value"])) - expected) / expected < Decimal("1e-12")
    assert result["pv_tax_shields"] == 0.0
    assert result["pv_expected_distress_costs"] == 0.0
    assert result["adjusted_firm_value"] == pytest.approx(result["unlevered_firm_value"])
    assert result["distress_treatment"] == "DISTRESS_EXCLUDED_BY_ASSUMPTION"
    assert any("EXCLUDED BY ASSUMPTION" in w for w in result["warnings"])


def test_shield_convention_is_required():
    with pytest.raises(ValueError, match="SHIELD_CONVENTION_REQUIRED"):
        apv_value(
            rows(),
            unlevered_cost_of_capital=0.10,
            terminal_growth=0.02,
            tax_rate=0.25,
            shield_discount_convention=None,
        )
    with pytest.raises(ValueError, match="SHIELD_CONVENTION_REQUIRED"):
        apv_value(
            rows(),
            unlevered_cost_of_capital=0.10,
            terminal_growth=0.02,
            tax_rate=0.25,
            shield_discount_convention="risk_free",
        )


def test_fixed_debt_shields_match_independent_decimal():
    schedule = [200.0, 180.0, 160.0, 140.0, 120.0]
    kd, tax, rho = 0.06, 0.25, 0.10
    result = apv_value(
        rows(),
        unlevered_cost_of_capital=rho,
        terminal_growth=0.02,
        tax_rate=tax,
        debt_schedule=schedule,
        cost_of_debt=kd,
        shield_discount_convention="fixed_debt_kd",
    )
    expected_shields = Decimal(0)
    for t, balance in enumerate(schedule, start=1):
        shield = Decimal("0.25") * Decimal(str(kd)) * Decimal(str(balance))
        expected_shields += shield / (Decimal(1) + Decimal(str(kd))) ** t
    assert abs(Decimal(str(result["pv_tax_shields"])) - expected_shields) / expected_shields < Decimal("1e-12")
    assert result["adjusted_firm_value"] == pytest.approx(
        result["unlevered_firm_value"] + result["pv_tax_shields"]
    )


def test_debt_repaid_policy_drops_terminal_shields():
    schedule = [200.0] * 5
    result = apv_value(
        rows(),
        unlevered_cost_of_capital=0.10,
        terminal_growth=0.02,
        tax_rate=0.25,
        debt_schedule=schedule,
        cost_of_debt=0.06,
        shield_discount_convention="fixed_debt_kd",
        terminal_shield_policy="debt_repaid",
    )
    assert result["pv_terminal_tax_shields"] == 0.0
    assert any("debt_repaid" in w for w in result["warnings"])

    result2 = apv_value(
        rows(),
        unlevered_cost_of_capital=0.10,
        terminal_growth=0.02,
        tax_rate=0.25,
        debt_schedule=schedule,
        cost_of_debt=0.06,
        shield_discount_convention="fixed_debt_kd",
        terminal_shield_policy="constant_debt_shield_perpetuity",
    )
    assert result2["pv_terminal_tax_shields"] > 0.0
    assert result2["adjusted_firm_value"] > result["adjusted_firm_value"]


def test_limited_taxable_income_defers_deductions():
    # EBIT below interest in year 1: shield limited, carryforward grows
    projections = [
        {"UFCF": 10.0, "EBIT": 5.0, "Year": 1},
        {"UFCF": 100.0, "EBIT": 200.0, "Year": 2},
        {"UFCF": 100.0, "EBIT": 200.0, "Year": 3},
        {"UFCF": 100.0, "EBIT": 200.0, "Year": 4},
        {"UFCF": 100.0, "EBIT": 200.0, "Year": 5},
    ]
    result = apv_value(
        projections,
        unlevered_cost_of_capital=0.10,
        terminal_growth=0.02,
        tax_rate=0.25,
        debt_schedule=[100.0] * 5,
        cost_of_debt=0.08,
        shield_discount_convention="fixed_debt_kd",
    )
    r1 = result["tax_shield_rows"][0]
    assert r1["interest"] == pytest.approx(8.0)
    assert r1["usable_interest"] == pytest.approx(5.0)  # limited to EBIT
    assert r1["tax_shield"] == pytest.approx(1.25)
    assert r1["carryforward_out"] > 0
    r2 = result["tax_shield_rows"][1]
    assert r2["usable_interest"] > r2["interest"] or r2["usable_interest"] == pytest.approx(8.0)
    assert any("limited taxable income" in w for w in result["warnings"])


def test_zero_tax_rate_means_no_shield_value():
    result = apv_value(
        rows(),
        unlevered_cost_of_capital=0.10,
        terminal_growth=0.02,
        tax_rate=0.0,
        debt_schedule=[200.0] * 5,
        cost_of_debt=0.06,
        shield_discount_convention="fixed_debt_kd",
    )
    assert result["pv_tax_shields"] == 0.0
    assert result["adjusted_firm_value"] == pytest.approx(result["unlevered_firm_value"])


def test_shield_conventions_order_as_expected():
    kwargs = dict(
        unlevered_cost_of_capital=0.10,
        terminal_growth=0.02,
        tax_rate=0.25,
        debt_schedule=[200.0] * 5,
        cost_of_debt=0.06,
    )
    kd_pv = apv_value(rows(), shield_discount_convention="fixed_debt_kd", **kwargs)["pv_tax_shields"]
    rho_pv = apv_value(rows(), shield_discount_convention="harris_pringle_rho_u", **kwargs)["pv_tax_shields"]
    me_pv = apv_value(rows(), shield_discount_convention="miles_ezzell", **kwargs)["pv_tax_shields"]
    # Discounting shields at kd (lower rate) values them highest; rho_u lowest;
    # Miles-Ezzell (year 1 at kd, rest at rho_u) sits between.
    assert kd_pv > me_pv > rho_pv > 0


def test_distress_scenarios_are_explicit_and_discounted():
    result = apv_value(
        rows(),
        unlevered_cost_of_capital=0.10,
        terminal_growth=0.02,
        tax_rate=0.25,
        shield_discount_convention="fixed_debt_kd",
        distress_scenarios=[
            {"probability": 0.10, "loss_amount": 500.0, "year": 3},
        ],
    )
    assert result["distress_treatment"] == "EXPECTED_SCENARIOS"
    expected = Decimal("0.10") * Decimal("500") / (Decimal("1.10") ** 3)
    assert abs(Decimal(str(result["pv_expected_distress_costs"])) - expected) / expected < Decimal("1e-12")
    assert result["adjusted_firm_value"] == pytest.approx(
        result["unlevered_firm_value"] + result["pv_tax_shields"] - result["pv_expected_distress_costs"]
    )
    assert not any("EXCLUDED BY ASSUMPTION" in w for w in result["warnings"])

    # loss_fraction scales off the unlevered firm value
    result2 = apv_value(
        rows(),
        unlevered_cost_of_capital=0.10,
        terminal_growth=0.02,
        tax_rate=0.25,
        shield_discount_convention="fixed_debt_kd",
        distress_scenarios=[
            {"probability": 0.20, "loss_fraction": 0.10, "year": 2},
        ],
    )
    assert result2["distress_scenarios_detail"][0]["loss_basis"] == "fraction_of_unlevered_firm_value"

    # ...and a scenario without a stated loss is refused
    with pytest.raises(ValueError, match="explicit loss_amount or loss_fraction"):
        apv_value(
            rows(),
            unlevered_cost_of_capital=0.10,
            terminal_growth=0.02,
            tax_rate=0.25,
            shield_discount_convention="fixed_debt_kd",
            distress_scenarios=[{"probability": 0.20, "year": 2}],
        )


def test_terminal_instability_rejected():
    with pytest.raises(ValueError, match="TERMINAL_GROWTH_NOT_FEASIBLE"):
        apv_value(
            rows(),
            unlevered_cost_of_capital=0.02,
            terminal_growth=0.02,
            tax_rate=0.25,
            shield_discount_convention="fixed_debt_kd",
        )


def test_apv_wacc_reconciliation_identity():
    """Reconciliation where the assumptions permit it.

    Exact theorem (perpetuity case): with constant UFCF, constant debt, MM
    fixed-debt shields at kd, perpetual terminal shields and no distress,
    V_apv = u/rho_u + T*D, and the self-consistent WACC
    rho_u * (1 - T*D/V_apv) discounts the identical flows back to exactly V_apv.

    Documented divergence (growing case): fixed nominal debt plus growing flows
    cannot be reconciled by ANY constant WACC - the implied leverage ratio falls
    over time, so exact equivalence would require a time-varying WACC. The
    residual gap is asserted to be real and bounded, not hidden.
    """
    from dcf_code import discount_fcff

    rho_u, kd, tax, debt = 0.10, 0.06, 0.25, 200.0
    projections = rows(ufcf=100.0, ebit=150.0)
    ufcf_rows = [
        {"Year": i + 1, "UFCF": p["UFCF"], "NOPAT": p["EBIT"] * (1 - tax)}
        for i, p in enumerate(projections)
    ]

    # ---- Exact identity: constant flows (terminal growth 0) ----
    apv0 = apv_value(
        projections,
        unlevered_cost_of_capital=rho_u,
        terminal_growth=0.0,
        tax_rate=tax,
        debt_schedule=[debt] * 5,
        cost_of_debt=kd,
        shield_discount_convention="fixed_debt_kd",
        terminal_shield_policy="constant_debt_shield_perpetuity",
    )
    v0 = apv0["adjusted_firm_value"]
    # Total shield value = T*D (perpetual shield discounted at kd)
    total_shields = apv0["pv_tax_shields"] + apv0["pv_terminal_tax_shields"]
    assert total_shields == pytest.approx(tax * debt, rel=1e-12)
    assert v0 == pytest.approx(100.0 / rho_u + tax * debt, rel=1e-12)
    wacc0 = rho_u * (1.0 - tax * debt / v0)
    wacc0_value = discount_fcff(ufcf_rows, wacc0, 0.0)["enterprise_value"]
    assert wacc0_value == pytest.approx(v0, rel=1e-12)

    # ---- Documented divergence: growing flows + constant nominal debt ----
    g = 0.02
    apv_g = apv_value(
        projections,
        unlevered_cost_of_capital=rho_u,
        terminal_growth=g,
        tax_rate=tax,
        debt_schedule=[debt] * 5,
        cost_of_debt=kd,
        shield_discount_convention="fixed_debt_kd",
        terminal_shield_policy="constant_debt_shield_perpetuity",
    )
    v_g = apv_g["adjusted_firm_value"]
    wacc_g = rho_u * (1.0 - tax * debt / v_g)
    wacc_g_value = discount_fcff(ufcf_rows, wacc_g, g)["enterprise_value"]
    gap = abs(v_g - wacc_g_value) / v_g
    # The gap is the financing-policy inconsistency, documented rather than hidden:
    # fixed nominal debt is not a constant debt/value policy, so a constant WACC
    # built from it leaves a real residual (bounded here to show it is not an error).
    assert 1e-6 < gap < 0.02


def test_apv_api_endpoint_returns_lineage():
    from app import app
    from dcf_loader import demo_document

    doc = demo_document()
    client = app.test_client()
    response = client.post(
        "/api/calculate/apv",
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
            "unlevered_cost_of_capital": 0.09,
            "debt_schedule": [500.0, 450.0, 400.0, 350.0, 300.0],
            "cost_of_debt": 0.05,
            "shield_discount_convention": "fixed_debt_kd",
            "terminal_shield_policy": "debt_repaid",
            "distress_scenarios": None,
        },
    )
    assert response.status_code == 200, response.json
    body = response.json
    assert body["method"] == "apv"
    assert body["valuation_basis"] == "enterprise"
    assert body["adjusted_firm_value"] == pytest.approx(
        body["unlevered_firm_value"]
        + body["pv_tax_shields"]
        + body["pv_terminal_tax_shields"]
        - body["pv_expected_distress_costs"]
    )
    assert body["distress_treatment"] == "DISTRESS_EXCLUDED_BY_ASSUMPTION"
    assert body["shield_discount_convention"] == "fixed_debt_kd"
    assert len(body["tax_shield_rows"]) == 5
