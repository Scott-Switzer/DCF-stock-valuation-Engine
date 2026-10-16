"""Bottom-up beta, CAPM cost of equity, and mutually consistent WACC build for DCF.

Connects Damodaran's ``industry_betas`` and ``country_risk_premiums`` benchmark
releases (served through Zion's private ``benchmark_context`` contract or the
local release store) to ``dcf-zero-subscription``.

Key financial & mathematical rules enforced here:

1. **Beta taxonomy (never conflated):**
   - ``unlevered_firm_not_cash_corrected``: ``unlevered_beta`` from ``betas.xls``
     (firm-wide asset beta including cash holdings).
   - ``unlevered_operating_cash_corrected``: ``unlevered_beta_ex_cash`` from
     ``betas.xls`` or ``unlevered_beta / (1 - cash_to_firm_value)``.
   - ``relevered_equity``: bottom-up equity beta relevered at target or issuer
     market-value D/E.
   - ``observed_regression``: historical return regression beta (e.g., 5-year
     weekly SPY regression from ``yahoo_provider.py``).

2. **No double cash correction:**
   - If the selected benchmark measure is already ``unlevered_beta_ex_cash``,
     requesting ``apply_cash_correction=True`` raises ``ValueError``
     (``CASH_CORRECTION_DOUBLE_COUNT``).
   - If ``apply_cash_correction=True`` with ``unlevered_beta``, an explicit
     ``cash_to_firm_value`` in ``[0, 1)`` is required.

3. **Hamada vs. generalized nonzero debt beta:**
   - Default ``debt_beta = 0.0`` (Hamada 1972):
       ``beta_L = beta_U * (1 + (1 - marginal_tax_rate) * (D / E))``
     Explicitly documented as ``zero_debt_beta_hamada``.
   - Nonzero ``debt_beta > 0`` (generalized Modigliani-Miller / Miles-Ezzell):
       ``beta_L = beta_U + (beta_U - beta_D) * (1 - marginal_tax_rate) * (D / E)``
     Explicitly documented as ``nonzero_debt_beta_generalized``.

4. **Market-value leverage vs. book leverage:**
   - Relevering requires market-value debt-to-equity (``debt / (price * shares)``)
     or an explicit ``target_de_ratio``. Passing ``leverage_mode="book"`` is
     rejected (``BOOK_LEVERAGE_FORBIDDEN``).

5. **CAPM & Country Risk Premium (no double counting):**
   - ``cost_of_equity = risk_free_rate + beta_equity * applicable_erp``
   - Damodaran's ``equity_risk_premium`` and ``equity_risk_premium_cds`` in
     ``country_risk_premiums`` are **Total Country ERPs** (they already include
     the mature-market ERP plus the country risk spread).
   - If a Total Country ERP benchmark is selected AND an incremental
     ``country_risk_premium`` benchmark or override is also supplied, this
     module raises ``ValueError`` (``ERP_DOUBLE_COUNTING``).
   - Incremental ``country_risk_premium`` (weighted by ``country_lambda``,
     default 1.0) may only be added to a mature-market base ERP (e.g.,
     ``implied_erp_fcfe`` / ``implied_erp_ddm`` or an explicit
     ``mature_market_erp``).

6. **WACC propagation is opt-in and mutually consistent:**
   - Computing bottom-up beta and CAPM ``cost_of_equity`` NEVER silently
     overwrites ``wacc_override`` or company-reported fundamentals.
   - Only when ``propagate_to_wacc=True`` (and ``assumptions.wacc_override`` is
     not already set) does this module compute a mutually consistent WACC:
       ``WACC = (E/V) * k_e + (D/V) * k_d * (1 - marginal_tax_rate) + (P/V) * k_p``
     using the exact same capital structure weights ``(E, D, P)`` and
     ``marginal_tax_rate`` used in relevering.
"""

from __future__ import annotations

from copy import deepcopy
from dcf_code import number

SCHEMA_VERSION = "dcf-bottom-up-capm-v1"

