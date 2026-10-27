"""SEC-first statement path: served statements and served market inputs.

A company qualifies only when its published PPE packet already contains every
statement input the DCF contract requires, with common-shareholder net income
coming exclusively from a bridged direct SEC tag. Anything else is an error:
there is no Yahoo annual-statement fallback.

Market inputs come from the Zion serving layer too. Price and beta derive
from served CRSP price history (see served_market); the risk-free rate has
no served source yet, so a load that needs capital costs fails closed with
SERVED_RISK_FREE_RATE_NOT_CONFIGURED instead of pulling a Treasury yield
from Yahoo.
"""

from copy import deepcopy
from datetime import datetime, timezone
import time

from dcf_loader import (
    HISTORY_FIELDS,
    BRIDGE_FIELDS,
    ProviderError,
    blank_document,
    parse_document,
    ticker_symbol,
)
from ppe_packets import validate_packet

STATEMENT_FIELDS = tuple(k for k in HISTORY_FIELDS if k != "net_income")


def eligibility_gate(packet, ticker, asof):
    """Decide whether a company may bypass Yahoo annual statements.

    Pure function: no network, no repair. Returns a dict with ``eligible``,
    machine-readable ``reasons`` (empty when eligible) and ``coverage``.
    """
    ticker = ticker_symbol(ticker)
    reasons = []
    coverage = {}
    if not isinstance(packet, dict):
        return {"eligible": False, "reasons": ["no_ppe_packet"], "coverage": coverage}
    try:
        validate_packet(packet, ticker, asof)
    except ProviderError as exc:
        return {
            "eligible": False,
            "reasons": [f"packet_contract_invalid: {exc}"],
            "coverage": coverage,
        }
    if asof != datetime.now(timezone.utc).date().isoformat():
        reasons.append(
            "historical_point_in_time_unavailable: market inputs require the current UTC date"
        )
    history = packet.get("historical", [])
    taxes = []
    if len(history) != 3:
        reasons.append(f"annual_periods_incomplete: {len(history)} of 3 packet periods")
    common_by_end = {x["period_end"]: x for x in packet.get("common_income", [])}
    for row in history:
        end = row.get("period_end")
        fields = row.get("fields", {})
        for key in ("revenue", "ebit"):
            prov = (fields.get(key) or {}).get("provenance") or {}
            if not prov.get("accession") or not (fields.get(key) or {}).get("available_at"):
                reasons.append(f"incomplete_provenance_{key}_{end}: missing accession or filing date")
        if common_by_end.get(end) is None:
            reasons.append(f"missing_common_income_{end}: no bridged direct common tag")
        coverage[end] = {}
        for key in STATEMENT_FIELDS:
            present = fields.get(key) is not None
            coverage[end][key] = present
            if not present:
                reasons.append(f"missing_{key}_{end}")
        # Reported history is preserved as filed, including negative rates
        # from benefits or settlements (see tax_policy). Only the latest
        # year governs default-forecast resolvability: a negative middle
        # year (e.g. ABBV 2024) never blocks forecasting from a valid
        # latest year (e.g. ABBV 2025). An unusable latest default blocks
        # only the unsupported default run, never an explicitly supported
        # forecast policy, and never the statement itself.
        taxes.append(((fields.get("tax_rate") or {}).get("value"), end))
    # Default-forecast resolvability depends on the latest year alone.
    # Middle-year negatives stay signed in history and never block;
    # a missing latest rate is already reported as missing_tax_rate_*.
    present = [(tax, end) for tax, end in taxes if tax is not None]
    if len(present) == len(history) and present:
        latest_tax, latest_end = present[-1]
        if not 0 <= latest_tax <= 1:
            reasons.append(
                f"tax_forecast_assumption_required_{latest_end}: reported "
                f"{latest_tax:.2%} is preserved; supply an explicit user "
                "override or filing-supported normalized scenario (tax_policy)"
            )
    shares = packet.get("diluted_shares")
    if not isinstance(shares, dict) or not (shares.get("value") or 0) > 0:
        reasons.append("missing_diluted_shares")
    bridge = packet.get("bridge", {})
    for key in BRIDGE_FIELDS:
        if key == "other_nonoperating_assets":
            continue  # assumed zero with a labeled warning, as in the Yahoo path
        if bridge.get(key) is None:
            reasons.append(f"missing_bridge_{key}")
    return {"eligible": not reasons, "reasons": reasons, "coverage": coverage}


