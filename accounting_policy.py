"""Source-independent accounting basis: evidence, classification, normalization.

Reported observations are immutable here. This module (a) extracts separately
disclosed adjustment facts from SEC companyfacts with filing-grade validation,
(b) classifies the accounting basis a snapshot actually uses, and (c) derives an
adjusted series only when a user-selected policy asks for one *and* the filing
evidence supports the add-back.

Rules enforced in code, not documentation:

1. No number is selected merely because its period-end matches. Issuer CIK,
   taxonomy, USD unit, annual duration, accepted form and the filing cutoff are
   all validated, and unresolved same-period conflicts are rejected outright.
2. A disclosed impairment is not automatically an EBIT add-back. The reported
   EBIT must be demonstrated to include it: the doc's EBIT is compared against
   SEC ``OperatingIncomeLoss`` for the same period. If EBIT equals GAAP
   operating income, the charge is inside it (add-back allowed); if EBIT equals
   GAAP operating income *plus* the charge, the charge is already excluded and
   the add-back is refused.
3. Impairment normalization never assumes non-recurrence; the ledger reports how
   many loaded periods carry charges and flags all-period cases.
4. Operating-lease ROU amortization is never added back (no matching bridge
   liability), and provider conventions are labeled *unverified* rather than
   "incomparable" unless a source-specific reconciliation is attached.
5. Absence is reported as unavailable, never as zero.

No ticker names or numeric constants live here.
"""

from copy import deepcopy
from datetime import date

# Kind -> tags that may carry the separately-disclosed charge, plus any other
# kind it could double count against when both match the same period.
ADJUSTMENT_TAGS = {
    "intangible_impairment": {
        "tags": ("ImpairmentOfIntangibleAssetsExcludingGoodwill",),
        "overlaps": (),
    },
    "goodwill_impairment": {
        "tags": ("GoodwillImpairmentLoss",),
        "overlaps": (),
    },
}
EBIT_TAGS = ("OperatingIncomeLoss",)
ACCEPTED_FORMS = ("10-K", "10-K/A")
ANNUAL_DAYS = (330, 400)
USD_UNIT = "USD"
POLICIES = ("as_reported", "normalize")

_COMPANYFACTS = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json"

# Evidence-based basis labels.
BASIS_VERIFIED_GAAP = "reported_gaap_verified"
BASIS_PROVIDER = "provider_defined"
BASIS_NORMALIZED = "normalized_adjusted"
BASIS_UNVERIFIED = "mixed_or_unverified"


def _headers():
    try:
        from dcf_loader import provider_setting

        identity = provider_setting("EDGAR_IDENTITY")
    except Exception:
        identity = ""
    if "@" not in str(identity):
        return None
    return {"User-Agent": str(identity), "Accept": "application/json"}


def _as_date(value):
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _annual_span(fact):
    """Days between start and end, or None when duration evidence is absent."""
    start, end = _as_date(fact.get("start")), _as_date(fact.get("end"))
    if start is None or end is None:
        return None
    return (end - start).days


def _fetch_tag(cik, tag, http):
    """One companyconcept payload, or a reason string describing the failure."""
    headers = _headers()
    if headers is None:
        return None, "SEC identification (EDGAR_IDENTITY) is unavailable"
    try:
        payload = http.get(
            _COMPANYFACTS.format(cik=cik, tag=tag),
            headers=headers,
            ttl=86400,
            cache_key=f"sec-concept-{cik}-{tag}",
        )
    except Exception as exc:
        return None, f"lookup failed: {exc}"[:160]
    if not isinstance(payload, dict):
        return None, "non-JSON companyconcept response"
    return payload, None


def _validate_payload(payload, cik, tag):
    """Issuer, taxonomy and unit checks that apply to the whole payload."""
    taxonomy = payload.get("taxonomy")
    if taxonomy is not None and taxonomy != "us-gaap":
        return f"taxonomy {taxonomy!r} is not us-gaap"
    payload_cik = payload.get("cik")
    if payload_cik is not None and str(payload_cik).lstrip("0") != str(cik).lstrip("0"):
        return f"payload CIK {payload_cik} does not match {cik}"
    if USD_UNIT not in (payload.get("units") or {}):
        return f"no {USD_UNIT} unit for {tag}"
    return None


