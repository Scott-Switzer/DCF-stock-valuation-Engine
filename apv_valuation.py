"""Adjusted Present Value (APV): unlevered value + financing tax shields - distress costs.

    APV = V_unlevered + PV(financing tax shields) - PV(expected financial distress costs)

All financing assumptions are explicit; nothing is inferred:

* **Unlevered valuation.** Forecast unlevered free cash flow (the DCFModel UFCF
  rows: NOPAT + D&A - CapEx - dNWC) is discounted at the unlevered cost of
  capital ``rho_u``, with a Gordon terminal value requiring ``rho_u > g`` and a
  positive terminal flow.

* **Tax shields.** Interest is computed from an explicit debt schedule and a
  pre-tax cost of debt. The usable shield is limited by taxable income: a
  deduction that cannot be used this year (limited taxable income or a loss
  year) carries forward with the interest limitation; nothing is assumed to be
  usable just because it exists. The discount-rate convention for shields is
  REQUIRED and explicit - the risk of tax shields is not identical under every
  financing policy:
  - ``fixed_debt_kd`` (Modigliani-Miller fixed debt): shields discounted at the
    pre-tax cost of debt.
  - ``harris_pringle_rho_u`` (debt rebalanced to a target ratio): shields
    discounted at the unlevered cost of capital.
  - ``miles_ezzell`` (rebalanced debt, discrete): the year-one shield at the
    cost of debt, later shields at the unlevered cost of capital.

* **Distress costs.** Supported only through explicit expected scenarios
  (probability x loss at a stated year) discounted at the unlevered cost of
  capital. If none are supplied the result is labeled
  ``DISTRESS_EXCLUDED_BY_ASSUMPTION`` - never a silently complete APV.
  Probabilities and loss sizes are never manufactured.

* **No double counting.** The tax shield is the tax benefit of interest
  deductions; subtracting debt principal in the equity bridge is a claim
  settlement, not a second shield. Cash and other claims follow the existing
  enterprise-to-equity bridge. With a zero debt schedule APV equals the
  unlevered firm value by construction.

The output is an ENTERPRISE-basis value (APV values the operating firm); the
equity bridge is applied separately and reported distinctly.
"""

import math

SCHEMA_VERSION = "apv-v1"

SHIELD_CONVENTIONS = ("fixed_debt_kd", "harris_pringle_rho_u", "miles_ezzell")
TERMINAL_SHIELD_POLICIES = ("debt_repaid", "constant_debt_shield_perpetuity")
DISTRESS_EXCLUDED = "DISTRESS_EXCLUDED_BY_ASSUMPTION"


