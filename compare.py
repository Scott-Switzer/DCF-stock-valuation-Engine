"""Football-field comparison: DCF, DDM and relative targets side by side.

Loads one DCF snapshot per ticker, then derives the DDM and relative
documents from that snapshot so all three methods share identical market
inputs. Methods that cannot be computed (no dividends, no peers) are
reported as unavailable with the underlying reason instead of failing
the whole page.
"""

from copy import deepcopy
from dataclasses import asdict, replace

from dcf_code import DCFAssumptions, DCFModel
from dcf_loader import ProviderError, ticker_symbol
from readiness import method_readiness, reliable_peers
from residual_income import residual_income_value
from issuer_classification import financial_block_reason
from suite_views import suite_assumptions, suite_evaluate


WACC_MODES = ("recalculated", "fixed")


def resolve_tax_rates(doc):
    """Baseline forecast tax rates via tax_policy, honoring a doc selection.

    A document carrying an explicit ``source.tax_policy.selected`` policy
    (SEC-first load or PPE merge with a user override / normalized
    scenario) uses its rates; otherwise the latest reported rate resolves
    the default. An unresolvable default raises ValueError naming the
    required explicit assumption -- never an invented rate -- so existing
    ``except ValueError`` lanes render it as an unavailable DCF.
    """
    from tax_policy import TaxPolicyError, resolve_forecast_tax

    policy = (doc.get("source") or {}).get("tax_policy") or {}
    selected = policy.get("selected") or {}
    rates = selected.get("rates")
    if isinstance(rates, list) and len(rates) == 5 and all(
        isinstance(v, (int, float)) and 0 <= v <= 1 for v in rates
    ):
        return [float(v) for v in rates], selected.get("basis", "unknown")
    try:
        resolved = resolve_forecast_tax([r["tax_rate"] for r in doc["historical"]])
    except TaxPolicyError as exc:
        raise ValueError(str(exc)) from None
    return resolved["rates"], resolved["basis"]


def recalculated_wacc(costs, shield):
    """Recompute WACC from frozen market inputs with the selected shield.

    Same arithmetic the loaders use for ``capital_costs.wacc``; with an
    unchanged shield it reproduces the loaded rate exactly, so the default
    path is numerically identical and scenarios stay coherent. Raises
    ValueError when the cost components are unavailable.
    """
    try:
        equity = float(costs["market_equity_value"])
        debt = float(costs["debt"])
        cost_equity = float(costs["cost_of_equity"])
        cost_debt = float(costs["cost_of_debt"])
        shield = float(shield)
    except (KeyError, TypeError, ValueError):
        raise ValueError(
            "Capital-cost components are unavailable; WACC cannot be recalculated."
        ) from None
    if equity + debt <= 0:
        raise ValueError("Capital weights are unavailable; WACC cannot be recalculated.")
    return (equity * cost_equity + debt * cost_debt * (1 - shield)) / (equity + debt)


def selected_shield(doc, assumptions):
    """Marginal debt-tax shield: explicit override beats forecast tax beats latest."""
    override = getattr(assumptions, "interest_tax_shield_rate", None)
    if isinstance(override, (int, float)):
        return float(override), "explicit_shield_override"
    if assumptions.tax_rates:
        return float(assumptions.tax_rates[0]), "coherent_with_forecast"
    latest = doc["historical"][-1].get("tax_rate")
    if isinstance(latest, (int, float)) and 0 <= latest <= 1:
        return float(latest), "latest_reported"
    return None, "unavailable"


