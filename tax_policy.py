"""Historical-versus-forecast tax policy: reported rates, forecast assumptions, shields.

Three concepts are never conflated here:

- **Reported historical effective tax rate**: tax expense (or benefit) divided
  by reported pretax income for a filed period. The signed filing value is
  preserved with provenance -- negative rates from benefits, settlements or
  credits are genuine accounting outcomes, never clamped or zeroed.
- **Forecast operating cash tax rate**: an explicit 0-1 assumption used to
  project taxes on EBIT/FCFF. The latest reported rate is reused only when it
  lies in 0-1; otherwise an explicit user override or a filing-supported
  normalized scenario is required, and the baseline run refuses loudly.
- **Marginal interest tax-shield rate**: the supported rate applied to the
  after-tax cost of debt. It defaults to the resolved forecast rate and may
  be overridden explicitly (e.g. deductibility limits); it is validated 0-1
  and labeled in both cases.

No ticker names or numeric rate constants live here. A normalized scenario
recommends nothing by itself: it carries its filing, period, reconciliation
components and recurring/discrete flags so callers can audit it.
"""

FORECAST_BASIS_LATEST_REPORTED = "latest_reported"
FORECAST_BASIS_USER_OVERRIDE = "user_override"
FORECAST_BASIS_NORMALIZED_SCENARIO = "normalized_scenario"

RECONCILIATION_TOLERANCE_PP = 0.15


class TaxPolicyError(ValueError):
    """Raised when no supportable forecast tax assumption exists."""


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value == value and abs(value) != float("inf")


def reported_history(rates):
    """Echo signed historical rates after a finiteness check.

    Preservation only: a negative or above-one rate is returned as filed.
    Raises TaxPolicyError on missing/non-finite input.
    """
    checked = []
    for rate in rates or []:
        if not _finite(rate):
            raise TaxPolicyError("Reported historical tax rate must be a finite number.")
        checked.append(float(rate))
    if not checked:
        raise TaxPolicyError("No reported historical tax rates available.")
    return checked


def resolve_forecast_tax(history, user_override=None, scenario=None):
    """Resolve the 5-year forecast operating tax assumption.

    Precedence: explicit user override (validated 0-1) > filing-supported
    normalized scenario > latest reported rate when it lies in 0-1.
    A latest reported rate outside 0-1 with no override or scenario raises
    TaxPolicyError naming the requirement instead of silently substituting a
    statutory rate. Returns {"rates", "basis", "evidence"}.
    """
    history = reported_history(history)
    if user_override is not None:
        override = list(user_override)
        if len(override) != 5 or any(not _finite(v) or not 0 <= v <= 1 for v in override):
            raise TaxPolicyError("User forecast tax override must be five rates in 0-1.")
        return {
            "rates": [float(v) for v in override],
            "basis": FORECAST_BASIS_USER_OVERRIDE,
            "evidence": {"note": "explicit user assumption; review suitability"},
        }
    if scenario is not None:
        rates = list(scenario.get("rates") or [])
        if len(rates) != 5 or any(not _finite(v) or not 0 <= v <= 1 for v in rates):
            raise TaxPolicyError("Normalized scenario must carry five rates in 0-1.")
        evidence = dict(scenario.get("evidence") or {})
        if not evidence.get("filing") or not evidence.get("period_end"):
            raise TaxPolicyError("Normalized scenario must cite its filing and period.")
        return {
            "rates": [float(v) for v in rates],
            "basis": FORECAST_BASIS_NORMALIZED_SCENARIO,
            "evidence": evidence,
        }
    latest = history[-1]
    if 0 <= latest <= 1:
        return {
            "rates": [latest] * 5,
            "basis": FORECAST_BASIS_LATEST_REPORTED,
            "evidence": {"note": "latest reported rate reused as forecast assumption"},
        }
    raise TaxPolicyError(
        f"Latest reported tax rate {latest:.2%} is outside 0-1; an explicit "
        "user override or filing-supported normalized scenario is required."
    )


