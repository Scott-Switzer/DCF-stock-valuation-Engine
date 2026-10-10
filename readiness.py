"""Per-method readiness: what each method can honestly compute from this snapshot.

Each method reports one state with the exact missing fields, the fallback
fields, the reasons and machine-readable ``codes``. No score is invented.
Precedence:

- unavailable: a required input is missing, or the method does not apply.
- stale: the market price is older than PRICE_STALE_DAYS at the valuation date.
- fallback: every input is present, but one came from a labelled fallback.
- sufficient: every required input is present from its primary source.

Forecast assumptions are user inputs and are not checked here. Fallback
provenance comes from the PPE overlay's field coverage, which records each
field as ``PPE`` or ``fallback``. Documents without that record report no
fallbacks rather than guessing. ``field_status`` gives the per-field view:
present, missing or fallback. Missing values are never converted to zero.
"""

from datetime import date

from dcf_loader import BRIDGE_FIELDS, HISTORY_FIELDS
from issuer_classification import financial_block_reason, is_confirmed

PRICE_STALE_DAYS = 7
# Peers loaded automatically but not reviewed never feed an automatic relative value.
BLOCKED_PEER_STATUSES = frozenset({"candidate", "excluded"})
LABELS = {
    "sufficient": "Sufficient inputs",
    "fallback": "Fallback used",
    "stale": "Stale price",
    "unavailable": "Unavailable",
}
# Source metrics that are present in a provider packet but deliberately not used
# for a valuation field. Each note explains why, so readiness can name it.
RELATED_SOURCE_METRICS = {
    "market.diluted_shares": ("shares_outstanding",),
    "bridge.cash": ("cash",),
    "bridge.short_term_debt": ("total_debt",),
    "bridge.long_term_debt": ("total_debt",),
}


def _issue(code, field, label):
    return {"code": code, "field": field, "label": label}


def _missing_issues(doc):
    """Every absent required value, as code, field path and display label."""
    issues = []
    market = doc.get("market", {})
    if market.get("price") is None:
        issues.append(_issue("missing_market_price", "market.price", "market price"))
    if market.get("diluted_shares") is None:
        issues.append(_issue("missing_diluted_shares", "market.diluted_shares", "diluted shares"))
    bridge = doc.get("bridge", {})
    for key in BRIDGE_FIELDS:
        if bridge.get(key) is None:
            issues.append(_issue(f"missing_bridge_{key}", f"bridge.{key}", f"bridge {key}"))
    for row in doc.get("historical", []):
        period = row.get("period_end")
        for key in HISTORY_FIELDS:
            if row.get(key) is None:
                issues.append(
                    _issue(f"missing_history_{key}", f"historical.{period}.{key}", f"{period} {key}")
                )
    return issues


def _fallback_paths(doc):
    return [
        entry["field"]
        for entry in doc.get("source", {}).get("field_coverage", [])
        if isinstance(entry, dict) and entry.get("status") != "PPE" and entry.get("field")
    ]


def _in_scope(path, method):
    """Whether a fallback field feeds this method's calculation."""
    if path.startswith(("historical.", "bridge.", "market.", "capital_costs.")):
        return True
    if path == "common_dividends":
        return method == "ddm"
    return False


def _is_stale(doc):
    price_as_of = doc.get("market", {}).get("price_as_of")
    if not price_as_of:
        return False
    age = date.fromisoformat(doc["valuation_date"]) - date.fromisoformat(str(price_as_of)[:10])
    return age.days > PRICE_STALE_DAYS


def _excluded_notes(doc, issues):
    """Explain source metrics that were present but not used for a missing field."""
    excluded = doc.get("source", {}).get("excluded_metrics") or {}
    notes = []
    for issue in issues:
        for metric in RELATED_SOURCE_METRICS.get(issue["field"], ()):
            if metric in excluded:
                notes.append(f"Source metric {metric} is present but not used: {excluded[metric]}")
    return notes


def _assess(method, doc, issues, blocking, fallbacks):
    scoped = [path for path in fallbacks if _in_scope(path, method)]
    stale = _is_stale(doc)
    unavailable = bool(blocking or issues)
    reasons = [b["reason"] for b in blocking]
    codes = [b["code"] for b in blocking]
    if issues:
        reasons.append("Missing: " + ", ".join(i["label"] for i in issues))
        codes += [i["code"] for i in issues]
        reasons += _excluded_notes(doc, issues)
    if stale and not unavailable:
        reasons.append(f"Market price is older than {PRICE_STALE_DAYS} days at the valuation date.")
        codes.append("stale_price")
    if scoped and not unavailable:
        reasons.append("Fallback inputs: " + ", ".join(scoped))
        codes.append("fallback_input")
    if unavailable:
        state = "unavailable"
    elif stale:
        state = "stale"
    elif scoped:
        state = "fallback"
    else:
        state = "sufficient"
    return {
        "state": state,
        "label": LABELS[state],
        "missing": [i["label"] for i in issues],
        "fallback": scoped,
        "reasons": reasons,
        "codes": codes,
    }