def _select_period_facts(payload, tag, period_ends, as_of, future, conflicts):
    """Validated 10-K/10-K-A facts keyed by period end, conflicts rejected.

    Selection is deterministic: among accepted-form facts that pass duration and
    cutoff checks, the latest ``filed`` wins per period. Two live facts sharing a
    period end and a filing date with different values are an unresolved
    conflict: the period is dropped, never guessed.
    """
    cutoff = _as_date(as_of) if as_of else None
    candidates = {}
    for fact in (payload.get("units") or {}).get(USD_UNIT, []):
        if not isinstance(fact, dict):
            continue
        end = fact.get("end")
        if end not in period_ends:
            continue
        form = fact.get("form")
        if form not in ACCEPTED_FORMS:
            continue
        span = _annual_span(fact)
        if span is None:
            continue
        if not ANNUAL_DAYS[0] <= span <= ANNUAL_DAYS[1]:
            # Quarterly or multi-year duration masquerading as an annual figure.
            continue
        if fact.get("val") is None:
            continue
        filed = _as_date(fact.get("filed"))
        if filed is None:
            # Missing or invalid filing date: not filing-grade evidence.
            continue
        if not fact.get("accn"):
            # No accession receipt: the filing context cannot be verified.
            continue
        if cutoff is not None and filed > cutoff:
            future.append(
                {
                    "period_end": end,
                    "tag": tag,
                    "amount": fact.get("val"),
                    "filed": fact.get("filed"),
                    "accession": fact.get("accn"),
                    "reason": f"filed {fact.get('filed')} after the valuation cutoff {as_of}",
                }
            )
            continue
        candidates.setdefault(end, []).append((str(fact.get("filed") or ""), fact))
    selected = {}
    for end, entries in candidates.items():
        entries.sort(key=lambda item: item[0], reverse=True)
        latest_filed = entries[0][0]
        live = [fact for filed, fact in entries if filed == latest_filed]
        values = {fact.get("val") for fact in live}
        if len(values) > 1:
            conflicts.append(
                {
                    "period_end": end,
                    "tag": tag,
                    "filed": latest_filed,
                    "values": sorted(values),
                    "reason": "same filing date carries contradictory values",
                }
            )
            continue
        fact = live[0]
        selected[end] = {
            "period_end": end,
            "amount": fact.get("val"),
            "tag": tag,
            "unit": USD_UNIT,
            "form": fact.get("form"),
            "accession": fact.get("accn"),
            "filed": fact.get("filed"),
            "period_start": fact.get("start"),
            "fiscal_year": fact.get("fy"),
            "fiscal_period": fact.get("fp"),
            "restated": bool(
                len(entries) > 1 or fact.get("form") == "10-K/A"
            ),
        }
    return selected


def fetch_adjustment_facts(
    cik,
    period_ends,
    http,
    as_of=None,
    tags=None,
    include_ebit=False,
):
    """Validated impairment (and optionally EBIT) facts for the doc's periods.

    Every returned fact carries tag, accession, form, filing date and period
    start/end. Rejections are returned with reasons instead of being dropped
    silently: ``unavailable`` (no usable evidence), ``conflicts`` (unresolved
    same-period disagreement) and ``future_restatements`` (filed after the
    cutoff, informational only).
    """
    tags = tags or ADJUSTMENT_TAGS
    wants = [p for p in (period_ends or []) if p]
    result = {
        "schema_version": "accounting-adjustments-v1",
        "cik": None,
        "as_of": as_of,
        "facts": {kind: [] for kind in tags},
        "ebit_facts": [],
        "unavailable": [],
        "conflicts": [],
        "future_restatements": [],
    }
    clean_cik = str(cik or "").strip().lstrip("0")
    if not clean_cik.isdigit():
        result["unavailable"].append(
            {"kind": "all", "tag": None, "reason": "issuer CIK unavailable"}
        )
        return result
    result["cik"] = str(cik).zfill(10)
    for kind, spec in tags.items():
        matched = False
        for tag in spec["tags"]:
            payload, failure = _fetch_tag(result["cik"], tag, http)
            if payload is None:
                result["unavailable"].append({"kind": kind, "tag": tag, "reason": failure})
                continue
            invalid = _validate_payload(payload, result["cik"], tag)
            if invalid:
                result["unavailable"].append({"kind": kind, "tag": tag, "reason": invalid})
                continue
            selected = _select_period_facts(
                payload, tag, wants, as_of, result["future_restatements"], result["conflicts"]
            )
            if selected:
                matched = True
                result["facts"][kind].extend(selected[end] for end in wants if end in selected)
            if matched:
                break
            result["unavailable"].append(
                {
                    "kind": kind,
                    "tag": tag,
                    "reason": "no validated annual 10-K fact for the loaded periods",
                }
            )
    if include_ebit:
        for tag in EBIT_TAGS:
            payload, failure = _fetch_tag(result["cik"], tag, http)
            if payload is None:
                result["unavailable"].append({"kind": "ebit", "tag": tag, "reason": failure})
                continue
            invalid = _validate_payload(payload, result["cik"], tag)
            if invalid:
                result["unavailable"].append({"kind": "ebit", "tag": tag, "reason": invalid})
                continue
            selected = _select_period_facts(
                payload, tag, wants, as_of, result["future_restatements"], result["conflicts"]
            )
            result["ebit_facts"] = [selected[end] for end in wants if end in selected]
            break
    return result