READINESS_STATES = (
    "PACKET_BUILT",
    "INPUTS_COMPLETE",
    "POLICY_VALID",
    "CAPITAL_COSTS_AVAILABLE",
    "DCF_EVALUABLE",
)


def valuation_readiness(packet, ticker, asof, preferred_cost=None):
    """Distinguish packet construction from data readiness for valuation.

    A gate-eligible (READY) packet is not a working valuation: the DCF also
    needs published accounting-policy evidence and priced capital claims,
    plus live market inputs (price, beta, Treasury) and an actual DCF run.
    Pure function: no network, runs no DCF. Returns ordered ``states`` (each
    met/blocked with a reason) plus ``valuation_ready``, which means only
    that every data-determined input state is met -- a data-completeness
    prediction, not a verified valuation. Brief rendering and live staging
    runs are operational checks recorded in the coverage report, not here.
    """
    states = {}
    try:
        validate_packet(packet, ticker, asof)
    except ProviderError as exc:
        states["PACKET_BUILT"] = {"met": False, "reason": f"packet_contract_invalid: {exc}"}
        for name in READINESS_STATES[1:]:
            states[name] = {"met": False, "reason": "blocked by PACKET_BUILT"}
        return {"states": states, "valuation_ready": False}
    states["PACKET_BUILT"] = {"met": True, "reason": "packet contract valid"}
    gate = eligibility_gate(packet, ticker, asof)
    if gate["eligible"]:
        states["INPUTS_COMPLETE"] = {"met": True, "reason": "eligibility gate passed"}
    else:
        states["INPUTS_COMPLETE"] = {
            "met": False,
            "reason": "eligibility gate failed: " + "; ".join(gate["reasons"]),
        }
        for name in READINESS_STATES[2:]:
            states[name] = {"met": False, "reason": "blocked by INPUTS_COMPLETE"}
        return {"states": states, "valuation_ready": False}
    published = packet.get("adjustment_facts") if isinstance(packet, dict) else None
    conflicts = (published or {}).get("conflicts") if isinstance(published, dict) else None
    if isinstance(published, dict) and isinstance(published.get("facts"), dict) and not conflicts:
        states["POLICY_VALID"] = {
            "met": True,
            "reason": "published adjustment evidence present without conflicts "
            "(evidence presence only; DCF run and market inputs still required)",
        }
    elif conflicts:
        states["POLICY_VALID"] = {
            "met": False,
            "reason": f"published adjustment evidence reports conflicts: {conflicts}",
        }
    else:
        states["POLICY_VALID"] = {
            "met": False,
            "reason": "no published adjustment evidence; load-time fallback only",
        }
    bridge = packet.get("bridge", {})
    preferred = (bridge.get("preferred_equity") or {}).get("value") or 0
    if preferred == 0:
        states["CAPITAL_COSTS_AVAILABLE"] = {
            "met": True,
            "reason": "zero preferred equity needs no preferred cost",
        }
    elif preferred_cost is not None and preferred_cost > 0:
        states["CAPITAL_COSTS_AVAILABLE"] = {
            "met": True,
            "reason": "explicit preferred cost supplied (conventional preferred only; "
            "mandatory-convertible instruments need conversion modeling)",
        }
    else:
        states["CAPITAL_COSTS_AVAILABLE"] = {
            "met": False,
            "reason": f"nonzero preferred equity ({preferred:,.0f} USD) with no explicit preferred cost",
        }
    ready = all(states[name]["met"] for name in READINESS_STATES[:4])
    states["DCF_EVALUABLE"] = {
        "met": ready,
        "reason": "inputs, policy evidence and capital costs data-complete "
        "(DCF not run here; market price/beta/Treasury still required)"
        if ready
        else "blocked by earlier states",
    }
    return {"states": states, "valuation_ready": states["DCF_EVALUABLE"]["met"]}