def wacc_basis_note(doc, assumptions, costs, wacc_mode):
    """Label which discount-rate regime an assumption set uses."""
    shield, shield_basis = selected_shield(doc, assumptions)
    expected = None
    if isinstance(costs, dict) and shield is not None:
        try:
            expected = recalculated_wacc(costs, shield)
        except ValueError:
            expected = None
    override = assumptions.wacc_override
    if (
        wacc_mode == "recalculated"
        and expected is not None
        and isinstance(override, (int, float))
        and abs(override - expected) < 1e-9
    ):
        return (
            f"Recalculated WACC {override:.2%} from frozen market inputs with "
            f"the {shield:.2%} tax shield ({shield_basis}; {wacc_mode} mode)."
        )
    return (
        f"Fixed-WACC sensitivity: discount rate held at {override:.2%} while "
        f"cash-flow taxes use {shield:.2%} ({shield_basis}; {wacc_mode} mode)."
        if isinstance(override, (int, float)) and shield is not None
        else f"WACC basis unavailable ({wacc_mode} mode)."
    )


def baseline_dcf_assumptions(doc, wacc):
    rows = doc["historical"]

    def average(key):
        values = [r[key] / r["revenue"] for r in rows]
        return sum(values) / len(values)

    tax_rates, _ = resolve_tax_rates(doc)
    return DCFAssumptions(
        revenue_growth_rates=[0.05] * 5,
        terminal_growth_rate=0.02,
        wacc_override=wacc,
        terminal_mode="template",
        ebit_margins=[average("ebit")] * 5,
        da_margins=[average("d_and_a")] * 5,
        capex_margins=[average("capex")] * 5,
        nwc_margins=[average("nwc")] * 5,
        tax_rates=tax_rates,
        net_income_margins=[average("net_income")] * 5,
        book_value_margins=[average("book_value")] * 5,
    )


def coerce_dcf_assumptions(doc, raw, wacc, costs=None, wacc_mode="recalculated"):
    """Validate user-supplied DCF assumptions; fall back to baselines.

    ``wacc_mode`` selects the discount-rate regime: ``recalculated``
    recomputes the WACC override from frozen market inputs
    (``costs`` -- the loaded ``capital_costs``) with the selected tax
    shield, so FCFF and WACC never use inconsistent rates; ``fixed``
    deliberately holds the loaded WACC while cash-flow taxes vary. The
    regime is labeled by ``wacc_basis_note``, never switched silently.
    """
    from app import assumptions_from_json

    # An explicit per-request mode travels in the raw assumptions (saves,
    # exports, compare posts); otherwise the caller's mode applies.
    if isinstance(raw, dict) and raw.get("wacc_mode") in WACC_MODES:
        wacc_mode = raw["wacc_mode"]
    if wacc_mode not in WACC_MODES:
        raise ValueError(f"WACC mode must be one of {WACC_MODES}.")
    if not isinstance(raw, dict) or not raw:
        base = baseline_dcf_assumptions(doc, wacc)
        base = replace(base, wacc_mode=wacc_mode)
        if wacc_mode == "recalculated" and isinstance(costs, dict):
            shield, _ = selected_shield(doc, base)
            if shield is not None:
                try:
                    base = replace(base, wacc_override=recalculated_wacc(costs, shield))
                except ValueError:
                    pass
        return base, False
    merged = asdict(baseline_dcf_assumptions(doc, wacc))
    merged.update({k: v for k, v in raw.items() if v is not None})
    merged["wacc_mode"] = wacc_mode
    assumptions = assumptions_from_json(merged)
    if wacc_mode == "recalculated" and isinstance(costs, dict):
        # Explicit recalculated mode wins over a stale displayed WACC.
        # Legacy raw overrides without a mode retain their fixed-rate behavior.
        if raw.get("wacc_override") is None or raw.get("wacc_mode") == "recalculated":
            shield, _ = selected_shield(doc, assumptions)
            if shield is not None:
                try:
                    assumptions = replace(
                        assumptions,
                        wacc_override=recalculated_wacc(costs, shield),
                    )
                except ValueError:
                    pass
    return assumptions, True


def scenario_band(doc, base, delta):
    """Bear/base/bull variant: shift growth and EBIT margins together."""
    from dataclasses import replace

    return replace(
        base,
        revenue_growth_rates=[g + delta for g in base.revenue_growth_rates],
        ebit_margins=[m + delta for m in base.ebit_margins],
    )