def shield_rate(policy, override=None):
    """Resolve the marginal interest tax-shield rate for the cost of debt.

    Defaults to the resolved forecast operating rate (first year) so FCFF
    and WACC stay coherent; an explicit override must be 0-1 and is labeled.
    """
    if override is not None:
        if not _finite(override) or not 0 <= override <= 1:
            raise TaxPolicyError("Shield override must be a rate in 0-1.")
        return {"rate": float(override), "basis": "explicit_shield_override"}
    rate = (policy.get("rates") or [None])[0]
    if rate is None or not 0 <= rate <= 1:
        raise TaxPolicyError("No supportable shield rate: resolve a forecast policy first.")
    return {"rate": float(rate), "basis": f"coherent_with_forecast:{policy.get('basis')}"}


def document_tax_policy(rows, user_override=None, scenario=None):
    """Record the reported-vs-forecast tax position on a loaded document.

    ``rows`` are historical records with ``period_end``, ``tax_rate`` and
    optional ``provenance.tax_rate.accession`` (plus Yahoo's
    ``reported_tax_rate`` filed ratio when the effective rate fell back to
    a provider convention). History is reported as filed -- signed, never
    substituted; the forecast selection resolves the latest default or an
    explicit policy. Raises TaxPolicyError on an invalid explicit
    selection instead of inventing history.
    """
    reported = []
    for row in rows or []:
        prov = ((row.get("provenance") or {}).get("tax_rate") or {}) or {}
        entry = {
            "period_end": row.get("period_end"),
            "rate": row.get("tax_rate"),
            "accession": prov.get("accession"),
        }
        if row.get("reported_tax_rate") is not None:
            entry["filed_ratio"] = row.get("reported_tax_rate")
        reported.append(entry)
    resolved = resolve_forecast_tax(
        [entry["rate"] for entry in reported],
        user_override=user_override,
        scenario=scenario,
    )
    evidence = dict(resolved["evidence"])
    # A scenario citation is only as strong as its match to loaded packet
    # provenance. An arbitrary client-supplied filing string must never
    # receive a verified-normalization label: without a matching accession
    # it stays an explicitly unverified citation (a user assumption).
    if scenario is not None:
        cited = evidence.get("accession")
        loaded = {entry.get("accession") for entry in reported}
        evidence["verification"] = (
            "packet_accession_matched"
            if cited is not None and cited in loaded
            else "unverified_citation"
        )
    elif user_override is not None:
        evidence["verification"] = "user_assumption"
    else:
        evidence["verification"] = "not_applicable_default"
    return {
        "reported": reported,
        "selected": {
            "basis": resolved["basis"],
            "rates": resolved["rates"],
            "evidence": evidence,
        },
        "explicit": user_override is not None or scenario is not None,
    }


def build_tax_reconciliation(statutory_rate, components, reported_rate, filing, period_end):
    """Check a filed effective-tax-rate reconciliation and split it.

    components: [{label, effect_pp, recurring (bool), note}]. The statutory
    rate plus summed effects must land within RECONCILIATION_TOLERANCE_PP of
    the reported rate or the reconciliation is rejected (never fudged).
    Returns the checked bridge plus the recurring-only normalized rate, which
    callers may adopt as a scenario -- adoption stays explicit, never automatic.
    """
    if not _finite(statutory_rate) or not _finite(reported_rate):
        raise TaxPolicyError("Reconciliation needs finite statutory and reported rates.")
    checked = []
    for component in components or []:
        effect = component.get("effect_pp")
        if not _finite(effect) or not component.get("label"):
            raise TaxPolicyError("Each reconciliation component needs a label and pp effect.")
        checked.append(
            {
                "label": component["label"],
                "effect_pp": float(effect),
                "recurring": bool(component.get("recurring")),
                "note": component.get("note", ""),
            }
        )
    if not checked:
        raise TaxPolicyError("Empty tax reconciliation explains nothing.")
    bridged = statutory_rate * 100 + sum(c["effect_pp"] for c in checked)
    if abs(bridged - reported_rate * 100) > RECONCILIATION_TOLERANCE_PP:
        raise TaxPolicyError(
            f"Reconciliation bridges to {bridged:.2f}pp, not the reported {reported_rate * 100:.2f}pp."
        )
    normalized = (statutory_rate * 100 + sum(c["effect_pp"] for c in checked if c["recurring"])) / 100
    return {
        "filing": filing,
        "period_end": period_end,
        "statutory_rate": float(statutory_rate),
        "reported_rate": float(reported_rate),
        "components": checked,
        "recurring_only_rate": normalized,
        "discrete_pp": sum(c["effect_pp"] for c in checked if not c["recurring"]),
    }