def build_adjustment_facts_from_companyfacts(cik, period_ends, facts, as_of=None, tags=None):
    """Offline adjustment evidence from a published companyfacts supplement.

    Same validation as the live path (issuer, taxonomy, USD, annual duration,
    accepted form, filing cutoff, accession, conflict rejection) but with no
    network: each tag payload is projected from the combined companyfacts
    ``facts`` dict used at packet publication time. Returns the same
    ``accounting-adjustments-v1`` shape with ``status`` resolved.
    """
    tags = tags or ADJUSTMENT_TAGS
    wants = [p for p in (period_ends or []) if p]
    result = {
        "schema_version": "accounting-adjustments-v1",
        "cik": None,
        "as_of": as_of,
        "status": "resolved",
        "facts": {kind: [] for kind in tags},
        "ebit_facts": [],
        "unavailable": [],
        "conflicts": [],
        "future_restatements": [],
    }
    clean_cik = str(cik or "").strip().lstrip("0")
    if not clean_cik.isdigit():
        result["unavailable"].append(
            {"kind": "all", "tag": None, "reason": "issuer CIK unavailable"}
        )
        return result
    result["cik"] = str(cik).zfill(10)
    # The combined source must identify the same issuer; trusted metadata is
    # never constructed from the requested CIK alone.
    source_cik = str((facts or {}).get("cik", "")).strip().lstrip("0")
    if source_cik and source_cik != clean_cik:
        result["unavailable"].append(
            {
                "kind": "all",
                "tag": None,
                "reason": f"supplement CIK {source_cik} does not match {clean_cik}",
            }
        )
        return result
    result["taxonomy"] = "us-gaap"
    _us_gaap = ((facts or {}).get("facts") or {}).get("us-gaap") or {}
    for kind, spec in tags.items():
        matched = False
        for tag in spec["tags"]:
            block = _us_gaap.get(tag)
            if not isinstance(block, dict):
                result["unavailable"].append(
                    {"kind": kind, "tag": tag, "reason": "tag absent from published supplement"}
                )
                continue
            payload = {
                "taxonomy": "us-gaap",
                "cik": result["cik"],
                "units": {USD_UNIT: ((block.get("units") or {}).get(USD_UNIT) or [])},
            }
            invalid = _validate_payload(payload, result["cik"], tag)
            if invalid:
                result["unavailable"].append({"kind": kind, "tag": tag, "reason": invalid})
                continue
            selected = _select_period_facts(
                payload, tag, wants, as_of, result["future_restatements"], result["conflicts"]
            )
            if selected:
                matched = True
                result["facts"][kind].extend(selected[end] for end in wants if end in selected)
            if matched:
                break
            result["unavailable"].append(
                {
                    "kind": kind,
                    "tag": tag,
                    "reason": "no validated annual 10-K fact for the loaded periods",
                }
            )
    for tag in EBIT_TAGS:
        block = _us_gaap.get(tag)
        if not isinstance(block, dict):
            result["unavailable"].append(
                {"kind": "ebit", "tag": tag, "reason": "tag absent from published supplement"}
            )
            continue
        payload = {
            "taxonomy": "us-gaap",
            "cik": result["cik"],
            "units": {USD_UNIT: ((block.get("units") or {}).get(USD_UNIT) or [])},
        }
        invalid = _validate_payload(payload, result["cik"], tag)
        if invalid:
            result["unavailable"].append({"kind": "ebit", "tag": tag, "reason": invalid})
            continue
        selected = _select_period_facts(
            payload, tag, wants, as_of, result["future_restatements"], result["conflicts"]
        )
        result["ebit_facts"] = [selected[end] for end in wants if end in selected]
        break
    return result


