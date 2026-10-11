"""Offline financial QA receipts. Readiness is not independent source verification.

This module does not acquire data, persist research, or silently repair inputs.
Keep source quality, method suitability and numerical reconciliation separate.
"""

from datetime import date
import math

from dcf_loader import BRIDGE_FIELDS, HISTORY_FIELDS, parse_document
from issuer_classification import is_confirmed
from readiness import method_readiness

QA_UNIVERSE = (
    "AAPL", "MSFT", "GOOGL", "META", "AMZN", "NVDA", "AMD", "ORCL", "CRM",
    "KO", "PEP", "COST", "WMT", "JNJ", "ABBV", "XOM", "CVX", "CAT", "DE",
    "UPS", "JPM", "BAC", "GS", "MRX", "O",
)
YAHOO_FIELDS = {
    "revenue": ("TotalRevenue",), "ebit": ("OperatingIncome",),
    "net_income": ("NetIncomeCommonStockholders",), "capex": ("CapitalExpenditure",),
    "d_and_a": ("ReconciledDepreciation", "DepreciationAndAmortization"),
    "book_value": ("StockholdersEquity",), "short_term_debt": ("CurrentDebt",),
    "long_term_debt": ("LongTermDebt",), "cash": ("CashAndCashEquivalents",),
    "preferred_equity": ("PreferredStockEquity", "StockholdersEquity", "CommonStockEquity"),
    "minority_interest": ("MinorityInterest", "TotalEquityGrossMinorityInterest", "StockholdersEquity"),
    "nwc": ("CurrentAssets", "CashAndCashEquivalents", "CurrentLiabilities", "CurrentDebt"),
}


def observation_provenance(records, key):
    if key in records:
        return records[key]
    components = [records[name] for name in YAHOO_FIELDS.get(key, ()) if name in records]
    if not components:
        return None
    return {"provider_records": components, "mapping": key,
            "note": "Raw provider observations; derived/sign-adjusted valuation values may differ."}


def issue(code, field, reason, severity="warning"):
    return {"code": code, "field": field, "reason": reason, "severity": severity}


def source_receipts(doc):
    """Record values, dates and provenance without treating provider labels as audits."""
    source = doc.get("source", {})
    coverage = {r["field"]: r for r in source.get("field_coverage", []) if r.get("field")}
    observations = []

    def add(path, value, period=None, available=None, provenance=None, unit="USD"):
        record = coverage.get(path, {})
        observations.append({
            "field": path, "value": value, "unit": unit,
            "period_end": record.get("period_end", period),
            "available_at": record.get("available_at", available),
            "provider_status": record.get("status", "not_recorded"),
            "provenance": record.get("provenance", provenance),
            "independently_source_verified": False,
        })

    for row in doc.get("historical", []):
        period = row.get("period_end")
        for key in HISTORY_FIELDS:
            add(f"historical.{period}.{key}", row.get(key), period, row.get("available_at"),
                observation_provenance(row.get("provenance") or {}, key), "pure" if key == "tax_rate" else "USD")
        ebit, da = row.get("ebit"), row.get("d_and_a")
        add(f"historical.{period}.ebitda", ebit + da if ebit is not None and da is not None else None,
            period, row.get("available_at"), {"definition": "operating income plus reported D&A; not adjusted EBITDA"})
    for key in BRIDGE_FIELDS:
        raw = (source.get("bridge_provenance") or {}).get(key) or {}
        add(f"bridge.{key}", doc.get("bridge", {}).get(key), raw.get("period_end"),
            raw.get("available_at"), raw.get("provenance", raw) or
            observation_provenance(source.get("bridge_provenance") or {}, key))
    market = doc.get("market", {})
    add("market.price", market.get("price"), market.get("price_as_of"))
    add("market.diluted_shares", market.get("diluted_shares"), market.get("shares_as_of"),
        provenance={"basis": market.get("shares_basis")}, unit="shares")
    for key in ("common_dividends", "common_book_equity"):
        raw = source.get(key) or {}
        add(f"source.{key}", raw.get("value"), raw.get("period_end"), raw.get("available_at"), raw.get("provenance"))
    return observations


