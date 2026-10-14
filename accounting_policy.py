"""Source-independent financial normalization between observations and forecasts.

Reported observations are immutable: this layer never rewrites them. It
attaches separately-disclosed, source-backed adjustment facts (intangible and
goodwill impairments from SEC companyfacts) and derives an *adjusted* series
only under an explicit ``normalize`` policy. The default ``as_reported`` policy
changes nothing.

Two hard rules, both enforced here rather than trusted to callers:

1. Impairment normalization never assumes non-recurrence. The ledger always
   reports how many of the loaded periods carry impairments, and normalizing
   across consecutive impairment years is flagged, not hidden.
2. Operating-lease ROU amortization is never added back to free cash flow by
   this layer: the enterprise-to-equity bridge carries no lease liabilities,
   so the add-back would lack its matching balance-sheet treatment. Yahoo D&A,
   which folds ROU amortization in, is therefore labeled definitionally
   incomparable with GAAP operating-profit-based measures, not corrected.

No ticker names, CUSIPs or numeric constants live here: kinds map to XBRL tag
tuples, and every amount arrives with its tag, accession, period and filer.
Missing or ambiguous facts are reported unavailable, never zero.
"""

from copy import deepcopy

# Kind -> XBRL tags that may carry the separately-disclosed charge, in
# preference order. Amounts are expected as positive charges.
ADJUSTMENT_TAGS = {
    "intangible_impairment": ("ImpairmentOfIntangibleAssetsExcludingGoodwill",),
    "goodwill_impairment": ("GoodwillImpairmentLoss",),
}

POLICIES = ("as_reported", "normalize")

_COMPANYFACTS = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json"


def _headers():
    try:
        from dcf_loader import provider_setting

        identity = provider_setting("EDGAR_IDENTITY")
    except Exception:
        identity = ""
    if "@" not in str(identity):
        identity = "DCF-Valuation-Engine/1.0"
    return {"User-Agent": str(identity), "Accept": "application/json"}


def fetch_adjustment_facts(cik, period_ends, http, tags=None):
    """Load impairment facts for the doc's periods from SEC companyfacts.

    Returns ``{"facts": {kind: [fact, ...]}, "unavailable": [{kind, tag,
    reason}, ...]}`` where each fact carries period_end, amount, tag,
    accession, filed and unit. A missing tag (HTTP 404), a fetch failure, or
    no 10-K fact for a period yields an ``unavailable`` entry: absence is
    never silently treated as zero.
    """
    from dcf_loader import ProviderError

    tags = tags or ADJUSTMENT_TAGS
    wants = [p for p in (period_ends or []) if p]
    facts = {kind: [] for kind in tags}
    unavailable = []
    if not str(cik or "").isdigit():
        return {
            "facts": facts,
            "unavailable": [
                {"kind": kind, "tag": names[0], "reason": "CIK unavailable"}
                for kind, names in tags.items()
            ],
        }
    for kind, names in tags.items():
        matched = False
        for tag in names:
            try:
                payload = http.get(
                    _COMPANYFACTS.format(cik=str(cik).zfill(10), tag=tag),
                    headers=_headers(),
                    ttl=86400,
                    cache_key=f"sec-adjust-{str(cik).zfill(10)}-{tag}",
                )
            except ProviderError as exc:
                unavailable.append({"kind": kind, "tag": tag, "reason": str(exc)[:160]})
                continue
            except Exception as exc:  # best-effort context; never breaks a load
                unavailable.append(
                    {"kind": kind, "tag": tag, "reason": f"lookup failed: {exc}"[:160]}
                )
                continue
            if not isinstance(payload, dict):
                unavailable.append(
                    {"kind": kind, "tag": tag, "reason": "non-JSON tag response"}
                )
                continue
            units = payload.get("units") or {}
            by_end = {}
            for unit, values in units.items():
                if not isinstance(values, list):
                    continue
                for fact in values:
                    if not isinstance(fact, dict) or fact.get("form") != "10-K":
                        continue
                    end = fact.get("end")
                    if end not in wants or fact.get("val") is None:
                        continue
                    prior = by_end.get(end)
                    # Prefer the filer's latest restatement of each period.
                    if prior is None or str(fact.get("filed", "")) >= str(
                        prior.get("filed", "")
                    ):
                        by_end[end] = {
                            "period_end": end,
                            "amount": fact["val"],
                            "tag": tag,
                            "unit": unit,
                            "accession": fact.get("accn"),
                            "filed": fact.get("filed"),
                            "fiscal_year": fact.get("fy"),
                        }
            if by_end:
                matched = True
                facts[kind].extend(by_end[end] for end in wants if end in by_end)
            if matched:
                break
            unavailable.append(
                {"kind": kind, "tag": tag, "reason": "no 10-K fact for loaded periods"}
            )
    return {"facts": facts, "unavailable": unavailable}