def _nearest_key(end, keys):
    """Exact period end, else the nearest candidate within 7 days, else None.

    Provider snapshots normalize fiscal dates to month ends while filings keep
    the true fiscal year end; the ≤7-day span is a fiscal-date normalization,
    not a period substitution. Anything farther apart does not match.
    """
    if end in keys:
        return end
    target = _as_date(end)
    if target is None:
        return None
    nearest, best = None, 8
    for candidate in keys:
        date = _as_date(candidate)
        if date is None:
            continue
        gap = abs((date - target).days)
        if gap < best:
            nearest, best = candidate, gap
    return nearest


def _fact_totals(adjustments):
    totals, evidence = {}, {}
    for kind, items in ((adjustments or {}).get("facts") or {}).items():
        for fact in items or []:
            amount, end = fact.get("amount"), fact.get("period_end")
            if amount is None or end is None:
                continue
            totals[end] = totals.get(end, 0) + amount
            evidence.setdefault(end, []).append(
                {
                    "kind": kind,
                    "amount": amount,
                    "tag": fact.get("tag"),
                    "accession": fact.get("accession"),
                    "form": fact.get("form"),
                    "filed": fact.get("filed"),
                }
            )
    return totals, evidence


def _ebit_definition(doc, adjustments):
    """Does the snapshot's EBIT include the disclosed charges? With evidence.

    Compares each period's EBIT with SEC ``OperatingIncomeLoss``. Equality means
    GAAP operating income (charge included). EBIT equal to GAAP operating income
    plus that period's charges means the provider already excludes them. Anything
    else is unverified and normalization stays blocked.
    """
    ebit_facts = {
        f["period_end"]: f for f in ((adjustments or {}).get("ebit_facts") or [])
    }
    if not ebit_facts:
        return {
            "classification": "unverified",
            "reason": (
                "No validated SEC OperatingIncomeLoss evidence rides with this "
                "snapshot; whether reported EBIT includes the disclosed charges "
                "is unverified."
            ),
            "periods": [],
        }
    totals, evidence = _fact_totals(adjustments)
    periods = []
    verdicts = set()
    def match(end):
        """Exact fiscal end, else the nearest filed end within 7 days.

        Provider snapshots normalize fiscal dates to month ends; the SEC fact
        keeps the true fiscal year end. The nearest-date match is recorded on
        the period so the tie-out stays auditable.
        """
        fact = ebit_facts.get(end)
        if fact is not None:
            return fact, "exact_period_end"
        target = _as_date(end)
        if target is None:
            return None, None
        nearest, best = None, 8
        for other, candidate in ebit_facts.items():
            other_date = _as_date(other)
            if other_date is None:
                continue
            gap = abs((other_date - target).days)
            if gap < best:
                nearest, best = candidate, gap
        if nearest is not None:
            return nearest, "nearest_fiscal_end"
        return None, None

    for row in (doc or {}).get("historical") or []:
        end, ebit = row.get("period_end"), row.get("ebit")
        fact, matched_by = match(end)
        if fact is None or ebit is None:
            periods.append({"period_end": end, "verdict": "unavailable"})
            verdicts.add("unavailable")
            continue
        gaap = fact.get("amount")
        sec_end = fact.get("period_end")
        # Compatible filing contexts only: the EBIT fact and every adjustment
        # fact for the tied period must come from the same filing accession.
        # A charge from another filing never explains this EBIT definition.
        charge_items = evidence.get(sec_end, []) or evidence.get(end, []) or []
        charge_accessions = {e.get("accession") for e in charge_items if e.get("accession")}
        context_compatible = not charge_items or (
            bool(fact.get("accession")) and charge_accessions == {fact.get("accession")}
        )
        charge = sum((e.get("amount") or 0) for e in charge_items)
        if gaap is None:
            verdict = "unavailable"
        elif charge_items and not context_compatible:
            verdict = "unverified"
        elif abs(ebit - gaap) < 1.0:
            verdict = "includes_charges"  # GAAP operating income
        elif charge and abs(ebit - (gaap + charge)) < 1.0:
            verdict = "excludes_charges"  # pre-impairment provider measure
        else:
            verdict = "unverified"
        periods.append(
            {
                "period_end": end,
                "sec_period_end": fact.get("period_end"),
                "matched_by": matched_by,
                "reported_ebit": ebit,
                "sec_operating_income": gaap,
                "adjustment_total": charge,
                "verdict": verdict,
                "filing_context_compatible": context_compatible,
                "adjustment_accessions": sorted(charge_accessions),
                "tag": fact.get("tag"),
                "accession": fact.get("accession"),
                "form": fact.get("form"),
                "filed": fact.get("filed"),
            }
        )
        verdicts.add(verdict)
    if verdicts == {"includes_charges"}:
        classification = "gaap_operating_income_verified"
    elif verdicts == {"excludes_charges"}:
        classification = "charges_already_excluded_verified"
    elif verdicts == {"unavailable"}:
        classification = "unverified"
    else:
        classification = "mixed_or_unverified"
    return {
        "classification": classification,
        "reason": {
            "gaap_operating_income_verified": (
                "Reported EBIT equals SEC OperatingIncomeLoss for every loaded "
                "period: the disclosed charges are inside the reported EBIT."
            ),
            "charges_already_excluded_verified": (
                "Reported EBIT equals SEC OperatingIncomeLoss plus the disclosed "
                "charges: this EBIT definition already excludes them, so an "
                "add-back would double count."
            ),
            "unverified": (
                "Reported EBIT could not be tied to SEC OperatingIncomeLoss; "
                "normalization is blocked rather than assumed."
            ),
            "mixed_or_unverified": (
                "Some periods could not be tied to SEC OperatingIncomeLoss; "
                "normalization is blocked rather than assumed."
            ),
        }[classification],
        "periods": periods,
    }