def football_field(ticker, asof=None, dcf_assumptions=None, snapshot=None, http=None,
                   wacc_mode="recalculated"):
    """Compare lanes for one ticker.

    ``snapshot`` is an optional dcf-financials-v1 document, such as the
    workspace's loaded financials. It is validated and reused without a
    provider load; DDM and relative lanes derive from the same document.
    """
    from auto_loading import load_method
    from app import evaluate
    from dcf_loader import parse_document

    symbol = ticker_symbol(ticker)
    if snapshot is not None:
        # The comparison page serves financial issuers too (equity multiples,
        # residual income, bank excess returns); each lane enforces its own
        # applicability, so intake keeps structural checks but skips the
        # FCFF operating-company gate.
        parse_document(snapshot, minority_may_be_negative=True, allow_financial=True)
        if snapshot["company"]["ticker"] != symbol:
            raise ValueError("Workspace snapshot ticker does not match.")
    dcf_kwargs = {"http": http}
    if snapshot is not None:
        dcf_kwargs["snapshot"] = snapshot
    bundle = load_method("dcf", symbol, asof, **dcf_kwargs)
    doc = bundle["financials"]
    costs = bundle["load_summary"].get("capital_costs", {})
    wacc = costs.get("wacc") or 0.065
    dcf_assumptions, custom = coerce_dcf_assumptions(
        doc, dcf_assumptions, wacc, costs=costs, wacc_mode=wacc_mode
    )
    lanes = []
    band_results = {}
    result = None
    try:
        result = evaluate(deepcopy(doc), deepcopy(dcf_assumptions))
        for name, delta in [("Bear", -0.02), ("Base", 0.0), ("Bull", 0.02)]:
            try:
                band_results[name] = evaluate(
                    deepcopy(doc), scenario_band(doc, deepcopy(dcf_assumptions), delta)
                )["target_price_12m"]
            except ValueError:
                band_results[name] = None
        lanes.append(
            {
                "method": "dcf",
                "label": "DCF intrinsic (today)",
                "value": result["intrinsic_value"],
                "detail": f"WACC {result['wacc']:.1%}, g {result['terminal_growth']:.1%}",
                "warnings": result["warnings"][:2],
            }
        )
        lanes.append(
            {
                "method": "dcf",
                "label": "DCF 12-month target" + (" (your scenario)" if custom else ""),
                "value": result["target_price_12m"],
                "detail": "Scenario with year-one overrides",
                "warnings": [],
                "band": band_results,
            }
        )
    except ValueError as exc:
        lanes.append({"method": "dcf", "label": "DCF", "value": None,
                      "detail": str(exc), "warnings": []})
    try:
        ddm_bundle = load_method(
            "ddm", symbol, doc["valuation_date"], snapshot=doc, http=http
        )
        ddm_doc = ddm_bundle["financials"]
        ddm_a = suite_assumptions(
            "ddm",
            {
                "dividend_growth_rates": [0.05] * 5,
                "required_return": costs.get("cost_of_equity", 0.07),
                "terminal_growth_rate": 0.02,
            },
        )
        ddm_result = suite_evaluate("ddm", ddm_doc, ddm_a)
        lanes.append(
            {
                "method": "ddm",
                "label": "DDM intrinsic (today)",
                "value": ddm_result["intrinsic_value"],
                "detail": "Common dividends only",
                "warnings": [],
            }
        )
        lanes.append(
            {
                "method": "ddm",
                "label": "DDM 12-month (ex-div)",
                "value": ddm_result["target_price_12m"],
                "detail": "Excludes the first dividend",
                "warnings": [],
            }
        )
    except (ProviderError, ValueError) as exc:
        lanes.append(
            {
                "method": "ddm",
                "label": "DDM",
                "value": None,
                "detail": str(exc),
                "warnings": [],
            }
        )
    try:
        residual_readiness = method_readiness(doc)["residual"]
        if residual_readiness["state"] == "unavailable":
            raise ValueError(" ".join(residual_readiness["reasons"]))
        # Earnings projections do not require an FCFF enterprise valuation.
        # In particular, financial firms can use residual income while DCF is blocked.
        projections = DCFModel(
            parse_document(doc, minority_may_be_negative=True, allow_financial=True),
            deepcopy(dcf_assumptions),
        ).forecast_cash_flows()
        cost_of_equity = costs.get("cost_of_equity")
        if not isinstance(cost_of_equity, (int, float)):
            raise ValueError("Cost of equity is unavailable from the loaded capital-cost inputs.")
        dividend = (doc["source"].get("common_dividends") or {}).get("value")
        last_net_income = doc["historical"][-1]["net_income"]
        payout = 0.0
        if isinstance(dividend, (int, float)) and dividend > 0 and last_net_income > 0:
            payout = min(1.0, max(0.0, dividend / last_net_income))
        residual = residual_income_value(
            net_income=[row["Net Income"] for row in projections],
            opening_book=doc["historical"][-1]["book_value"],
            cost_of_equity=cost_of_equity,
            terminal_growth=dcf_assumptions.terminal_growth_rate,
            shares=doc["market"]["diluted_shares"],
            payout_ratio=payout,
        )
        lanes.append(
            {
                "method": "residual",
                "label": "Residual income (today)",
                "value": residual["intrinsic_value"],
                "detail": (
                    f"Cost of equity {cost_of_equity:.1%}, payout {payout:.0%}, "
                    "clean-surplus book"
                ),
                "warnings": residual["warnings"][:1],
            }
        )
    except (ValueError, KeyError, TypeError) as exc:
        lanes.append(
            {
                "method": "residual",
                "label": "Residual income",
                "value": None,
                "detail": str(exc),
                "warnings": [],
            }
        )
    # Bank / financial-institution excess-return lane: dedicated equity model,
    # explicitly gated on issuer type. Industrial FCFF/WACC machinery is never
    # applied to banks; non-financial issuers get the exclusion reason, not a zero.
    try:
        financial_reason = financial_block_reason(doc)
        if not financial_reason:
            raise ValueError(
                "Excluded: the bank excess-return lane applies to financial institutions; "
                "use DCF/FCFE for operating companies."
            )
        from bank_excess_return import bank_excess_return_value

        bank_ke = costs.get("cost_of_equity")
        if not isinstance(bank_ke, (int, float)):
            raise ValueError(
                "Cost of equity is unavailable from the loaded capital-cost inputs."
            )
        bank_projections = DCFModel(
            parse_document(deepcopy(doc), minority_may_be_negative=True, allow_financial=True),
            deepcopy(dcf_assumptions),
        ).forecast_cash_flows()
        dividend = (doc["source"].get("common_dividends") or {}).get("value")
        bank_ni = doc["historical"][-1]["net_income"]
        bank_payout = 0.0
        if isinstance(dividend, (int, float)) and dividend > 0 and bank_ni > 0:
            bank_payout = min(1.0, max(0.0, dividend / bank_ni))
        bank = bank_excess_return_value(
            [row["Net Income"] for row in bank_projections],
            opening_book=doc["historical"][-1]["book_value"],
            cost_of_equity=bank_ke,
            terminal_growth=dcf_assumptions.terminal_growth_rate,
            shares=doc["market"]["diluted_shares"],
            payout_ratio=bank_payout,
            equity_basis="TOTAL_BOOK",
        )
        lanes.append(
            {
                "method": "bank",
                "label": "Bank excess return (today)",
                "value": bank["intrinsic_value"],
                "detail": (
                    f"Cost of equity {bank_ke:.1%}, payout {bank_payout:.0%}, "
                    "equity excess returns over book capital (total-book basis)"
                ),
                "warnings": bank["warnings"][:1],
                "basis": "equity",
            }
        )
    except (ValueError, KeyError, TypeError) as exc:
        lanes.append(
            {
                "method": "bank",
                "label": "Bank excess return",
                "value": None,
                "detail": str(exc),
                "warnings": [],
                "basis": "equity",
            }
        )
    try:
        from fcfe_valuation import fcfe_value

        fcfe_ke = costs.get("cost_of_equity")
        if not isinstance(fcfe_ke, (int, float)):
            raise ValueError(
                "Cost of equity is unavailable from the loaded capital-cost inputs."
            )
        fcfe_projections = DCFModel(
            parse_document(deepcopy(doc), minority_may_be_negative=True),
            deepcopy(dcf_assumptions),
        ).forecast_cash_flows()
        # Financing policy is explicit: the compare baseline assumes zero net
        # borrowing and says so, rather than inferring one from history.
        fcfe = fcfe_value(
            fcfe_projections,
            cost_of_equity=fcfe_ke,
            terminal_growth=dcf_assumptions.terminal_growth_rate,
            shares=doc["market"]["diluted_shares"],
            net_borrowing=None,
            market_price=doc["market"]["price"],
        )
        lanes.append(
            {
                "method": "fcfe",
                "label": "FCFE equity (today)",
                "value": fcfe["intrinsic_value"],
                "detail": (
                    f"Cost of equity {fcfe_ke:.1%}, "
                    f"{fcfe['net_borrowing_policy'].replace('_', ' ').lower()}"
                ),
                "warnings": fcfe["warnings"][:1],
                "basis": "equity",
            }
        )
    except (ValueError, KeyError, TypeError) as exc:
        lanes.append(
            {
                "method": "fcfe",
                "label": "FCFE",
                "value": None,
                "detail": str(exc),
                "warnings": [],
                "basis": "equity",
            }
        )
    try:
        from apv_valuation import apv_value

        wacc_loaded = costs.get("wacc")
        kd_loaded = costs.get("cost_of_debt")
        total_debt = doc["bridge"]["short_term_debt"] + doc["bridge"]["long_term_debt"]
        if not isinstance(wacc_loaded, (int, float)):
            raise ValueError(
                "WACC is unavailable from the loaded capital-cost inputs; APV needs a "
                "documented unlevered cost of capital."
            )
        tax_rate = dcf_assumptions.tax_rates[-1] if dcf_assumptions.tax_rates else doc["historical"][-1]["tax_rate"]
        market_equity = doc["market"]["price"] * doc["market"]["diluted_shares"]
        # Implied unlevered cost of capital under the fixed-debt MM identity
        # WACC = rho_u * (1 - T*D/V); inverted here with the market-value structure.
        value_weight = market_equity + total_debt
        shield_drag = tax_rate * total_debt / value_weight if value_weight > 0 else 0.0
        rho_u = wacc_loaded / (1.0 - shield_drag) if shield_drag < 1 else None
        if rho_u is None:
            raise ValueError("The capital structure implies no positive unlevered cost of capital.")
        apv_projections = DCFModel(
            parse_document(deepcopy(doc), minority_may_be_negative=True),
            deepcopy(dcf_assumptions),
        ).forecast_cash_flows()
        apv = apv_value(
            apv_projections,
            unlevered_cost_of_capital=rho_u,
            terminal_growth=dcf_assumptions.terminal_growth_rate,
            tax_rate=tax_rate,
            debt_schedule=[total_debt] * 5 if total_debt > 0 else None,
            cost_of_debt=kd_loaded if total_debt > 0 else None,
            shield_discount_convention="fixed_debt_kd" if total_debt > 0 else "fixed_debt_kd",
            terminal_shield_policy="debt_repaid",
            distress_scenarios=None,
        )
        # APV values the operating firm; the same claims bridge as the DCF lane
        # converts to per-share so the lanes share a comparable price basis.
        claims = (
            doc["bridge"]["short_term_debt"] + doc["bridge"]["long_term_debt"]
            + doc["bridge"]["preferred_equity"] + doc["bridge"]["minority_interest"]
            - doc["bridge"]["cash"] - doc["bridge"]["other_nonoperating_assets"]
        )
        apv_equity = apv["adjusted_firm_value"] - claims
        apv_per_share = apv_equity / doc["market"]["diluted_shares"]
        lanes.append(
            {
                "method": "apv",
                "label": "APV per share (today)",
                "value": apv_per_share,
                "detail": (
                    f"Unlevered rho {rho_u:.1%}, MM fixed-debt shields; "
                    "distress excluded by assumption"
                ),
                "warnings": apv["warnings"][-1:],
                "basis": "enterprise_then_same_bridge",
            }
        )
    except (ValueError, KeyError, TypeError) as exc:
        lanes.append(
            {
                "method": "apv",
                "label": "APV",
                "value": None,
                "detail": str(exc),
                "warnings": [],
                "basis": "enterprise",
            }
        )
    rel_doc = None
    try:
        rel_bundle = load_method(
            "relative",
            symbol,
            doc["valuation_date"],
            snapshot=doc,
            forecast_assumptions=deepcopy(dcf_assumptions),
            http=http,
        )
        rel_doc = rel_bundle["financials"]
        # Financial firms and a negative noncontrolling interest block EV-based multiples only.
        ev_blocked = rel_doc["bridge"]["minority_interest"] < 0 or bool(financial_block_reason(rel_doc))
        candidates = ["pe"] if ev_blocked else ["ev_revenue", "ev_ebitda", "pe"]
        # Unreviewed candidate peers never feed an automatic relative value.
        reviewed = reliable_peers(rel_doc["comparables"])
        included = [
            k
            for k in candidates
            if rel_doc["target"]["forward"][
                {"ev_revenue": "revenue", "ev_ebitda": "ebitda", "pe": "net_income"}[k]
            ]
            > 0
            and any(
                p["multiples"][k] is not None and p["multiples"][k] > 0 for p in reviewed
            )
        ]
        if not included:
            raise ValueError(
                "No reviewed peer multiples for this ticker. Loaded peers are unverified candidates "
                "unless confirmed on the relative page."
            )
        rel_result = suite_evaluate(
            "relative",
            dict(rel_doc, comparables=reviewed),
            suite_assumptions("relative", {"included_methods": included}),
        )
        lanes.append(
            {
                "method": "relative",
                "label": f"Relative 12-month ({len(included)} methods)",
                "value": rel_result["target_price_12m"],
                "detail": "Equal-weighted peer means",
                "warnings": [],
            }
        )
    except (ProviderError, ValueError, KeyError) as exc:
        lanes.append(
            {
                "method": "relative",
                "label": "Relative",
                "value": None,
                "detail": (str(exc) if isinstance(exc, (ProviderError, ValueError))
                             else "Peer snapshot was incomplete; reload the ticker."),
                "warnings": [],
            }
        )
    packet = _packet(
        doc, lanes, bundle, dcf_assumptions, custom, snapshot is not None, relative_doc=rel_doc
    )
    packet["drivers"] = driver_impacts(doc, dcf_assumptions)
    packet["method_notes"] = method_notes(doc, lanes)
    try:
        from reverse_dcf import solve

        packet["reverse"] = {
            "revenue_growth": solve(
                doc, deepcopy(dcf_assumptions), doc["market"]["price"],
                "revenue_growth",
            ),
            "ebit_margin": solve(
                doc, deepcopy(dcf_assumptions), doc["market"]["price"],
                "ebit_margin",
            ),
        }
    except ValueError as exc:
        packet["reverse"] = {"status": "unsolvable", "detail": str(exc)}
    return packet


