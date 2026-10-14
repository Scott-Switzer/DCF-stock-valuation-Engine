"""SEC-first statement path: bypass Yahoo annual statements for qualified issuers.

A company qualifies only when its published PPE packet already contains every
statement input the DCF contract requires, with common-shareholder net income
coming exclusively from a bridged direct SEC tag. Anything else keeps the
existing Yahoo annual-statement path with accurate source warnings.

Market inputs (price, beta, Treasury yield) still come from Yahoo market
endpoints; only the annual *statement* request is bypassed.
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
        tax = (fields.get("tax_rate") or {}).get("value")
        if tax is not None and not 0 <= tax <= 1:
            reasons.append(f"tax_rate_out_of_bounds_{end}")
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
):
    """Build a Yahoo-shaped financial document from a qualified packet.

    Raises ProviderError with the gate's machine-readable reasons when the
    packet does not qualify, so callers can fall back with accurate warnings.
    """
    ticker = ticker_symbol(ticker)
    now = datetime.now(timezone.utc)
    if asof != now.date().isoformat():
        raise ProviderError(
            "SEC-first supports only the current UTC date; historical point-in-time snapshots are unavailable."
        )
    gate = eligibility_gate(packet, ticker, asof)
    if not gate["eligible"]:
        raise ProviderError(
            "SEC-first path unavailable: " + "; ".join(gate["reasons"])
        )
    from yahoo_provider import chart, market_quote, market_beta, finite

    stock = chart(http, ticker)
    meta = stock.get("meta", {})
    if meta.get("symbol") != ticker or meta.get("instrumentType") != "EQUITY":
        raise ProviderError("Yahoo requires an operating-company equity ticker.")
    if meta.get("currency") != "USD":
        raise ProviderError("Yahoo market currency must be USD.")
    price, price_day = market_quote(meta, asof)
    try:
        directory = http.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers={"User-Agent": "DCF-Valuation-Engine/1.0", "Accept": "application/json"},
            ttl=86400,
            cache_key="sec-directory",
        )
        entry = next(
            (
                r
                for r in directory.values()
                if str(r.get("ticker", "")).replace(".", "-") == ticker
            ),
            None,
        )
        name = entry.get("title", ticker) if entry else ticker
        cik = str((entry or {}).get("cik_str", "")).zfill(10) or None
    except ProviderError:
        name = ticker
        cik = None
    doc = blank_document(ticker, name, asof, "api")
    doc["company"].update(eligible=True, security_type="EQUITY")
    warnings = [
        "SEC-first statement path: annual financials come from the published PPE/SEC packet; no Yahoo annual-statement request was made.",
        "Market price, beta and Treasury inputs remain dated Yahoo market observations, not filings.",
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
        benchmark, treasury = chart(http, "SPY"), chart(http, "^TNX")
        beta, n = market_beta(stock, benchmark)
        tm = treasury.get("meta", {})
        if tm.get("symbol") != "^TNX" or benchmark.get("meta", {}).get("symbol") != "SPY":
            raise ProviderError("Yahoo returned a mismatched capital-cost benchmark.")
        rf_date = (
            datetime.fromtimestamp(
                finite(tm.get("regularMarketTime"), "Treasury timestamp"), timezone.utc
            )
            .date()
            .isoformat()
        )
        rf = finite(tm.get("regularMarketPrice"), "Treasury yield") / 100
        if rf_date > asof or not 0 <= rf < 1:
            raise ProviderError("Yahoo Treasury yield date or units are invalid.")
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
        tax = doc["historical"][-1]["tax_rate"]
        if debt < 0 or not 0 <= tax <= 1:
            raise ProviderError("Debt or effective tax rate is outside supported bounds.")
        costs = {
            "risk_free_rate": rf,
            "risk_free_rate_as_of": rf_date,
            "beta": beta,
            "beta_basis": f"Five-year weekly adjusted total returns versus SPY; {n} aligned observations",
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
        name="PPE / SEC packet statements + Yahoo market inputs (SEC-first)",
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
        statement_source="SEC-first",
        ppe_release=packet["source"],
        ppe_cutoff=packet["cutoff_date"],
    )
    for key, value in costs.items():
        if isinstance(value, (int, float)):
            finite(value, key)
    # Adjustment evidence preferably rides with the validated packet
    # publication (no network). Packets predating the evidence keep the
    # bounded live companyconcept fallback so existing issuers (e.g. via the
    # Zion binding) retain their audited add-backs until republication; the
    # fetch is skipped when the shared budget is nearly spent (pending, never
    # zero). Never fails the load.
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