BETA_MEASURES = {
    "unlevered_beta_ex_cash": "unlevered_operating_cash_corrected",
    "unlevered_beta": "unlevered_firm_not_cash_corrected",
}
TOTAL_ERP_MEASURES = frozenset({
    "equity_risk_premium",
    "equity_risk_premium_cds",
})
MATURE_ERP_MEASURES = frozenset({
    "implied_erp_fcfe",
    "implied_erp_ddm",
})
INCREMENTAL_CRP_MEASURES = frozenset({
    "country_risk_premium",
    "country_risk_premium_cds",
})


def _finite(val, label, lo=None, hi=None):
    return number(val, label, lo, hi)


def unlever_beta(beta_levered, de_ratio, tax_rate, *, debt_beta=0.0):
    """Unlever equity beta to asset beta under zero (Hamada) or nonzero debt beta."""
    bl = _finite(beta_levered, "Levered beta", 0.000001, 20.0)
    de = _finite(de_ratio, "Debt-to-equity ratio", 0.0, 100.0)
    t = _finite(tax_rate, "Marginal tax rate", 0.0, 0.999999)
    bd = _finite(debt_beta, "Debt beta", 0.0, 10.0)
    shield = (1.0 - t) * de
    return (bl + bd * shield) / (1.0 + shield)


def relever_beta(beta_unlevered, de_ratio, tax_rate, *, debt_beta=0.0):
    """Relever asset/operating beta to equity beta:
    - Hamada (debt_beta == 0): beta_L = beta_U * (1 + (1 - t) * D/E)
    - Generalized (debt_beta > 0): beta_L = beta_U + (beta_U - beta_D) * (1 - t) * D/E
    """
    bu = _finite(beta_unlevered, "Unlevered beta", 0.000001, 20.0)
    de = _finite(de_ratio, "Target debt-to-equity ratio", 0.0, 100.0)
    t = _finite(tax_rate, "Marginal tax rate", 0.0, 0.999999)
    bd = _finite(debt_beta, "Debt beta", 0.0, 10.0)
    if bd > bu:
        raise ValueError("INVALID_DEBT_BETA: Debt beta cannot exceed unlevered asset beta.")
    shield = (1.0 - t) * de
    if bd == 0.0:
        return bu * (1.0 + shield)
    return bu + (bu - bd) * shield


def apply_cash_adjustment(beta_unlevered, cash_to_firm_value, *, measure_name):
    """Adjust firm unlevered beta for cash: beta_U / (1 - Cash/FirmValue).
    Refuses if ``measure_name`` is already cash-corrected.
    """
    bu = _finite(beta_unlevered, "Unlevered beta", 0.000001, 20.0)
    if measure_name == "unlevered_beta_ex_cash":
        raise ValueError(
            "CASH_CORRECTION_DOUBLE_COUNT: benchmark measure 'unlevered_beta_ex_cash' "
            "is already corrected for cash; do not apply a second cash adjustment."
        )
    cash_ratio = _finite(cash_to_firm_value, "Cash-to-firm-value ratio", 0.0, 0.999999)
    return bu / (1.0 - cash_ratio)