def driver_impacts(doc, base):
    """One-at-a-time +1pt moves, ranked by per-share impact."""
    from dataclasses import replace
    from app import evaluate

    candidates = [
        ("Revenue growth (+1pt all years)",
         replace(base, revenue_growth_rates=[g + 0.01 for g in base.revenue_growth_rates])),
        ("EBIT margin (+1pt all years)",
         replace(base, ebit_margins=[m + 0.01 for m in base.ebit_margins])),
        ("WACC (+1pt)",
         replace(base, wacc_override=(base.wacc_override or 0.065) + 0.01)),
        ("Terminal growth (+1pt)",
         replace(base, terminal_growth_rate=base.terminal_growth_rate + 0.01)),
        ("Tax rate (+1pt all years)",
         replace(base, tax_rates=[t + 0.01 for t in base.tax_rates])),
    ]
    try:
        anchor = evaluate(deepcopy(doc), deepcopy(base))["intrinsic_value"]
    except ValueError:
        return []
    impacts = []
    for label, variant in candidates:
        try:
            moved = evaluate(deepcopy(doc), variant)["intrinsic_value"]
            impacts.append({"label": label, "delta": moved - anchor})
        except ValueError:
            continue
    impacts.sort(key=lambda r: abs(r["delta"]), reverse=True)
    return impacts[:3]