def _finite(value, name, lo=None, hi=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number.")
    value = float(value)
    if lo is not None and value < lo:
        raise ValueError(f"{name} must be at least {lo}.")
    if hi is not None and value > hi:
        raise ValueError(f"{name} must be at most {hi}.")
    return value


def apv_value(
    projections,
    *,
    unlevered_cost_of_capital,
    terminal_growth,
    tax_rate,
    debt_schedule=None,
    cost_of_debt=None,
    shield_discount_convention,
    terminal_shield_policy="debt_repaid",
    distress_scenarios=None,
):
    """Compute the APV components over five explicit forecast years.

    ``projections``: five DCFModel forecast rows (UFCF and EBIT per year).
    ``debt_schedule``: None (no debt) or five beginning-of-year debt balances.
    ``distress_scenarios``: None (explicitly excluded) or a list of
    ``{"probability", "loss_fraction"|"loss_amount", "year"}`` dicts.
    """
    if not isinstance(projections, (list, tuple)) or len(projections) != 5:
        raise ValueError("APV needs exactly five forecast years.")
    if shield_discount_convention not in SHIELD_CONVENTIONS:
        raise ValueError(
            "SHIELD_CONVENTION_REQUIRED: choose one of " + ", ".join(SHIELD_CONVENTIONS)
            + ". The risk of tax shields depends on the financing policy and cannot be assumed."
        )
    if terminal_shield_policy not in TERMINAL_SHIELD_POLICIES:
        raise ValueError(
            "terminal_shield_policy must be one of " + ", ".join(TERMINAL_SHIELD_POLICIES)
        )
    rho_u = _finite(unlevered_cost_of_capital, "Unlevered cost of capital", 0.001, 1.0)
    g = _finite(terminal_growth, "Terminal growth", -0.5, 0.5)
    tax = _finite(tax_rate, "Marginal tax rate", 0.0, 0.999999)
    if rho_u <= g:
        raise ValueError(
            "TERMINAL_GROWTH_NOT_FEASIBLE: unlevered cost of capital must exceed terminal growth."
        )

    # ---- Unlevered firm value ----
    ufcf_rows = []
    pv_unlevered = 0.0
    for i, proj in enumerate(projections):
        if not isinstance(proj, dict):
            raise ValueError("Each forecast row must be an object.")
        ufcf = _finite(proj.get("UFCF"), "Unlevered free cash flow")
        ebit = _finite(proj.get("EBIT"), "EBIT")
        df = 1.0 / (1.0 + rho_u) ** (i + 1)
        pv_unlevered += ufcf * df
        ufcf_rows.append({"year": i + 1, "ufcf": ufcf, "ebit": ebit,
                          "discount_factor": df, "pv_ufcf": ufcf * df})
    terminal_ufcf = ufcf_rows[-1]["ufcf"] * (1.0 + g)
    if terminal_ufcf <= 0:
        raise ValueError(
            "TERMINAL_UFCF_NOT_POSITIVE: terminal unlevered cash flow is not positive; "
            "a Gordon terminal value is not meaningful."
        )
    terminal_unlevered = terminal_ufcf / (rho_u - g)
    pv_terminal_unlevered = terminal_unlevered * ufcf_rows[-1]["discount_factor"]
    unlevered_value = pv_unlevered + pv_terminal_unlevered

    # ---- Financing tax shields ----
    if debt_schedule is None:
        balances = [0.0] * 5
    elif isinstance(debt_schedule, (list, tuple)) and len(debt_schedule) == 5:
        balances = [_finite(v, "Debt balance", 0.0, 1e15) for v in debt_schedule]
    else:
        raise ValueError("debt_schedule must be None or five beginning-of-year debt balances.")
    has_debt = any(b > 0 for b in balances)
    if has_debt and cost_of_debt is None:
        raise ValueError("A pre-tax cost of debt is required when a debt schedule is supplied.")
    kd = _finite(cost_of_debt, "Pre-tax cost of debt", 0.0, 0.5) if cost_of_debt is not None else 0.0
    if has_debt and kd <= 0:
        raise ValueError("Pre-tax cost of debt must be positive when debt is scheduled.")

    shield_rows = []
    pv_shields = 0.0
    carryforward = 0.0  # unused deductions carried to the next year
    for i, row in enumerate(ufcf_rows):
        interest = kd * balances[i]
        available = row["ebit"] + carryforward
        usable_interest = min(interest, max(0.0, available))
        shield = tax * usable_interest if tax > 0 else 0.0
        # Unused interest limitation and remaining taxable income both carry forward.
        carryforward = max(0.0, available - usable_interest) + (interest - usable_interest)
        if shield_discount_convention == "fixed_debt_kd":
            rate = kd
        elif shield_discount_convention == "harris_pringle_rho_u":
            rate = rho_u
        else:  # miles_ezzell: year one at kd, later at rho_u
            rate = kd if i == 0 else rho_u
        df = 1.0 / (1.0 + rate) ** (i + 1) if interest > 0 else 0.0
        pv_shields += shield * df
        shield_rows.append({
            "year": i + 1,
            "debt_balance": balances[i],
            "interest": interest,
            "usable_interest": usable_interest,
            "tax_shield": shield,
            "carryforward_out": carryforward,
            "shield_discount_rate": rate,
            "pv_tax_shield": shield * df,
        })

    terminal_shield_pv = 0.0
    if terminal_shield_policy == "constant_debt_shield_perpetuity":
        last = shield_rows[-1]
        if last["tax_shield"] > 0:
            term_rate = kd if shield_discount_convention == "fixed_debt_kd" else rho_u
            if term_rate <= g:
                raise ValueError(
                    "TERMINAL_SHIELD_NOT_FEASIBLE: shield discount rate must exceed terminal growth."
                )
            # Gordon perpetuity on the final-year shield at the convention rate.
            df_last = 1.0 / (1.0 + term_rate) ** 5
            terminal_shield_pv = last["tax_shield"] * (1.0 + g) / (term_rate - g) * df_last
    # else debt_repaid: terminal shields are zero by explicit policy

    # ---- Expected financial distress costs ----
    distress_pv = 0.0
    distress_detail = []
    if distress_scenarios is None:
        distress_treatment = DISTRESS_EXCLUDED
    elif isinstance(distress_scenarios, (list, tuple)) and distress_scenarios:
        distress_treatment = "EXPECTED_SCENARIOS"
        for sc in distress_scenarios:
            if not isinstance(sc, dict):
                raise ValueError("Each distress scenario must be an object.")
            p = _finite(sc.get("probability"), "Distress probability", 0.0, 1.0)
            year = sc.get("year")
            if not isinstance(year, int) or not 1 <= year <= 5:
                raise ValueError("Distress scenario year must be an integer in 1..5.")
            if "loss_amount" in sc and sc["loss_amount"] is not None:
                loss = _finite(sc["loss_amount"], "Distress loss", 0.0, 1e15)
                basis = "explicit_loss_amount"
            elif "loss_fraction" in sc and sc["loss_fraction"] is not None:
                loss = _finite(sc["loss_fraction"], "Distress loss fraction", 0.0, 1.0) * unlevered_value
                basis = "fraction_of_unlevered_firm_value"
            else:
                raise ValueError(
                    "Each distress scenario needs an explicit loss_amount or loss_fraction."
                )
            df = 1.0 / (1.0 + rho_u) ** year
            expected = p * loss
            distress_pv += expected * df
            distress_detail.append({
                "probability": p, "year": year, "loss": loss, "loss_basis": basis,
                "expected_cost": expected, "discount_rate": rho_u, "pv_expected_cost": expected * df,
            })
    else:
        raise ValueError("distress_scenarios must be None or a non-empty list of scenarios.")

    adjusted_firm_value = unlevered_value + pv_shields + terminal_shield_pv - distress_pv

    warnings = [
        "APV separates operating value from financing effects; the unlevered value is "
        "discounted at the unlevered cost of capital, not WACC.",
        "Tax-shield discounting follows the selected financing-policy convention; "
        "changing the convention changes the value.",
    ]
    if distress_treatment == DISTRESS_EXCLUDED:
        warnings.append(
            "No distress scenarios were provided: expected financial distress costs are "
            "EXCLUDED BY ASSUMPTION, so this is not a complete distress-adjusted APV."
        )
    if has_debt and any(r["usable_interest"] < r["interest"] for r in shield_rows):
        warnings.append(
            "At least one year has limited taxable income: part of the interest deduction "
            "is deferred through the carryforward rather than used immediately."
        )
    if terminal_shield_policy == "debt_repaid" and has_debt:
        warnings.append(
            "Terminal policy 'debt_repaid' assumes scheduled debt is repaid before the "
            "terminal period, so no terminal tax shields are valued."
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "method": "apv",
        "valuation_basis": "enterprise",
        "unlevered_firm_value": unlevered_value,
        "pv_explicit_unlevered": pv_unlevered,
        "pv_terminal_unlevered": pv_terminal_unlevered,
        "pv_tax_shields": pv_shields,
        "pv_terminal_tax_shields": terminal_shield_pv,
        "pv_expected_distress_costs": distress_pv,
        "distress_treatment": distress_treatment,
        "distress_scenarios_detail": distress_detail,
        "adjusted_firm_value": adjusted_firm_value,
        "unlevered_cost_of_capital": rho_u,
        "terminal_growth": g,
        "marginal_tax_rate": tax,
        "shield_discount_convention": shield_discount_convention,
        "terminal_shield_policy": terminal_shield_policy,
        "debt_schedule": balances,
        "pre_tax_cost_of_debt": kd,
        "unlevered_rows": ufcf_rows,
        "tax_shield_rows": shield_rows,
        "warnings": warnings,
    }