def resolve_erp(
    *,
    erp_benchmark=None,
    crp_benchmark=None,
    mature_market_erp=None,
    country_risk_premium=None,
    country_lambda=1.0,
):
    """Resolve the applicable Equity Risk Premium without double-counting country risk."""
    lam = _finite(country_lambda, "Country risk exposure lambda", 0.0, 5.0)
    sources = {}

    if erp_benchmark is not None:
        measure = erp_benchmark.get("measure")
        val = _finite(float(erp_benchmark["value_decimal"]), "Benchmark ERP", 0.0001, 0.5)
        sources["erp_benchmark"] = deepcopy(erp_benchmark)
        if measure in TOTAL_ERP_MEASURES:
            if crp_benchmark is not None or (country_risk_premium is not None and country_risk_premium > 0):
                raise ValueError(
                    f"ERP_DOUBLE_COUNTING: benchmark measure '{measure}' for "
                    f"'{erp_benchmark.get('subject')}' is already a Total Equity Risk Premium "
                    "incorporating country risk; do not add a separate country_risk_premium."
                )
            if mature_market_erp is not None:
                raise ValueError(
                    "ERP_CONFLICT: cannot supply both a Total Country ERP benchmark and mature_market_erp."
                )
            return {
                "mode": "total_country_erp_benchmark",
                "base_erp": val,
                "country_risk_premium": 0.0,
                "country_lambda": lam,
                "applicable_erp": val,
                "erp_includes_country_risk": True,
                "subject": erp_benchmark.get("subject"),
                "measure": measure,
                "sources": sources,
            }
        if measure in MATURE_ERP_MEASURES:
            base_erp = val
        else:
            raise ValueError(f"Unsupported ERP benchmark measure: {measure}")
    elif mature_market_erp is not None:
        base_erp = _finite(mature_market_erp, "Mature-market ERP", 0.0001, 0.5)
    else:
        raise ValueError("Provide an ERP benchmark selection or an explicit mature_market_erp.")

    # Mature-market ERP base: optional incremental country risk premium allowed
    if crp_benchmark is not None and country_risk_premium is not None:
        raise ValueError("CRP_CONFLICT: cannot specify both crp_benchmark and explicit country_risk_premium.")
    crp_val = 0.0
    if crp_benchmark is not None:
        c_measure = crp_benchmark.get("measure")
        if c_measure not in INCREMENTAL_CRP_MEASURES:
            raise ValueError(
                f"ERP_DOUBLE_COUNTING: measure '{c_measure}' is not an incremental country risk spread."
            )
        crp_val = _finite(float(crp_benchmark["value_decimal"]), "Benchmark CRP", 0.0, 0.5)
        sources["crp_benchmark"] = deepcopy(crp_benchmark)
    elif country_risk_premium is not None:
        crp_val = _finite(country_risk_premium, "Country risk premium", 0.0, 0.5)

    applicable = base_erp + lam * crp_val
    return {
        "mode": "mature_erp_plus_country_spread" if crp_val > 0 else "mature_market_erp_only",
        "base_erp": base_erp,
        "country_risk_premium": crp_val,
        "country_lambda": lam,
        "applicable_erp": applicable,
        "erp_includes_country_risk": False,
        "subject": (crp_benchmark or erp_benchmark or {}).get("subject"),
        "measure": (erp_benchmark or {}).get("measure", "explicit_mature_erp"),
        "sources": sources,
    }


def resolve_capital_structure(doc, spec):
    """Determine market-value leverage D/E, marginal tax rate, and financing weights.

    Explicitly rejects book-equity leverage when market equity is required.
    """
    leverage_mode = spec.get("leverage_mode", "issuer_market")
    if leverage_mode == "book" or spec.get("use_book_leverage") is True:
        raise ValueError(
            "BOOK_LEVERAGE_FORBIDDEN: Hamada relevering requires market-value debt-to-equity "
            "or an explicit target D/E ratio, never book D/E."
        )
    market = doc.get("market", {})
    bridge = doc.get("bridge", {})
    historical = doc.get("historical", [])

    price = _finite(market.get("price"), "Market price", 0.000001)
    shares = _finite(market.get("diluted_shares"), "Diluted shares", 0.000001)
    market_equity = _finite(
        spec.get("market_equity_override", price * shares),
        "Market equity value",
        0.000001,
    )
    st_debt = _finite(bridge.get("short_term_debt", 0.0), "Short-term debt", 0.0)
    lt_debt = _finite(bridge.get("long_term_debt", 0.0), "Long-term debt", 0.0)
    total_debt = _finite(
        spec.get("debt_override", st_debt + lt_debt),
        "Total debt",
        0.0,
    )
    preferred = _finite(
        spec.get("preferred_override", bridge.get("preferred_equity", 0.0)),
        "Preferred equity",
        0.0,
    )
    issuer_market_de = total_debt / market_equity

    if leverage_mode == "issuer_market":
        target_de = issuer_market_de
        basis = "issuer_market_value_debt_to_equity"
    elif leverage_mode == "target_de":
        if "target_de_ratio" not in spec or spec["target_de_ratio"] is None:
            raise ValueError("leverage_mode='target_de' requires an explicit target_de_ratio.")
        target_de = _finite(spec["target_de_ratio"], "Target D/E ratio", 0.0, 100.0)
        basis = "explicit_target_debt_to_equity"
    else:
        raise ValueError("leverage_mode must be 'issuer_market' or 'target_de'.")

    # Marginal tax rate resolution with provenance
    if spec.get("marginal_tax_rate") is not None:
        tax_rate = _finite(spec["marginal_tax_rate"], "Marginal tax rate", 0.0, 0.999999)
        tax_source = "explicit_marginal_tax_rate"
    elif spec.get("tax_benchmark") is not None:
        tb = spec["tax_benchmark"]
        tax_rate = _finite(float(tb["value_decimal"]), "Benchmark tax rate", 0.0, 0.999999)
        tax_source = f"benchmark:{tb.get('dataset_id')}:{tb.get('subject')}:{tb.get('measure')}"
    elif historical and historical[-1].get("tax_rate") is not None:
        tax_rate = _finite(historical[-1]["tax_rate"], "Latest reported effective tax rate", 0.0, 0.999999)
        tax_source = f"issuer_historical_effective_tax_rate:{historical[-1].get('period_end')}"
    else:
        raise ValueError("A marginal_tax_rate or historical tax_rate is required for beta relevering.")

    # Compute consistent financing weights E/V, D/V, P/V
    if leverage_mode == "target_de":
        # With target D/E and no preferred override, D/E = target_de => E/(D+E) = 1/(1+target_de)
        pref_weight = 0.0
        eq_weight = 1.0 / (1.0 + target_de)
        debt_weight = target_de / (1.0 + target_de)
        total_capital = market_equity * (1.0 + target_de)
    else:
        total_capital = market_equity + total_debt + preferred
        eq_weight = market_equity / total_capital
        debt_weight = total_debt / total_capital
        pref_weight = preferred / total_capital

    return {
        "leverage_mode": leverage_mode,
        "leverage_basis": basis,
        "market_equity": market_equity,
        "total_debt": total_debt,
        "preferred_equity": preferred,
        "total_capital": total_capital,
        "issuer_market_de_ratio": issuer_market_de,
        "target_de_ratio": target_de,
        "equity_weight": eq_weight,
        "debt_weight": debt_weight,
        "preferred_weight": pref_weight,
        "marginal_tax_rate": tax_rate,
        "marginal_tax_rate_source": tax_source,
    }