def field_status(doc):
    """Per-field view of the valuation inputs: present, missing or fallback."""
    issues = {i["field"]: i["code"] for i in _missing_issues(doc)}
    fallbacks = set(_fallback_paths(doc))
    paths = ["market.price", "market.diluted_shares"]
    paths += [f"bridge.{key}" for key in BRIDGE_FIELDS]
    paths += [
        f"historical.{row.get('period_end')}.{key}"
        for row in doc.get("historical", [])
        for key in HISTORY_FIELDS
    ]
    status = {}
    for path in paths:
        if path in issues:
            status[path] = {"status": "missing", "code": issues[path]}
        elif path in fallbacks:
            status[path] = {"status": "fallback", "code": "fallback_input"}
        else:
            status[path] = {"status": "present", "code": None}
    return status


def reliable_peers(comparables):
    """Peers allowed to feed an automatic relative value. Manual peers carry no status."""
    return [p for p in comparables or [] if p.get("review_status") not in BLOCKED_PEER_STATUSES]


def _sector_blocking(doc):
    """Industrial FCFF DCF does not apply to financial firms, whatever the NCI sign."""
    reason = financial_block_reason(doc)
    if reason:
        return [{"code": "financial_firm_enterprise_model", "reason": reason}]
    return []


def _minority_blocking(doc):
    """A reported negative noncontrolling interest blocks FCFF DCF, not P/E or P/B."""
    value = doc.get("bridge", {}).get("minority_interest")
    if isinstance(value, (int, float)) and value < 0:
        return [
            {
                "code": "negative_minority_interest",
                "reason": (
                    "Reported noncontrolling interest is negative. FCFF DCF requires a "
                    "nonnegative equity bridge; P/E and P/B do not use it."
                ),
            }
        ]
    return []


def _relative_assessment(doc, issues, blocking, fallbacks):
    """Relative stays usable for P/E and P/B when only EV-based claims are affected."""
    result = _assess("relative", doc, issues, blocking, fallbacks)
    if _minority_blocking(doc):
        result["reasons"].append(
            "Negative noncontrolling interest blocks EV-based multiples; P/E and P/B remain available."
        )
        result["codes"].append("negative_minority_ev_blocked")
    return result


def method_readiness(doc, relative_doc=None):
    """Readiness for DCF, DDM, residual income and relative valuation from one snapshot.

    ``relative_doc`` is the document the relative lane actually computed from,
    when it loaded its own peer set. Peers are read from it when given.
    """
    issues = _missing_issues(doc)
    market = [i for i in issues if i["field"].startswith("market.")]
    fallbacks = _fallback_paths(doc)

    dividend = (doc.get("source", {}).get("common_dividends") or {}).get("value")
    ddm_blocking = []
    if not (isinstance(dividend, (int, float)) and dividend > 0):
        ddm_blocking.append(
            {
                "code": "no_common_dividend",
                "reason": "No verified common dividend in this snapshot; DDM does not apply.",
            }
        )

    peer_source = relative_doc if relative_doc is not None else doc
    peers = peer_source.get("comparables") or []
    usable_peers = [
        peer
        for peer in reliable_peers(peers)
        if any(
            isinstance(v, (int, float)) and v > 0 for v in (peer.get("multiples") or {}).values()
        )
    ]
    candidates = [p["ticker"] for p in peers if p.get("review_status") in BLOCKED_PEER_STATUSES]
    relative_blocking = []
    if not usable_peers and candidates:
        relative_blocking.append(
            {
                "code": "unverified_peers_only",
                "reason": (
                    f"Loaded peers are unverified candidates ({', '.join(candidates)}); none is "
                    "a reviewed comparable. Confirm or replace peers to calculate."
                ),
            }
        )
    elif not usable_peers:
        relative_blocking.append(
            {"code": "no_usable_peers", "reason": "No peers with usable multiples in this snapshot."}
        )

    residual_blocking = []
    for key, label in [
        ("preferred_equity", "Preferred equity"),
        ("minority_interest", "Noncontrolling interest"),
    ]:
        if (doc.get("bridge", {}).get(key) or 0) != 0:
            residual_blocking.append(
                {
                    "code": f"senior_claim_{key}",
                    "reason": f"{label} claims are not modeled by residual income in this release.",
                }
            )

    dcf = _assess("dcf", doc, issues, _sector_blocking(doc) + _minority_blocking(doc), fallbacks)
    record = doc.get("source", {}).get("classification")
    if record is not None and not is_confirmed(record) and dcf["state"] != "unavailable":
        # An explicit unknown record is not a confirmed operating-company classification.
        # Documents with no classification record (demo, manual) are unchanged.
        dcf["reasons"].append(
            "Industry classification is unconfirmed; confirm operating-company suitability before using FCFF DCF."
        )
        dcf["codes"].append("classification_unconfirmed")
        if dcf["state"] == "sufficient":
            dcf["state"], dcf["label"] = "fallback", LABELS["fallback"]
    return {
        "dcf": dcf,
        "ddm": _assess("ddm", doc, market, ddm_blocking, fallbacks),
        "residual": _assess("residual", doc, issues, residual_blocking, fallbacks),
        "relative": _relative_assessment(doc, issues, relative_blocking, fallbacks),
    }