def _doc_tax_policy(doc, tax_override=None, tax_scenario=None):
    """Record the reported-vs-forecast tax position on a loaded document."""
    from tax_policy import TaxPolicyError, document_tax_policy

    try:
        return document_tax_policy(
            doc.get("historical", []),
            user_override=tax_override,
            scenario=tax_scenario,
        )
    except TaxPolicyError as exc:
        raise ProviderError(str(exc)) from None


def _packet_value(packet_row_fields, end_fields, key):
    field = end_fields.get(key)
    return field["value"] if field is not None else None


def load_sec_first(
    ticker,
    asof,
    http,
    packet,
    include_capital_costs=True,
    require_wacc=True,
    tax_override=None,
    tax_scenario=None,
):
    """Build a Yahoo-shaped financial document from a qualified packet.

    Reported history stays signed as filed. ``tax_override`` (five rates
    in 0-1) or ``tax_scenario`` (rates plus filing/period evidence) select
    an explicit forecast policy via tax_policy; the selection is recorded
    in ``doc["source"]["tax_policy"]`` without mutating history. Raises
    ProviderError with the gate's machine-readable reasons when the packet
    does not qualify, so callers can fall back with accurate warnings.
    """
    ticker = ticker_symbol(ticker)
    now = datetime.now(timezone.utc)
    if asof != now.date().isoformat():
        raise ProviderError(
            "SEC-first supports only the current UTC date; historical point-in-time snapshots are unavailable."
        )
    gate = eligibility_gate(packet, ticker, asof)
    if not gate["eligible"]:
        # An unusable latest default blocks only the unsupported default run:
        # with an explicit forecast policy supplied, a gate held up solely by
        # tax_forecast_assumption_required_* proceeds once that selection
        # itself resolves. Anything else still falls back with the reasons.
        explicit = tax_override is not None or tax_scenario is not None
        tax_only = gate["reasons"] and all(
            r.startswith("tax_forecast_assumption_required_") for r in gate["reasons"]
        )
        if tax_only and explicit:
            from tax_policy import TaxPolicyError, resolve_forecast_tax

            try:
                history_rates = [
                    ((row.get("fields") or {}).get("tax_rate") or {}).get("value")
                    for row in packet.get("historical", [])
                ]
                resolve_forecast_tax(
                    history_rates, user_override=tax_override, scenario=tax_scenario
                )
            except (TaxPolicyError, KeyError, TypeError) as exc:
                raise ProviderError(str(exc)) from None
        else:
            raise ProviderError(
                "SEC-first path unavailable: " + "; ".join(gate["reasons"])
            )
    from yahoo_provider import finite
    import served_market

    served = served_market.latest_price(ticker, asof)
    price, price_day = served["price"], served["price_as_of"]
    from issuer_classification import reviewed_identity

    identity = reviewed_identity(ticker, packet.get("cik"), asof)
    if identity is not None:
        name, cik = identity
    else:
        # No direct SEC directory lookup: identity comes from the served
        # packet only. An unreviewed issuer keeps the ticker as its display
        # name, and the CIK is whatever the packet itself carries.
        name = ticker
        raw_cik = str(packet.get("cik") or "").strip()
        cik = raw_cik.zfill(10) if raw_cik.isdigit() else None
    doc = blank_document(ticker, name, asof, "api")
    doc["company"].update(eligible=True, security_type="EQUITY")
    warnings = [
        "SEC-first statement path: annual financials come from the published PPE/SEC packet; no Yahoo annual-statement request was made.",
        "Market price and beta come from served CRSP price history through the Zion serving layer, not from filings or Yahoo.",
        "Other nonoperating assets are explicitly assumed to be zero; review excess investments and other adjustments.",
        "Market equity weights use annual weighted-average diluted shares, which proxy for ordinary outstanding shares; per-share valuation uses the same diluted basis.",
    ]
    common_by_end = {x["period_end"]: x for x in packet["common_income"]}
    dividend_by_end = {x["period_end"]: x for x in packet.get("dividends", [])}
    diluted_by_end = {}
    for row in packet["historical"]:
        end = row["period_end"]
        fields = row["fields"]
        common = common_by_end[end]
        tax = fields["tax_rate"]["value"]
        packet_row = {
            "period_end": end,
            "available_at": max(
                [fields[k]["available_at"] for k in STATEMENT_FIELDS]
                + [common["available_at"]]
            ),
            "revenue": fields["revenue"]["value"],
            "ebit": fields["ebit"]["value"],
            "net_income": common["value"],
            "capex": abs(fields["capex"]["value"]),
            "d_and_a": fields["d_and_a"]["value"],
            "nwc": fields["nwc"]["value"],
            "book_value": fields["book_value"]["value"],
            "tax_rate": tax,
            "provenance": {
                k: deepcopy(fields[k]["provenance"]) for k in STATEMENT_FIELDS
            },
        }
        packet_row["provenance"]["net_income"] = deepcopy(common["provenance"])
        packet_row["provenance"]["net_income"]["basis"] = (
            "Bridged direct SEC NetIncomeLossAvailableToCommonStockholdersBasic; "
            "consolidated income never substitutes."
        )
        diluted = (fields.get("diluted_shares") or {}).get("value")
        diluted_by_end[end] = diluted
        doc["historical"].append(packet_row)
    bridge_src = packet["bridge"]
    end = packet["historical"][-1]["period_end"]
    preferred = bridge_src["preferred_equity"]["value"]
    minority = bridge_src["minority_interest"]["value"]
    if minority < 0:
        warnings.append(
            f"Reported minority interest is negative ({minority:,.0f} USD) and is carried as reported. "
            "FCFF DCF and EV-based multiples are blocked by it; P/E and P/B do not use it."
        )
    if preferred != 0 and include_capital_costs and require_wacc:
        raise ProviderError(
            "Nonzero preferred equity requires an explicit preferred cost assumption; SEC-first WACC cannot be completed."
        )
    doc["bridge"].update(
        short_term_debt=bridge_src["short_term_debt"]["value"],
        long_term_debt=bridge_src["long_term_debt"]["value"],
        cash=bridge_src["cash"]["value"],
        preferred_equity=preferred,
        minority_interest=minority,
        other_nonoperating_assets=0.0,
        as_of=end,
    )
    diluted = packet["diluted_shares"]["value"]
    if diluted <= 0:
        raise ProviderError("SEC packet diluted shares must be positive.")
    doc["market"].update(
        price=price,
        price_as_of=price_day,
        diluted_shares=diluted,
        shares_basis=(
            "SEC packet annual weighted-average diluted shares, "
            f"{packet['diluted_shares']['period_end']}; annual weighted-average dilution"
        ),
    )
    costs = {}
    if include_capital_costs:
        warnings.extend(
            [
                "Capital costs use dated market inputs and explicit equity risk premium and credit spread assumptions.",
                "Market equity weights use annual diluted shares as a proxy for ordinary outstanding shares.",
            ]
        )
        beta, n = served_market.served_beta(ticker, asof)
        # Fails closed with SERVED_RISK_FREE_RATE_NOT_CONFIGURED until the
        # serving layer publishes a Treasury yield series; no Yahoo pull.
        rf_record = served_market.risk_free_rate(asof)
        rf, rf_date = rf_record["rate"], rf_record["as_of"]
        if rf_date > asof or not 0 <= rf < 1:
            raise ProviderError("Served Treasury yield date or units are invalid.")
        debt = doc["bridge"]["short_term_debt"] + doc["bridge"]["long_term_debt"]
        interest = (
            packet["interest_expense"]["value"]
            if packet.get("interest_expense") is not None
            else None
        )
        cost_debt = abs(interest) / debt if interest is not None and debt > 0 else rf + 0.015
        basis = (
            f"Latest annual interest expense / latest annual debt, {end}"
            if interest is not None and debt > 0
            else f"Dated Treasury yield ({rf_date}) + assumed 1.5% credit spread; latest interest expense unavailable or no debt"
        )
        if interest is None:
            warnings.append(
                "Latest annual interest expense is missing; cost of debt uses current Treasury yield plus assumed credit spread."
            )
        cost_equity = rf + beta * 0.05
        equity = finite(diluted * price, "equity market value")
        # The shield uses the selected forecast policy (latest default or an
        # explicit override/scenario resolved in _doc_tax_policy below), so a
        # signed latest history with an explicit policy still gets coherent
        # capital costs instead of a bounds refusal.
        try:
            from tax_policy import TaxPolicyError, document_tax_policy as _document_tax_policy

            _policy = _document_tax_policy(
                doc["historical"], user_override=tax_override, scenario=tax_scenario
            )
            tax = _policy["selected"]["rates"][0]
        except (TaxPolicyError, KeyError, TypeError, IndexError) as exc:
            raise ProviderError(str(exc)) from None
        tax_explicit = tax_override is not None or tax_scenario is not None
        if debt < 0:
            raise ProviderError("Debt is outside supported bounds.")
        costs = {
            "risk_free_rate": rf,
            "risk_free_rate_as_of": rf_date,
            "beta": beta,
            "beta_basis": f"Five-year weekly total returns from served CRSP price history versus SPY; {n} aligned observations",
            "equity_risk_premium": 0.05,
            "credit_spread": 0.015,
            "cost_of_debt": cost_debt,
            "cost_of_equity": cost_equity,
            "wacc": (equity * cost_equity + debt * cost_debt * (1 - tax)) / (equity + debt)
            if require_wacc
            else None,
            "capital_cost_method": "wacc" if require_wacc else "equity",
            "debt_cost_basis": basis,
            "equity_market_value": equity,
            "market_equity_value": equity,
            "market_equity_basis": "diluted weighted-average shares proxy for ordinary outstanding",
            "debt_book_value": debt,
            "debt": debt,
            "tax_rate": tax,
            "tax_shield_basis": (
                "explicit forecast policy" if tax_explicit else "latest reported rate"
            ),
            "preferred_equity": preferred,
            "preferred_cost": None,
            "reported_cost_of_debt": abs(interest) / debt
            if interest is not None and debt > 0
            else None,
            "equity_shares_as_of": end,
        }
    common = None
    if preferred == 0 and minority == 0:
        common = doc["historical"][-1]["book_value"]
        warnings.append(
            "Common book equity equals total book value: verified zero preferred equity and zero noncontrolling interest."
        )
    else:
        warnings.append(
            "Common book equity is unavailable (preferred or noncontrolling claims are nonzero or unverified); common P/B and ROE cannot be computed."
        )
    dividend_rows = []
    for row in packet["historical"]:
        d = dividend_by_end.get(row["period_end"])
        dividend_rows.append(
            {
                "period_end": row["period_end"],
                "value": abs(d["value"]) if d is not None else None,
                "shares": diluted_by_end.get(row["period_end"]),
            }
        )
    dividends = dividend_rows[-1]["value"] if dividend_rows else None
    if dividends is None:
        warnings.append(
            "Common cash dividends are unavailable; DDM cannot be computed. Missing dividends do not mean zero."
        )
    doc["source"].update(
        name="PPE / SEC packet statements + Zion served market inputs (SEC-first)",
        available_at=asof,
        retrieved_at=now.isoformat(),
        warnings=warnings,
        capital_costs=costs,
        common_dividends={
            "historical": dividend_rows,
            "value": dividends,
            "per_share": dividends / diluted if dividends is not None else None,
            "period_end": end,
            "shares_basis": "Annual diluted weighted-average shares",
            "unit": "USD",
        },
        common_book_equity={
            "value": common,
            "period_end": end,
            "unit": "USD",
            "historical": [
                {"period_end": r["period_end"], "value": None} for r in packet["historical"]
            ],
            "basis": "derived: book value less zero preferred and zero noncontrolling interest"
            if common is not None
            else "unavailable",
        },
        finance_diagnostics={
            "roe": doc["historical"][-1]["net_income"] / common if common else None,
            "roe_basis": "Latest annual common net income / ending common equity",
            "period_end": end,
        },
        bridge_provenance={
            k: deepcopy(bridge_src[k]["provenance"])
            for k in BRIDGE_FIELDS
            if k in bridge_src and bridge_src[k] is not None
        },
        market_observation={"price": price, "currency": "USD", "as_of": price_day},
        market_provenance=served["provenance"],
        statement_source="SEC-first",
        ppe_release=packet["source"],
        ppe_cutoff=packet["cutoff_date"],
        tax_policy=_doc_tax_policy(doc, tax_override, tax_scenario),
    )
    for key, value in costs.items():
        if isinstance(value, (int, float)):
            finite(value, key)
    # Adjustment evidence preferably rides with the validated packet
    # publication (no network). Packets predating the evidence use the
    # bounded live companyconcept fallback only under the local-development
    # direct-fetch flag; in production the fallback reports unavailable
    # evidence instead of fetching SEC directly (see accounting_policy).
    # The fetch is also skipped when the shared budget is nearly spent
    # (pending, never zero). Never fails the load.
    began_adjust = time.monotonic()
    period_ends = [r["period_end"] for r in doc["historical"]]
    published = packet.get("adjustment_facts") if isinstance(packet, dict) else None
    if isinstance(published, dict) and isinstance(published.get("facts"), dict):
        doc["source"]["accounting_adjustments"] = published
        doc["source"]["accounting_adjustments_source"] = "published with packet"
    else:
        from accounting_policy import fetch_adjustment_facts

        deadline = getattr(http, "deadline", None)
        remaining = None if deadline is None else deadline - time.monotonic()
        if remaining is not None and remaining < 1.5:
            doc["source"]["accounting_adjustments"] = {
                "schema_version": "accounting-adjustments-v1",
                "status": "pending",
                "facts": {},
                "ebit_facts": [],
                "unavailable": [
                    {
                        "kind": "all",
                        "tag": None,
                        "reason": (
                            "not fetched: only "
                            f"{max(remaining, 0):.2f}s of the shared request budget remained"
                        ),
                    }
                ],
                "conflicts": [],
                "future_restatements": [],
            }
            doc["source"]["accounting_adjustments_source"] = "pending"
        else:
            try:
                facts = fetch_adjustment_facts(
                    cik, period_ends, http, as_of=asof, include_ebit=True
                )
                facts["status"] = "resolved"
                doc["source"]["accounting_adjustments"] = facts
                doc["source"]["accounting_adjustments_source"] = (
                    "SEC companyconcept (validated at load; packet predates published evidence)"
                )
            except Exception as exc:
                doc["source"]["accounting_adjustments"] = {
                    "schema_version": "accounting-adjustments-v1",
                    "status": "unavailable",
                    "facts": {},
                    "ebit_facts": [],
                    "unavailable": [
                        {"kind": "all", "tag": None, "reason": f"lookup failed: {exc}"[:160]}
                    ],
                    "conflicts": [],
                    "future_restatements": [],
                }
                doc["source"]["accounting_adjustments_source"] = "unavailable"
    doc["source"]["accounting_adjustments_timing"] = round(
        time.monotonic() - began_adjust, 3
    )
    try:
        parse_document(doc, minority_may_be_negative=True)
    except ValueError as exc:
        raise ProviderError(f"SEC-first snapshot failed validation: {exc}") from None
    return doc
