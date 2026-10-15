"""Historical-versus-forecast tax policy: preservation, explicit assumptions, coherence."""

import json
from pathlib import Path

import pytest

from tax_policy import (
    TaxPolicyError,
    build_tax_reconciliation,
    reported_history,
    resolve_forecast_tax,
    shield_rate,
)


def test_reported_history_preserves_signed_rates():
    assert reported_history([0.2203, -0.1534, 0.3583]) == [0.2203, -0.1534, 0.3583]
    with pytest.raises(TaxPolicyError):
        reported_history([0.2, float("nan")])
    with pytest.raises(TaxPolicyError):
        reported_history([])


def test_resolve_prefers_override_then_scenario_then_latest():
    history = [0.22, -0.1534, 0.3583]
    user = resolve_forecast_tax(history, user_override=[0.25] * 5)
    assert user["rates"] == [0.25] * 5
    assert user["basis"] == "user_override"
    scenario = resolve_forecast_tax(
        history,
        scenario={
            "rates": [0.231] * 5,
            "evidence": {"filing": "f", "period_end": "2024-12-31"},
        },
    )
    assert scenario["rates"] == [0.231] * 5
    assert scenario["basis"] == "normalized_scenario"
    latest = resolve_forecast_tax([0.22, 0.24, 0.238])
    assert latest["rates"] == [0.238] * 5
    assert latest["basis"] == "latest_reported"


def test_resolve_refuses_silent_substitution():
    with pytest.raises(TaxPolicyError, match="explicit"):
        resolve_forecast_tax([0.22, -0.1534])
    with pytest.raises(TaxPolicyError, match="five rates"):
        resolve_forecast_tax([0.22, -0.1534], user_override=[0.25] * 4)
    with pytest.raises(TaxPolicyError, match="five rates"):
        resolve_forecast_tax([0.22, -0.1534], user_override=[1.5] * 5)
    with pytest.raises(TaxPolicyError, match="filing and period"):
        resolve_forecast_tax(
            [0.22, -0.1534], scenario={"rates": [0.2] * 5, "evidence": {}}
        )


def test_shield_defaults_coherent_with_forecast():
    policy = {"rates": [0.231] * 5, "basis": "normalized_scenario"}
    assert shield_rate(policy) == {"rate": 0.231, "basis": "coherent_with_forecast:normalized_scenario"}
    assert shield_rate(policy, override=0.21)["basis"] == "explicit_shield_override"
    with pytest.raises(TaxPolicyError):
        shield_rate(policy, override=1.5)
    with pytest.raises(TaxPolicyError):
        shield_rate({"rates": []})


def test_reconciliation_checks_bridge_and_splits_discrete():
    recon = build_tax_reconciliation(
        0.21,
        [
            {"label": "recurring credit", "effect_pp": -5.0, "recurring": True},
            {"label": "audit settlement", "effect_pp": -51.4, "recurring": False},
        ],
        0.21 - 0.05 - 0.514,
        "filing",
        "2024-12-31",
    )
    assert recon["recurring_only_rate"] == pytest.approx(0.16)
    assert recon["discrete_pp"] == pytest.approx(-51.4)
    with pytest.raises(TaxPolicyError, match="not the reported"):
        build_tax_reconciliation(
            0.21,
            [{"label": "x", "effect_pp": -5.0, "recurring": True}],
            0.0,
            "filing",
            "2024-12-31",
        )
    with pytest.raises(TaxPolicyError, match="Empty"):
        build_tax_reconciliation(0.21, [], 0.21, "filing", "2024-12-31")