def method_notes(doc, lanes):
    """Explain gaps between computed lanes and flag unsuitable methods."""
    notes = []
    by_label = {lane["label"]: lane["value"] for lane in lanes}
    dcf = by_label.get("DCF intrinsic (today)")
    ddm = by_label.get("DDM intrinsic (today)")
    if isinstance(dcf, (int, float)) and isinstance(ddm, (int, float)) and dcf:
        gap = (ddm - dcf) / abs(dcf)
        if abs(gap) > 0.25:
            notes.append(
                f"DDM sits {gap:+.0%} from DCF: dividends capture only part of "
                "the cash the firm generates. Trust DCF when retention funds "
                "growth; trust DDM when payouts are the sustainable distribution."
            )
    text = " ".join(
        str(doc["company"].get(k, "")) for k in ("sector", "industry", "security_type")
    ).lower()
    financial = any(
        t in text for t in ("bank", "insurance", "financial service", "reit")
    ) or doc["company"].get("is_financial") is True
    if financial:
        notes.append(
            "This looks like a financial or real-estate issuer: enterprise-value "
            "methods mislead here. Use equity multiples (P/E, P/B) on the "
            "relative page instead of DCF."
        )
    dividend = doc["source"].get("common_dividends", {})
    if (dividend.get("value") or 0) <= 0 and any(
        lane["method"] == "ddm" and lane["value"] is None for lane in lanes
    ):
        notes.append(
            "No verified common dividend in this snapshot, so DDM is parked. "
            "Use DCF or relative valuation for non-payers."
        )
    return notes