def audit_adjustments(doc, adjustments):
    """Per-period add-back verdicts, with the evidence behind each one."""
    totals, evidence = _fact_totals(adjustments)
    definition = _ebit_definition(doc, adjustments)
    known = set(totals)
    overlap_pairs = [
        (a, b)
        for a, spec in ADJUSTMENT_TAGS.items()
        for b in spec.get("overlaps", ())
    ]
    periods = []
    for row in (doc or {}).get("historical") or []:
        end = row.get("period_end")
        key = _nearest_key(end, known) if known else None
        matched = key is not None
        amount = (totals.get(key, 0) or 0) if matched else 0
        kinds = {e["kind"] for e in evidence.get(key, [])} if matched else set()
        verdict, reason = "unavailable", "no validated charge for this period"
        if amount:
            if any({a, b} <= kinds for a, b in overlap_pairs):
                verdict = "overlap_rejected"
                reason = (
                    "Two matched concepts could describe the same charge; the "
                    "period is excluded rather than double counted."
                )
            elif definition["classification"] == "gaap_operating_income_verified":
                verdict = "verified_addback"
                reason = "charge is inside the reported GAAP operating income"
            elif definition["classification"] == "charges_already_excluded_verified":
                verdict = "rejected_already_excluded"
                reason = (
                    "the reported EBIT definition already excludes this charge; "
                    "adding it back would double count"
                )
            else:
                verdict = "rejected_unverified"
                reason = "inclusion of the charge in reported EBIT is unverified"
        periods.append(
            {
                "period_end": end,
                "matched_period_end": key,
                "amount": amount,
                "verdict": verdict,
                "reason": reason,
                "evidence": evidence.get(key, []) if matched else [],
                "reported_ebit": row.get("ebit"),
            }
        )
    return {
        "ebit_definition": definition,
        "periods": periods,
        "addback_total": sum(p["amount"] for p in periods if p["verdict"] == "verified_addback"),
        "rejected_total": sum(
            p["amount"]
            for p in periods
            if p["verdict"].startswith("rejected") or p["verdict"] == "overlap_rejected"
        ),
    }