def test_filed_abbv_aep_reconciliations_pin_normalized_rates():
    doc = json.loads(Path("find/outputs/forecast-tax/abbv-aep-evidence.json").read_text())
    abbv = doc["companies"]["ABBV"]["reconciliation"]
    assert abbv["reported_rate"] == pytest.approx(-570.0 / 3716.0)
    assert abbv["recurring_only_rate"] == pytest.approx(0.231, abs=0.001)
    assert abbv["discrete_pp"] == pytest.approx(-38.4, abs=0.05)
    aep = doc["companies"]["AEP"]["reconciliation"]
    assert aep["reported_rate"] == pytest.approx(-39.2 / 2935.2)
    assert aep["recurring_only_rate"] == pytest.approx(0.078, abs=0.001)
    # Filing-supported scenarios are adopted explicitly, never by default.
    assert doc["companies"]["ABBV"]["normalized_scenario"]["rate"] == 0.231
    assert doc["companies"]["AEP"]["normalized_scenario"]["rate"] == 0.078
    # FY2025 corroboration: AEP reported 3.37% bridges to recurring-only
    # 13.4% via the single discrete remeasurement (-10.01pp).
    aep25 = doc["companies"]["AEP"]["reconciliation_2025"]
    assert aep25["reported_rate"] == pytest.approx(129.0 / 3825.0)
    assert aep25["recurring_only_rate"] == pytest.approx(0.134, abs=0.001)
    assert aep25["discrete_pp"] == pytest.approx(-10.01, abs=0.05)
    # ABBV FY2025 discrete dominates both ways: adopted-flags recurring
    # 42.3% vs 21.0% with the whole PR pair discrete -- no stable point.
    sens = doc["companies"]["ABBV"]["fy2025_recurring_sensitivity"]
    assert sens["adopted_flags"] == pytest.approx(0.423, abs=0.002)
    assert sens["pr_pair_discrete"] == pytest.approx(0.210, abs=0.002)


def test_gate_names_tax_assumption_instead_of_invalidating_history():
    import sys

    sys.path.insert(0, "tests")
    from test_sec_first import full_packet

    from sec_first import eligibility_gate

    packet = full_packet()
    end = packet["historical"][-1]["period_end"]
    packet["historical"][-1]["fields"]["tax_rate"]["value"] = -0.153
    gate = eligibility_gate(packet, "TEST", packet["cutoff_date"])
    assert not gate["eligible"]
    assert any(r.startswith(f"tax_forecast_assumption_required_{end}") for r in gate["reasons"])
    assert not any("tax_rate_out_of_bounds" in r for r in gate["reasons"])
    # The signed history itself is preserved in the packet.
    assert packet["historical"][-1]["fields"]["tax_rate"]["value"] == -0.153


def test_gate_ignores_negative_middle_year_with_valid_latest():
    import sys

    sys.path.insert(0, "tests")
    from test_sec_first import full_packet

    from sec_first import eligibility_gate
    from tax_policy import resolve_forecast_tax

    # ABBV shape: 2023 +22.0%, 2024 -15.3%, 2025 +35.8%.
    packet = full_packet()
    taxes = [0.220, -0.153, 0.358]
    for row, tax in zip(packet["historical"], taxes):
        row["fields"]["tax_rate"]["value"] = tax
    gate = eligibility_gate(packet, "TEST", packet["cutoff_date"])
    assert not any("tax_forecast_assumption_required" in r for r in gate["reasons"])
    assert gate["eligible"]
    # The middle-year negative is preserved and the default forecasts from latest.
    assert packet["historical"][1]["fields"]["tax_rate"]["value"] == -0.153
    assert resolve_forecast_tax(taxes)["rates"] == [0.358] * 5


def test_gate_missing_latest_tax_reports_missing_not_assumption():
    import sys

    sys.path.insert(0, "tests")
    from test_sec_first import full_packet

    from sec_first import eligibility_gate

    packet = full_packet()
    packet["historical"][-1]["fields"].pop("tax_rate")
    gate = eligibility_gate(packet, "TEST", packet["cutoff_date"])
    assert not gate["eligible"]
    assert any(r.startswith("missing_tax_rate_") for r in gate["reasons"])
    assert not any("tax_forecast_assumption_required" in r for r in gate["reasons"])