def _impairment_by_end(adjustments):
    totals = {}
    evidence = {}
    for kind, items in ((adjustments or {}).get("facts") or {}).items():
        for fact in items or []:
            amount = fact.get("amount")
            if amount is None:
                continue
            end = fact.get("period_end")
            totals[end] = totals.get(end, 0) + amount
            evidence.setdefault(end, []).append(
                {
                    "kind": kind,
                    "amount": amount,
                    "tag": fact.get("tag"),
                    "accession": fact.get("accession"),
                    "filed": fact.get("filed"),
                }
            )
    return totals, evidence


def apply_policy(doc, adjustments, policy="as_reported"):
    """Derive the forecast-ready series for ``policy`` without touching ``doc``.

    Returns ``(series_or_None, ledger)``. ``as_reported`` returns no adjusted
    series (the loaded GAAP observations stand) plus a ledger describing what
    a normalization *would* adjust. ``normalize`` adds back matched impairment
    charges to EBIT per period, with per-period evidence and a recurrence
    flag. Unknown policies raise ValueError.
    """
    if policy not in POLICIES:
        raise ValueError(f"Accounting policy must be one of {POLICIES}.")
    historical = (doc or {}).get("historical") or []
    totals, evidence = _impairment_by_end(adjustments)
    reported_margins = [
        (row.get("ebit") / row.get("revenue") if row.get("revenue") else None)
        for row in historical
    ]
    impaired_periods = sum(
        1
        for row in historical
        if totals.get(row.get("period_end"), 0) not in (0, None)
        and totals.get(row.get("period_end"))
    )
    ledger = {
        "policy": policy,
        "reported_ebit_margins": reported_margins,
        "adjustments": [],
        "periods_with_impairment": impaired_periods,
        "period_count": len(historical),
        "recurrence_note": (
            f"Separately-disclosed impairments appear in {impaired_periods} of "
            f"{len(historical)} loaded periods; normalizing assumes they do not "
            "recur, which consecutive-year impairments contradict. Review the "
            "filing Notes before relying on a normalized basis."
            if impaired_periods
            else "No separately-disclosed impairments in the loaded periods."
        ),
    }
    for row in historical:
        end = row.get("period_end")
        amount = totals.get(end, 0) or 0
        if amount:
            ledger["adjustments"].append(
                {
                    "period_end": end,
                    "kind": "impairment_addback",
                    "amount": amount,
                    "reported_ebit": row.get("ebit"),
                    "adjusted_ebit": (
                        row.get("ebit") + amount if row.get("ebit") is not None else None
                    ),
                    "evidence": evidence.get(end, []),
                }
            )
    if policy == "as_reported" or not ledger["adjustments"]:
        ledger["adjusted_ebit_margins"] = None
        ledger["forecast_basis"] = "reported_gaap"
        return None, ledger
    adjusted = deepcopy(doc)
    for row in adjusted.get("historical", []):
        entry = next(
            (a for a in ledger["adjustments"] if a["period_end"] == row.get("period_end")),
            None,
        )
        if entry and row.get("ebit") is not None:
            row["ebit"] = entry["adjusted_ebit"]
    ledger["adjusted_ebit_margins"] = [
        (row.get("ebit") / row.get("revenue") if row.get("revenue") else None)
        for row in adjusted.get("historical", [])
    ]
    ledger["forecast_basis"] = "normalized_operating"
    ledger["tax_note"] = (
        "The forecast applies the period tax rate to adjusted EBIT; the tax "
        "shield on the add-back itself is not separately modeled."
    )
    return adjusted, ledger


def rou_treatment(doc, rou_amount=None):
    """Why operating-lease ROU amortization is excluded from the D&A add-back.

    Always returns a blocking disclosure unless the bridge explicitly carries
    lease liabilities with matching interest treatment, which the current
    bridge schema does not. ``rou_amount`` (when observed, e.g. Yahoo D&A
    minus cash-flow D&A) is reported for labeling, never added back.
    """
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


def provider_convention_notes(doc):
    """Label definitionally incomparable provider conventions on Yahoo docs."""
    source = (doc or {}).get("source") or {}
    if source.get("statement_source") != "Yahoo":
        return []
    return [
        "Yahoo OperatingIncome may exclude separately-disclosed impairment "
        "charges that GAAP operating profit includes; Yahoo D&A may fold in "
        "operating-lease ROU amortization that cash-flow D&A excludes. These "
        "series are definitionally incomparable with GAAP-based measures: "
        "compare valuations only within one accounting basis."
    ]