def classify_basis(doc, adjustments=None):
    """Label the accounting basis the snapshot's EBIT actually uses."""
    source = (doc or {}).get("source") or {}
    statement_source = source.get("statement_source")
    if source.get("accounting_policy") == "normalize":
        return {
            "label": BASIS_NORMALIZED,
            "reason": "Snapshot EBIT was adjusted by the normalization policy.",
            "evidence": {"policy": "normalize"},
        }
    if statement_source == "SEC-first":
        historical = (doc or {}).get("historical") or []
        reported = [
            ((row.get("provenance") or {}).get("ebit") or {}) for row in historical
        ]
        statuses = {p.get("quality_status") for p in reported}
        accessions = {p.get("accession") for p in reported if p.get("accession")}
        per_period = [
            (p.get("quality_status"), p.get("accession"), p.get("period_start"))
            for p in reported
        ]
        complete = (
            bool(reported)
            and all(status == "REPORTED" for status, _, _ in per_period)
            and all(bool(accn) for _, accn, _ in per_period)
            and all(bool(start) for _, _, start in per_period)
        )
        if complete:
            return {
                "label": BASIS_VERIFIED_GAAP,
                "reason": (
                    "EBIT comes from filed SEC statements with REPORTED quality "
                    "status and an accession receipt for every loaded period."
                ),
                "evidence": {"accessions": sorted(accessions), "quality_status": "REPORTED"},
            }
        return {
            "label": BASIS_UNVERIFIED,
            "reason": (
                "SEC-first statements are present but lack complete per-period "
                "REPORTED quality status, accession receipts or period starts."
            ),
            "evidence": {"quality_status": sorted(s for s in statuses if s)},
        }
    if statement_source == "Yahoo":
        return {
            "label": BASIS_PROVIDER,
            "reason": (
                "EBIT and D&A are provider-defined measures; comparability with "
                "filed GAAP definitions is unverified for this issuer."
            ),
            "evidence": {"statement_source": "Yahoo"},
        }
    return {
        "label": BASIS_UNVERIFIED,
        "reason": "Statement source is unrecorded or unrecognized.",
        "evidence": {"statement_source": statement_source},
    }


def comparability_note(doc):
    """Comparability statement: verified only with an attached reconciliation."""
    source = (doc or {}).get("source") or {}
    reconciliation = source.get("definition_reconciliation")
    if isinstance(reconciliation, dict) and reconciliation.get("verified"):
        return {
            "status": "verified_definition_difference",
            "text": (
                "A source-specific reconciliation demonstrates that this "
                "snapshot and its filed GAAP counterpart use different "
                "operating-income/D&A definitions: "
                + str(reconciliation.get("summary", ""))[:300]
            ),
            "evidence": reconciliation.get("evidence"),
        }
    return {
        "status": "unverified",
        "text": (
            "Comparability of this snapshot's operating-income and D&A "
            "definitions against filed GAAP is unverified: no source-specific "
            "reconciliation is attached for this issuer."
        ),
        "evidence": None,
    }