def audit_snapshot(doc):
    """Assess an already loaded snapshot, retaining exact contract/blocking reasons."""
    source = doc.get("source", {})
    findings = []
    try:
        parse_document(doc, minority_may_be_negative=True)
    except (ValueError, TypeError, KeyError) as exc:
        findings.append(issue("invalid_contract", "financials", str(exc), "error"))
        return {"status": "FAIL", "issues": findings, "methods": {}, "observations": []}

    classification = source.get("classification") or {}
    if not is_confirmed(classification):
        findings.append(issue("classification_unconfirmed", "source.classification", "SEC industry classification has not been confirmed."))
    findings.append(issue("filing_reconciliation_pending", "source", "Provider provenance retained; this automated audit has not independently reconciled every observation to filings."))
    if source.get("kind") == "synthetic" or source.get("origin_kind") == "synthetic":
        findings.append(issue("synthetic_data", "source.kind", "Synthetic data is not real-company evidence."))
    if "current" in str(source.get("name", "")).lower() or source.get("kind") not in {"sec", "zion"}:
        findings.append(issue("point_in_time_not_established", "source", "Snapshot retrieval dates do not establish point-in-time filing availability."))

    observations = source_receipts(doc)
    cutoff = date.fromisoformat(doc["valuation_date"])
    for record in observations:
        for key in ("available_at", "period_end"):
            value = record.get(key)
            if not value:
                continue
            try:
                observed = date.fromisoformat(str(value)[:10])
            except ValueError:
                findings.append(issue("invalid_observation_date", record["field"], f"Invalid {key} date.", "error"))
                continue
            if observed > cutoff:
                findings.append(issue("future_observation", record["field"], f"{key} {value} is after valuation date {cutoff}.", "error"))
    price_date = date.fromisoformat(doc["market"]["price_as_of"])
    if price_date > cutoff:
        findings.append(issue("future_price", "market.price_as_of", "Price observation is after the valuation date.", "error"))

    methods = {}
    for method, state in method_readiness(doc).items():
        status = "BLOCKED" if state["state"] == "unavailable" else "PARTIAL"
        methods[method] = {"status": status, "readiness": state, "calculation_check": "NOT_RUN",
                           "reasons": list(state["reasons"]), "reconciled_fields": []}
        if status != "BLOCKED":
            methods[method]["reasons"].append("Calculation and source observations have not both been independently validated.")
    return {
        "ticker": doc["company"]["ticker"], "company_name": doc["company"].get("name"),
        "valuation_date": doc["valuation_date"], "source": source.get("name"),
        "classification": classification, "currency": doc["company"]["currency"], "units": doc["units"],
        "price_as_of": doc["market"]["price_as_of"], "price_age_days": (cutoff - price_date).days,
        "shares_basis": doc["market"].get("shares_basis"), "status": "FAIL" if any(x["severity"] == "error" for x in findings) else "PARTIAL",
        "issues": findings, "methods": methods, "observations": observations,
        "source_warnings": source.get("warnings", []),
    }


def capital_cost_check(doc):
    """Reconcile reported WACC components; do not certify beta or risk-free inputs."""
    costs = doc.get("source", {}).get("capital_costs") or {}
    keys = ("risk_free_rate", "beta", "equity_risk_premium", "equity_market_value",
            "debt", "cost_of_debt", "tax_rate", "preferred_equity", "wacc")
    if any(not isinstance(costs.get(k), (int, float)) or isinstance(costs.get(k), bool)
           or not math.isfinite(costs[k]) for k in keys):
        return {"status": "BLOCKED", "reason": "Complete finite WACC components are not recorded."}
    equity, debt, preferred = (costs[k] for k in ("equity_market_value", "debt", "preferred_equity"))
    kp = costs.get("preferred_cost")
    if equity <= 0 or min(debt, preferred) < 0 or (preferred and (
        not isinstance(kp, (int, float)) or isinstance(kp, bool) or not math.isfinite(kp) or kp < 0
    )):
        return {"status": "BLOCKED", "reason": "Unsupported capital structure or missing preferred cost."}
    ke = costs["risk_free_rate"] + costs["beta"] * costs["equity_risk_premium"]
    expected = (equity * ke + debt * costs["cost_of_debt"] * (1 - costs["tax_rate"])
                + preferred * (costs.get("preferred_cost") or 0)) / (equity + debt + preferred)
    return {"status": "PASS" if math.isclose(expected, costs["wacc"], rel_tol=1e-9, abs_tol=1e-12) else "FAIL",
            "expected": expected, "reported": costs["wacc"],
            "scope": "Component arithmetic only; beta, market observations and credit spread are not independently source-verified."}