def test_resolve_rejects_invalid_explicit_policies():
    import sys

    sys.path.insert(0, "tests")
    from test_sec_first import full_packet

    from sec_first import eligibility_gate
    from tax_policy import TaxPolicyError, resolve_forecast_tax

    history = [0.22, -0.153, 0.358]
    # Wrong length, out-of-bounds entries, and evidence-free scenarios refuse.
    for bad in ([0.25] * 4, [0.25] * 6, [1.5] * 5, [-0.1] * 5):
        with pytest.raises(TaxPolicyError):
            resolve_forecast_tax(history, user_override=bad)
    with pytest.raises(TaxPolicyError):
        resolve_forecast_tax(history, scenario={"rates": [0.231] * 5})
    # The gate still blocks the unsupported default, not the explicit policy.
    packet = full_packet()
    packet["historical"][-1]["fields"]["tax_rate"]["value"] = 2.0
    gate = eligibility_gate(packet, "TEST", packet["cutoff_date"])
    assert not gate["eligible"]
    assert resolve_forecast_tax(
        [0.22, 0.24, 2.0], user_override=[0.25] * 5
    )["basis"] == "user_override"


def test_model_preserves_history_but_requires_explicit_forecast():
    from dcf_code import DCFAssumptions, DCFModel, FinancialData

    def data_with(history):
        return FinancialData(
            years=["2023", "2024", "2025"],
            revenue=[100.0, 110.0, 121.0],
            ebit=[20.0, 22.0, 24.0],
            ebitda=[25.0, 27.0, 29.0],
            net_income=[10.0, 11.0, 12.0],
            effective_tax_rate=history,
            interest_expense=[2.0, 2.0, 2.0],
            current_assets=[50.0, 55.0, 60.0],
            current_liabilities=[30.0, 32.0, 35.0],
            cash_and_equivalents=[10.0, 10.0, 10.0],
            short_term_debt=[5.0, 5.0, 5.0],
            long_term_debt=[20.0, 20.0, 20.0],
            total_debt=[25.0, 25.0, 25.0],
            total_assets=[100.0, 110.0, 120.0],
            total_liabilities=[60.0, 65.0, 70.0],
            property_plant_equipment_net=[30.0, 30.0, 30.0],
            preferred_equity=[0.0, 0.0, 0.0],
            d_and_a=[5.0, 5.0, 5.0],
            capex=[6.0, 6.0, 6.0],
            preferred_dividends=[0.0, 0.0, 0.0],
            shares_outstanding=10.0,
            beta=1.0,
            stock_price=50.0,
            market_cap=500.0,
            risk_free_rate=0.04,
            market_return_rate=0.09,
        )

    base = DCFAssumptions(revenue_growth_rates=[0.05] * 5, terminal_growth_rate=0.02)
    # In-bounds history keeps the old default path exactly (parity).
    model = DCFModel(data_with([0.22, 0.24, 0.25]), base)
    assert model.forecast_cash_flows()[0]["Taxes"] == pytest.approx(0.25 * model.forecast_cash_flows()[0]["EBIT"])
    # A latest reported rate outside 0-1 refuses the baseline run loudly.
    bad = DCFModel(data_with([0.22, 0.24, -0.15]), base)
    with pytest.raises(ValueError, match="explicit"):
        bad.forecast_cash_flows()
    with pytest.raises(ValueError, match="explicit"):
        bad.calculate_wacc()
    # An explicit assumption resolves both FCFF and the shield coherently.
    explicit = DCFAssumptions(
        revenue_growth_rates=[0.05] * 5, terminal_growth_rate=0.02, tax_rates=[0.23] * 5
    )
    good = DCFModel(data_with([0.22, 0.24, -0.15]), explicit)
    flows = good.forecast_cash_flows()
    assert flows[0]["Taxes"] == pytest.approx(0.23 * flows[0]["EBIT"])
    assert good.calculate_wacc() == pytest.approx(
        DCFModel(data_with([0.22, 0.24, 0.23]), base).calculate_wacc()
    )