def compute_bottom_up_capm(
    doc,
    spec,
    *,
    beta_benchmark,
    erp_benchmark=None,
    crp_benchmark=None,
    cash_benchmark=None,
    cost_of_debt_benchmark=None,
):
    """Compute bottom-up levered beta, CAPM cost of equity, comparison diagnostics,
    and (when requested) a mutually consistent WACC.
    """
    if not isinstance(doc, dict) or not isinstance(spec, dict):
        raise ValueError("Financial document and bottom_up_beta specification are required.")
    if not isinstance(beta_benchmark, dict) or "value_decimal" not in beta_benchmark:
        raise ValueError("A resolved industry beta benchmark observation is required.")

    measure = beta_benchmark.get("measure")
    if measure not in BETA_MEASURES:
        raise ValueError(
            f"Unsupported beta benchmark measure '{measure}'. Choose 'unlevered_beta_ex_cash' "
            "or 'unlevered_beta' from industry_betas."
        )
    raw_unlevered = _finite(float(beta_benchmark["value_decimal"]), "Industry unlevered beta", 0.000001, 20.0)
    initial_kind = BETA_MEASURES[measure]

    apply_cash = bool(spec.get("apply_cash_correction", False))
    cash_ratio_used = None
    if apply_cash:
        if cash_benchmark is not None:
            cash_ratio_used = _finite(float(cash_benchmark["value_decimal"]), "Benchmark cash/firm value", 0.0, 0.999999)
        elif spec.get("industry_cash_to_firm_value") is not None:
            cash_ratio_used = _finite(spec["industry_cash_to_firm_value"], "Industry cash/firm value", 0.0, 0.999999)
        else:
            raise ValueError(
                "apply_cash_correction=True requires cash_benchmark ('cash_to_firm_value') "
                "or industry_cash_to_firm_value."
            )
        operating_beta = apply_cash_adjustment(raw_unlevered, cash_ratio_used, measure_name=measure)
        operating_kind = "unlevered_operating_cash_corrected"
    else:
        operating_beta = raw_unlevered
        operating_kind = initial_kind

    cap_struct = resolve_capital_structure(doc, spec)
    debt_beta = _finite(spec.get("debt_beta", 0.0), "Debt beta", 0.0, 10.0)
    relevered_equity_beta = relever_beta(
        operating_beta,
        cap_struct["target_de_ratio"],
        cap_struct["marginal_tax_rate"],
        debt_beta=debt_beta,
    )
    roundtrip_unlevered = unlever_beta(
        relevered_equity_beta,
        cap_struct["target_de_ratio"],
        cap_struct["marginal_tax_rate"],
        debt_beta=debt_beta,
    )

    # Risk-free rate resolution
    existing_costs = (doc.get("source") or {}).get("capital_costs") or {}
    if spec.get("risk_free_rate") is not None:
        rf = _finite(spec["risk_free_rate"], "Risk-free rate", -0.05, 0.5)
        rf_source = spec.get("risk_free_rate_source", "explicit_user_assumption")
    elif existing_costs.get("risk_free_rate") is not None:
        rf = _finite(existing_costs["risk_free_rate"], "Snapshot risk-free rate", -0.05, 0.5)
        rf_source = f"snapshot_capital_costs:{existing_costs.get('risk_free_rate_as_of', 'loaded')}"
    else:
        raise ValueError("Provide risk_free_rate in bottom_up_beta spec or source.capital_costs.")

    erp_block = resolve_erp(
        erp_benchmark=erp_benchmark,
        crp_benchmark=crp_benchmark,
        mature_market_erp=spec.get("mature_market_erp"),
        country_risk_premium=spec.get("country_risk_premium"),
        country_lambda=spec.get("country_lambda", 1.0),
    )

    ke = rf + relevered_equity_beta * erp_block["applicable_erp"]
    _finite(ke, "CAPM cost of equity", 0.001, 1.0)

    # Observed regression beta & existing cost of equity comparison
    observed_beta = existing_costs.get("beta")
    existing_ke = existing_costs.get("cost_of_equity")
    existing_wacc = existing_costs.get("wacc")
    comparison = {
        "observed_regression_beta": observed_beta,
        "observed_beta_basis": existing_costs.get("beta_basis"),
        "bottom_up_relevered_beta": relevered_equity_beta,
        "beta_delta_vs_observed": (
            relevered_equity_beta - observed_beta
            if isinstance(observed_beta, (int, float))
            else None
        ),
        "existing_cost_of_equity": existing_ke,
        "bottom_up_cost_of_equity": ke,
        "cost_of_equity_delta_vs_existing": (
            ke - existing_ke if isinstance(existing_ke, (int, float)) else None
        ),
        "existing_wacc": existing_wacc,
    }

    # Optional mutually-consistent WACC build
    propagate_to_wacc = bool(spec.get("propagate_to_wacc", False))
    wacc_block = None
    if propagate_to_wacc or spec.get("preview_wacc", True):
        kd = None
        kd_source = None
        if spec.get("pre_tax_cost_of_debt") is not None:
            kd = _finite(spec["pre_tax_cost_of_debt"], "Pre-tax cost of debt", 0.0, 0.5)
            kd_source = "explicit_pre_tax_cost_of_debt"
        elif cost_of_debt_benchmark is not None:
            kd = _finite(float(cost_of_debt_benchmark["value_decimal"]), "Benchmark cost of debt", 0.0, 0.5)
            kd_source = f"benchmark:{cost_of_debt_benchmark.get('dataset_id')}:{cost_of_debt_benchmark.get('subject')}:cost_of_debt"
        elif spec.get("credit_spread") is not None:
            spread = _finite(spec["credit_spread"], "Credit spread", 0.0, 0.5)
            kd = rf + spread
            kd_source = f"risk_free_plus_credit_spread({spread:.4f})"
        elif existing_costs.get("cost_of_debt") is not None:
            kd = _finite(existing_costs["cost_of_debt"], "Snapshot cost of debt", 0.0, 0.5)
            kd_source = f"snapshot_capital_costs:{existing_costs.get('debt_cost_basis', 'loaded')}"
        elif cap_struct["total_debt"] == 0 and cap_struct["debt_weight"] == 0:
            kd = 0.0
            kd_source = "zero_debt"

        kp = 0.0
        kp_source = "zero_preferred"
        if cap_struct["preferred_weight"] > 0:
            if spec.get("preferred_cost") is not None:
                kp = _finite(spec["preferred_cost"], "Preferred cost", 0.0, 0.5)
                kp_source = "explicit_preferred_cost"
            elif existing_costs.get("preferred_cost") is not None:
                kp = _finite(existing_costs["preferred_cost"], "Snapshot preferred cost", 0.0, 0.5)
                kp_source = "snapshot_preferred_cost"
            elif propagate_to_wacc:
                raise ValueError(
                    "Nonzero preferred equity requires an explicit preferred_cost when propagating to WACC."
                )

        if kd is None:
            if propagate_to_wacc:
                raise ValueError(
                    "Propagating CAPM cost of equity to WACC requires pre_tax_cost_of_debt, "
                    "cost_of_debt_benchmark, credit_spread, or snapshot cost_of_debt."
                )
        else:
            after_tax_kd = kd * (1.0 - cap_struct["marginal_tax_rate"])
            computed_wacc = (
                cap_struct["equity_weight"] * ke
                + cap_struct["debt_weight"] * after_tax_kd
                + cap_struct["preferred_weight"] * kp
            )
            _finite(computed_wacc, "Bottom-up WACC", 0.001, 0.5)
            wacc_block = {
                "propagated_to_dcf_wacc": propagate_to_wacc,
                "wacc": computed_wacc,
                "pre_tax_cost_of_debt": kd,
                "after_tax_cost_of_debt": after_tax_kd,
                "cost_of_debt_source": kd_source,
                "preferred_cost": kp,
                "preferred_cost_source": kp_source,
                "tax_rate_used": cap_struct["marginal_tax_rate"],
                "tax_rate_source": cap_struct["marginal_tax_rate_source"],
                "weights": {
                    "equity_weight": cap_struct["equity_weight"],
                    "debt_weight": cap_struct["debt_weight"],
                    "preferred_weight": cap_struct["preferred_weight"],
                },
                "wacc_delta_vs_existing": (
                    computed_wacc - existing_wacc
                    if isinstance(existing_wacc, (int, float))
                    else None
                ),
            }

    sources = {"beta_benchmark": deepcopy(beta_benchmark)}
    sources.update(erp_block["sources"])
    if cash_benchmark is not None:
        sources["cash_benchmark"] = deepcopy(cash_benchmark)
    if cost_of_debt_benchmark is not None:
        sources["cost_of_debt_benchmark"] = deepcopy(cost_of_debt_benchmark)
    if spec.get("tax_benchmark") is not None:
        sources["tax_benchmark"] = deepcopy(spec["tax_benchmark"])

    return {
        "schema_version": SCHEMA_VERSION,
        "industry_subject": beta_benchmark.get("subject"),
        "beta_decomposition": {
            "raw_benchmark_measure": measure,
            "raw_benchmark_beta": raw_unlevered,
            "raw_beta_kind": initial_kind,
            "cash_correction_applied_here": apply_cash,
            "industry_cash_to_firm_value": cash_ratio_used,
            "operating_unlevered_beta": operating_beta,
            "operating_beta_kind": operating_kind,
            "debt_beta": debt_beta,
            "debt_beta_assumption": (
                "zero_debt_beta_hamada" if debt_beta == 0.0 else "nonzero_debt_beta_generalized"
            ),
            "relevered_equity_beta": relevered_equity_beta,
            "relevered_beta_kind": "relevered_equity",
            "roundtrip_unlevered_beta": roundtrip_unlevered,
            "roundtrip_identity_diff": abs(roundtrip_unlevered - operating_beta),
        },
        "capital_structure": cap_struct,
        "capm": {
            "risk_free_rate": rf,
            "risk_free_rate_source": rf_source,
            "beta_equity": relevered_equity_beta,
            "erp_mode": erp_block["mode"],
            "base_equity_risk_premium": erp_block["base_erp"],
            "country_risk_premium": erp_block["country_risk_premium"],
            "country_lambda": erp_block["country_lambda"],
            "applicable_equity_risk_premium": erp_block["applicable_erp"],
            "erp_includes_country_risk": erp_block["erp_includes_country_risk"],
            "cost_of_equity": ke,
        },
        "wacc_build": wacc_block,
        "comparison": comparison,
        "benchmark_sources": sources,
    }