def apply_policy(doc, adjustments, policy="as_reported"):
    """Derive the forecast-ready series for ``policy``; ``doc`` is untouched.

    ``normalize`` succeeds only when every loaded period carrying a charge is
    a ``verified_addback``. Any overlap rejection or partial/unverified charge
    blocks the whole normalized series (no partial-period normalization).
    Returns ``(series_or_None, ledger)``; unknown policies raise ValueError.
    """
    if policy not in POLICIES:
        raise ValueError(f"Accounting policy must be one of {POLICIES}.")
    audit = audit_adjustments(doc, adjustments)
    historical = (doc or {}).get("historical") or []
    reported_margins = [
        (row.get("ebit") / row.get("revenue") if row.get("revenue") else None)
        for row in historical
    ]
    applied = [p for p in audit["periods"] if p["verdict"] == "verified_addback"]
    impaired_periods = sum(1 for p in audit["periods"] if p["amount"])
    charged = [p for p in audit["periods"] if p["amount"]]
    has_overlap = any(p["verdict"] == "overlap_rejected" for p in charged)
    has_non_verified = any(p["verdict"] != "verified_addback" for p in charged)
    if policy == "normalize" and charged and (has_overlap or has_non_verified):
        blocked_status = "conflicted_evidence" if has_overlap else "partial_or_unverified_evidence"
        blocked_reason = (
            "overlapping impairment concepts could double count; no normalized series"
            if has_overlap
            else "only a subset of charged periods verifies; a partial add-back would misstate the trend"
        )
        ledger = {
            "policy": policy,
            "reported_ebit_margins": reported_margins,
            "adjustments": [],
            "period_audit": audit["periods"],
            "ebit_definition": audit["ebit_definition"],
            "periods_with_impairment": impaired_periods,
            "period_count": len(historical),
            "applied_total": 0,
            "rejected_total": audit["rejected_total"],
            "recurrence_note": (
                f"Separately-disclosed impairments appear in {impaired_periods} of "
                f"{len(historical)} loaded periods. Normalizing assumes the charges "
                "do not recur"
                + (
                    "; with charges in every loaded period that assumption is "
                    "aggressive and the normalized value is a scenario, not a "
                    "better valuation."
                    if impaired_periods == len(historical) and impaired_periods
                    else "."
                )
            )
            if impaired_periods
            else "No separately-disclosed impairments in the loaded periods.",
            "adjusted_ebit_margins": None,
            "forecast_basis": "reported_gaap",
            "adjustment_status": blocked_status,
            "blocked_reason": blocked_reason,
        }
        return None, ledger
    ledger = {
        "policy": policy,
        "reported_ebit_margins": reported_margins,
        "adjustments": [],
        "period_audit": audit["periods"],
        "ebit_definition": audit["ebit_definition"],
        "periods_with_impairment": impaired_periods,
        "period_count": len(historical),
        "applied_total": audit["addback_total"],
        "rejected_total": audit["rejected_total"],
        "recurrence_note": (
            f"Separately-disclosed impairments appear in {impaired_periods} of "
            f"{len(historical)} loaded periods. Normalizing assumes the charges "
            "do not recur"
            + (
                "; with charges in every loaded period that assumption is "
                "aggressive and the normalized value is a scenario, not a "
                "better valuation."
                if impaired_periods == len(historical) and impaired_periods
                else "."
            )
        )
        if impaired_periods
        else "No separately-disclosed impairments in the loaded periods.",
    }
    for period in applied:
        ledger["adjustments"].append(
            {
                "period_end": period["period_end"],
                "kind": "impairment_addback",
                "amount": period["amount"],
                "reported_ebit": period["reported_ebit"],
                "adjusted_ebit": (
                    period["reported_ebit"] + period["amount"]
                    if period["reported_ebit"] is not None
                    else None
                ),
                "evidence": period["evidence"],
            }
        )
    if policy == "as_reported" or not ledger["adjustments"]:
        ledger["adjusted_ebit_margins"] = None
        ledger["forecast_basis"] = "reported_gaap"
        ledger["adjustment_status"] = (
            "not_requested"
            if policy == "as_reported"
            else "no_verifiable_adjustments"
        )
        return None, ledger
    adjusted = deepcopy(doc)
    for row in adjusted.get("historical", []):
        entry = next(
            (a for a in ledger["adjustments"] if a["period_end"] == row.get("period_end")),
            None,
        )
        if entry and row.get("ebit") is not None:
            row["ebit"] = entry["adjusted_ebit"]
    adjusted["source"]["accounting_policy"] = "normalize"
    ledger["adjusted_ebit_margins"] = [
        (row.get("ebit") / row.get("revenue") if row.get("revenue") else None)
        for row in adjusted.get("historical", [])
    ]
    ledger["forecast_basis"] = "normalized_operating"
    ledger["adjustment_status"] = "applied"
    ledger["tax_note"] = (
        "The forecast applies the period tax rate to adjusted EBIT; the tax "
        "shield on the add-back itself is not separately modeled."
    )
    return adjusted, ledger


def rou_treatment(doc, rou_amount=None):
    """Why operating-lease ROU amortization is excluded from the D&A add-back."""
    bridge = (doc or {}).get("bridge") or {}
    lease_keys = [k for k in bridge if "lease" in str(k).lower()]
    if rou_amount is not None and lease_keys:
        return {
            "status": "review_required",
            "reason": (
                "Bridge carries lease-related items; verify interest/principal "
                "treatment before any ROU add-back."
            ),
            "observed_rou_amortization": rou_amount,
        }
    return {
        "status": "excluded",
        "reason": (
            "Operating-lease ROU amortization is not added back: the "
            "enterprise-to-equity bridge carries no lease liabilities, and "
            "operating lease cost already sits inside EBIT. Adding it back "
            "without the matching liability would overstate equity value."
        ),
        "observed_rou_amortization": rou_amount,
    }