def _packet(doc, lanes, bundle, assumptions, custom, reused, relative_doc=None):
    """Response packet. ``assumptions`` are the effective values the lanes used."""
    values = [lane["value"] for lane in lanes
              if isinstance(lane["value"], (int, float))]
    peak = max(values + [doc["market"]["price"], 0.01])
    for lane in lanes:
        lane["share"] = lane["value"] / peak if isinstance(lane["value"], (int, float)) else 0
        if isinstance(lane["value"], (int, float)):
            lane["upside"] = lane["value"] / doc["market"]["price"] - 1
        else:
            lane["upside"] = None
    return {
        "custom": custom,
        "assumptions_source": "workspace" if custom else "baseline",
        "snapshot_reused": reused,
        "ticker": doc["company"]["ticker"],
        "company_name": doc["company"]["name"],
        "valuation_date": doc["valuation_date"],
        "market_price": doc["market"]["price"],
        "price_as_of": doc["market"]["price_as_of"],
        "source": doc["source"]["name"],
        "is_demo": doc["source"]["kind"] == "synthetic"
        or doc["source"].get("origin_kind") == "synthetic",
        "lanes": lanes,
        "readiness": method_readiness(doc, relative_doc=relative_doc),
        "load_summary": bundle["load_summary"],
        "assumptions": asdict(assumptions),
    }
