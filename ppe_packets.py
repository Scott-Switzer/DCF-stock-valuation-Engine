"""Public SEC-only compact packets built from immutable PPE releases."""

from copy import deepcopy
from datetime import date, datetime, timezone
import json
import math
from pathlib import Path
import re
from dcf_loader import HISTORY_FIELDS, BRIDGE_FIELDS, TAGS, DURATION, ProviderError, ticker_symbol

SCHEMA = "ppe-valuation-packet-v1"
CANONICAL = {
    "revenue": "revenue",
    "ebit": "operating_income",
    "net_income": "net_income",
    "book_value": "shareholders_equity",
    "cash": "cash",
    "total_debt": "total_debt",
}
SEC_TAGS = {
    **{k: list(v) for k, v in TAGS.items()},
    "book_value": ["StockholdersEquity"],
    "common_dividends": ["PaymentsOfDividendsCommonStock"],
    "interest_expense": ["InterestExpense", "InterestAndDebtExpense"],
}
SEC_TAGS["ebit"] = ["OperatingIncomeLoss", "EarningsBeforeInterestAndTaxes"]
SEC_TAGS["pretax_income"] = [
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxes",
]
SEC_TAGS["interest_expense"] = ["InterestExpense", "InterestAndDebtExpense", "InterestCostsIncurred"]
SEC_TAGS["short_term_borrowings"] = ["ShortTermBorrowings", "CommercialPaper"]
# Regulated-utility top line, lowest priority like dcf_loader.TAGS (which this
# module copied at import time before extending its own lists).
SEC_TAGS["revenue"] = [*SEC_TAGS["revenue"], "RegulatedAndUnregulatedOperatingRevenue"]
# Basic EPS numerator: income attributable to the parent after preferred dividends.
# Direct tag only. It is never derived from NetIncomeLoss less preferred dividends or
# noncontrolling interests: an absent tag is not zero, and that derivation needs
# reconciliation evidence this producer does not have.
SEC_TAGS["common_income"] = ["NetIncomeLossAvailableToCommonStockholdersBasic"]
DURATIONS = DURATION | {"common_dividends", "interest_expense", "common_income"}
# Statement items that can explain the residual between parent NetIncomeLoss and the direct
# common-income tag. They are matched within the same filing (accession) as the direct
# observation, so an observation from one filing is never explained by another filing's items.
COMMON_INCOME_COMPONENTS = {
    "preferred_dividends": ["PreferredStockDividendsIncomeStatementImpact"],
    "preferred_cash": ["DividendsPreferredStockCash"],
    "preferred_stock": ["DividendsPreferredStock"],
    "preferred_and_adjustments": ["PreferredStockDividendsAndOtherAdjustments"],
    "preferred_dividends_alt": ["PreferredStockDividends"],
    "preferred_redemption_premium": ["PreferredStockRedemptionPremium"],
    "participating_securities": ["ParticipatingSecuritiesDistributedAndUndistributedEarningsLossBasic"],
    "participating_securities_alt": ["ParticipatingSecuritiesDistributedAndUndistributedEarnings"],
    "nci_income": ["NetIncomeLossAttributableToNoncontrollingInterest"],
}
# Mutually exclusive economic categories: at most one tag per category may contribute to a
# multi-component EPS numerator bridge, preventing synonymous preferred or participating tags
# from being summed together.
COMMON_INCOME_CATEGORIES = (
    (
        "preferred_dividends",
        "preferred_cash",
        "preferred_stock",
        "preferred_and_adjustments",
        "preferred_dividends_alt",
    ),
    (
        "participating_securities",
        "participating_securities_alt",
    ),
    (
        "preferred_redemption_premium",
    ),
    (
        "nci_income",
    ),
)
COMMON_INCOME_TOLERANCE_USD = 1.0
# Reusable common-equity build-up variants for the preferred-equity and NCI
# derivations below. Ordered most-specific first: filers that disclose APIC in
# the generic AdditionalPaidInCapital tag (e.g. AEP, Paychex) or treasury stock
# in TreasuryStockCommonValue (e.g. EOG) follow the same filing identity as
# the classic leg set, and every leg must still come from one 10-K accession.
COMMON_HEAD_PAIRS = (
    ("CommonStockValue", "AdditionalPaidInCapitalCommonStock"),
    ("CommonStockValue", "AdditionalPaidInCapital"),
)
TREASURY_TAGS = ("TreasuryStockValue", "TreasuryStockCommonValue")
# Long-term-debt total/current tag pairs whose difference is the noncurrent
# portion. Ordered most-standard first; each pair must agree in one accession.
LTD_TOTAL_PAIRS = (
    ("LongTermDebt", "LongTermDebtCurrent"),
    (
        "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",
        "LongTermDebtAndCapitalLeaseObligationsCurrent",
    ),
    # Some filers (e.g. Honeywell, AbbVie) disclose the total in LongTermDebt
    # but the current portion only in the capital-lease-obligations branch.
    # Lowest priority: same total-less-current economics, one accession.
    ("LongTermDebt", "LongTermDebtAndCapitalLeaseObligationsCurrent"),
)


def _number(value):
    if isinstance(value, bool):
        raise ProviderError("Invalid packet number.")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ProviderError("Invalid packet number.") from None
    if not math.isfinite(value):
        raise ProviderError("Invalid packet number.")
    return value


def _annual(start, end):
    try:
        return 330 <= (date.fromisoformat(end) - date.fromisoformat(start)).days <= 400
    except (TypeError, ValueError):
        return False


def _field(value, end, available, unit, provenance):
    return {
        "value": _number(value),
        "period_end": end,
        "available_at": available,
        "unit": unit,
        "provenance": provenance,
    }


def _sec(facts, metric, end, cutoff, source):
    unit = "shares" if metric == "diluted_shares" else "USD"
    for tag in SEC_TAGS.get(metric, []):
        candidates = []
        for r in (
            facts.get("facts", {}).get("us-gaap", {}).get(tag, {}).get("units", {}).get(unit, [])
        ):
            if (
                r.get("end") != end
                or r.get("form") not in {"10-K", "10-K/A"}
                or r.get("filed", "9999") > cutoff
            ):
                continue
            if metric in DURATIONS and not _annual(r.get("start"), end):
                continue
            if metric not in DURATIONS and r.get("start"):
                continue
            candidates.append(r)
        if candidates:
            latest = max(r["filed"] for r in candidates)
            top = [r for r in candidates if r["filed"] == latest]
            if len({_number(r["val"]) for r in top}) != 1:
                raise ProviderError(f"Conflicting SEC {metric} facts for {end}.")
            r = top[0]
            return _field(
                r["val"],
                end,
                r["filed"],
                unit,
                {
                    **source,
                    "provider": "SEC companyfacts",
                    "tag": tag,
                    "accession": r.get("accn"),
                    "period_start": r.get("start"),
                    "filing_date": r["filed"],
                },
            )
    return None


def _filing_value(facts, tags, end, accession):
    """Annual USD value of the given tags reported in one specific 10-K accession."""
    values = set()
    for tag in tags:
        for r in facts.get("facts", {}).get("us-gaap", {}).get(tag, {}).get("units", {}).get("USD", []):
            if (
                r.get("end") == end
                and r.get("accn") == accession
                and r.get("form") in {"10-K", "10-K/A"}
                and _annual(r.get("start"), end)
            ):
                values.add(_number(r["val"]))
    if len(values) > 1:
        raise ProviderError(f"Conflicting SEC facts in filing {accession} for {end}.")
    return values.pop() if values else None


def explain_residual(parent, direct, components):
    """Explain parent net income less the direct common-income value.

    Explained only when the residual equals zero, one reported component, or an exact sum of
    components drawn from distinct economic categories (preferred dividends, participating
    securities, and preferred redemption premium). Synonymous tags within the same category are
    never summed together. Anything else is 'unexplained_residual' and is never forced into a
    match. Shared with scripts/reconcile_common_income.py.
    """
    if direct is None:
        return "no_direct_tag"
    if parent is None:
        return "no_parent_net_income"
    residual = parent - direct
    tol = COMMON_INCOME_TOLERANCE_USD
    if abs(residual) <= tol:
        return "match_parent_net_income"
    for name, value in components.items():
        if abs(residual - value) <= tol:
            return f"explained_by_{name}"
    active = [
        [name for name in group if name in components and abs(components[name]) > tol]
        for group in COMMON_INCOME_CATEGORIES
    ]
    for i in range(len(active)):
        for j in range(i + 1, len(active)):
            for first in active[i]:
                for second in active[j]:
                    if abs(residual - components[first] - components[second]) <= tol:
                        return f"explained_by_{first}_plus_{second}"
    for first in active[0]:
        for second in active[1]:
            for third in active[2]:
                if (
                    abs(residual - components[first] - components[second] - components[third])
                    <= tol
                ):
                    return f"explained_by_{first}_plus_{second}_plus_{third}"
    return "unexplained_residual"


def common_income_evidence(facts, end, direct):
    """Same-filing evidence for one direct common-income observation, with its verdict.

    Parent income and every component are read only from the direct observation's own 10-K
    accession. Shared by the packet gate and scripts/reconcile_common_income.py.
    """
    accession = direct["provenance"].get("accession")
    if not accession:
        return {"verdict": "no_accession", "accession": None, "parent": None, "components": {}}
    parent = _filing_value(facts, ["NetIncomeLoss"], end, accession)
    parent_tag = "NetIncomeLoss"
    if parent is None:
        # Some issuers (e.g. Caterpillar) report consolidated income as
        # ProfitLoss; the NCI component below then reconciles it to the
        # parent-attributable direct tag within the same filing.
        parent = _filing_value(facts, ["ProfitLoss"], end, accession)
        parent_tag = "ProfitLoss"
    components = {}
    for name, tags in COMMON_INCOME_COMPONENTS.items():
        value = _filing_value(facts, tags, end, accession)
        if value is not None:
            components[name] = value
    return {
        "verdict": explain_residual(parent, direct["value"], components),
        "accession": accession,
        "parent": parent,
        "parent_tag": parent_tag,
        "components": components,
    }


def common_income_bridge(facts, end, direct):
    """Verify a direct common-income observation against its own filing's parent income."""
    return common_income_evidence(facts, end, direct)["verdict"]


def bridge_accepted(verdict):
    return verdict == "match_parent_net_income" or str(verdict).startswith("explained_by_")


def _sec_subtotal_difference(facts, total_tag, part_tag, end, cutoff, source, formula):
    """Derive a bridge claim from two reported equity subtotals (Yahoo parity).

    Preferred equity is stockholders equity minus common equity; minority
    interest is total equity including noncontrolling interest minus
    stockholders equity. Both legs must come from the same 10-K accession and
    agree at the latest filing date; a negative difference is rejected and
    reported as missing, never as zero. Returns an SEC-provenance field or None.
    """
    legs = {}
    for tag in (total_tag, part_tag):
        candidates = [
            r
            for r in facts.get("facts", {})
            .get("us-gaap", {})
            .get(tag, {})
            .get("units", {})
            .get("USD", [])
            if r.get("end") == end
            and r.get("form") in {"10-K", "10-K/A"}
            and r.get("filed", "9999") <= cutoff
            and not r.get("start")
        ]
        if not candidates:
            return None
        latest = max(r["filed"] for r in candidates)
        top = [r for r in candidates if r["filed"] == latest]
        if len({_number(r["val"]) for r in top}) != 1:
            return None
        legs[tag] = top[0]
    if legs[total_tag].get("accn") != legs[part_tag].get("accn"):
        return None
    value = _number(legs[total_tag]["val"]) - _number(legs[part_tag]["val"])
    if value < -COMMON_INCOME_TOLERANCE_USD:
        return None
    return _field(
        max(value, 0.0),
        end,
        max(r["filed"] for r in legs.values()),
        "USD",
        {
            **source,
            "provider": "SEC companyfacts",
            "formula": formula,
            "total_tag": total_tag,
            "part_tag": part_tag,
            "accession": legs[total_tag].get("accn"),
            "filing_date": max(r["filed"] for r in legs.values()),
        },
    )


def _instant_leg(facts, tag, end, cutoff):
    """Latest-filed 10-K instant USD row for one tag, or None.

    Returns None when the tag is absent, has no row for the period, or carries
    contradictory values at the latest filing date. Shared by the bridge
    derivations so every leg follows the same selection discipline.
    """
    candidates = [
        r
        for r in facts.get("facts", {})
        .get("us-gaap", {})
        .get(tag, {})
        .get("units", {})
        .get("USD", [])
        if r.get("end") == end
        and r.get("form") in {"10-K", "10-K/A"}
        and r.get("filed", "9999") <= cutoff
        and not r.get("start")
    ]
    if not candidates:
        return None
    latest = max(r["filed"] for r in candidates)
    top = [r for r in candidates if r["filed"] == latest]
    if len({_number(r["val"]) for r in top}) != 1:
        return None
    return top[0]


def _sec_preferred_from_common_buildup(facts, end, cutoff, source):
    """Derive preferred equity from a full common-equity build-up (filing identity).

    Preferred equity is stockholders equity minus common equity, where common
    equity is par/common value plus additional paid-in capital plus retained
    earnings plus accumulated other comprehensive income minus treasury stock.
    Two reusable filing variants are accepted: the combined
    ``CommonStocksIncludingAdditionalPaidInCapital`` tag may stand in for the
    separate par-value and APIC legs, and stockholders equity may be derived
    as total equity including noncontrolling interest less filed NCI when the
    standalone stockholders-equity tag is absent. Every leg must come from the
    same 10-K accession; a negative residual beyond tolerance is rejected and
    reported as missing, never as zero. Returns an SEC-provenance field or
    None.
    """
    legs = {}
    used_tags = []
    se_row = _instant_leg(facts, "StockholdersEquity", end, cutoff)
    if se_row is not None:
        legs["StockholdersEquity"] = se_row
        used_tags.append("StockholdersEquity")
        se_value = _number(se_row["val"])
    else:
        total = _instant_leg(
            facts, "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", end, cutoff
        )
        nci = _instant_leg(facts, "MinorityInterest", end, cutoff)
        if total is None or nci is None:
            return None
        legs["StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"] = total
        legs["MinorityInterest"] = nci
        used_tags.extend(
            ["StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", "MinorityInterest"]
        )
        se_value = _number(total["val"]) - _number(nci["val"])
    pair = None
    for csv_tag, apic_tag in COMMON_HEAD_PAIRS:
        candidate = [_instant_leg(facts, tag, end, cutoff) for tag in (csv_tag, apic_tag)]
        if all(row is not None for row in candidate):
            pair = candidate
            legs[csv_tag], legs[apic_tag] = pair
            used_tags.extend([csv_tag, apic_tag])
            common_head = _number(pair[0]["val"]) + _number(pair[1]["val"])
            break
    if pair is None:
        combined = _instant_leg(facts, "CommonStocksIncludingAdditionalPaidInCapital", end, cutoff)
        if combined is None:
            return None
        legs["CommonStocksIncludingAdditionalPaidInCapital"] = combined
        used_tags.append("CommonStocksIncludingAdditionalPaidInCapital")
        common_head = _number(combined["val"])
    signs = {
        "RetainedEarningsAccumulatedDeficit": 1,
        "AccumulatedOtherComprehensiveIncomeLossNetOfTax": 1,
    }
    for tag in signs:
        row = _instant_leg(facts, tag, end, cutoff)
        if row is None:
            return None
        legs[tag] = row
        used_tags.append(tag)
    treasury_row = None
    for tag in TREASURY_TAGS:
        row = _instant_leg(facts, tag, end, cutoff)
        if row is not None:
            treasury_row = row
            legs[tag] = row
            used_tags.append(tag)
            break
    if treasury_row is None:
        return None
    accessions = {r.get("accn") for r in legs.values()}
    if len(accessions) != 1:
        return None
    common = (
        common_head
        + sum(signs[tag] * _number(legs[tag]["val"]) for tag in signs)
        - _number(treasury_row["val"])
    )
    value = se_value - common
    if value < -COMMON_INCOME_TOLERANCE_USD:
        return None
    classic = {
        "StockholdersEquity", "CommonStockValue", "AdditionalPaidInCapitalCommonStock",
        "RetainedEarningsAccumulatedDeficit", "AccumulatedOtherComprehensiveIncomeLossNetOfTax",
        "TreasuryStockValue",
    }
    formula = (
        "stockholders equity minus (common value + APIC + retained earnings + AOCI - treasury stock)"
        if set(used_tags) == classic
        else "stockholders equity minus built-up common equity (" + ", ".join(sorted(used_tags)) + ")"
    )
    return _field(
        max(value, 0.0),
        end,
        max(r["filed"] for r in legs.values()),
        "USD",
        {
            **source,
            "provider": "SEC companyfacts",
            "formula": formula,
            "total_tag": "StockholdersEquity",
            "part_tags": sorted(used_tags),
            "accession": next(iter(accessions)),
            "filing_date": max(r["filed"] for r in legs.values()),
        },
    )


def _duration_leg(facts, tag, end, cutoff):
    """Latest-filed 10-K annual-duration USD row for one tag, or None.

    Duration counterpart to _instant_leg for cash-flow statement tags such as
    Depreciation: the row must carry a start date spanning roughly one year.
    Returns None on absence or contradictory values at the latest filing date.
    """
    candidates = [
        r
        for r in facts.get("facts", {})
        .get("us-gaap", {})
        .get(tag, {})
        .get("units", {})
        .get("USD", [])
        if r.get("end") == end
        and r.get("form") in {"10-K", "10-K/A"}
        and r.get("filed", "9999") <= cutoff
        and _annual(r.get("start"), end)
    ]
    if not candidates:
        return None
    latest = max(r["filed"] for r in candidates)
    top = [r for r in candidates if r["filed"] == latest]
    if len({_number(r["val"]) for r in top}) != 1:
        return None
    return top[0]


def _sec_depreciation_plus_amortization(facts, end, cutoff, source):
    """Derive D&A as PP&E depreciation plus intangible amortization.

    Filers such as Microsoft, Alphabet, Broadcom and Abbott report no combined
    cash-flow D&A tag; they disclose Depreciation (PP&E) and
    AmortizationOfIntangibleAssets as separate annual duration tags. Their sum
    is the same cash-flow add-back the combined tag reports. Both legs must
    come from the same 10-K accession; either leg absent or contradictory
    means no derivation, never a partial sum. Returns an SEC-provenance field
    or None.
    """
    legs = {}
    for tag in ("Depreciation", "AmortizationOfIntangibleAssets"):
        row = _duration_leg(facts, tag, end, cutoff)
        if row is None:
            return None
        legs[tag] = row
    accessions = {r.get("accn") for r in legs.values()}
    if len(accessions) != 1:
        return None
    return _field(
        sum(_number(r["val"]) for r in legs.values()),
        end,
        max(r["filed"] for r in legs.values()),
        "USD",
        {
            **source,
            "provider": "SEC companyfacts",
            "formula": "Depreciation + AmortizationOfIntangibleAssets",
            "part_tags": sorted(legs),
            "accession": next(iter(accessions)),
            "filing_date": max(r["filed"] for r in legs.values()),
        },
    )


def _sec_domestic_plus_foreign_pretax(facts, end, cutoff, source):
    """Derive pretax income as domestic plus foreign continuing income.

    Filers such as Oracle disclose IncomeLossFromContinuingOperationsBefore-
    IncomeTaxesDomestic and ...Foreign instead of a combined pretax tag.
    Their sum is the same income-before-taxes line the combined tag reports.
    Both legs must be annual-duration rows from the same 10-K accession;
    either leg absent or contradictory means no derivation, never a partial
    sum. Returns an SEC-provenance field or None.
    """
    legs = {}
    for tag in (
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesForeign",
    ):
        row = _duration_leg(facts, tag, end, cutoff)
        if row is None:
            return None
        legs[tag] = row
    accessions = {r.get("accn") for r in legs.values()}
    if len(accessions) != 1:
        return None
    return _field(
        sum(_number(r["val"]) for r in legs.values()),
        end,
        max(r["filed"] for r in legs.values()),
        "USD",
        {
            **source,
            "provider": "SEC companyfacts",
            "formula": (
                "IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic + "
                "IncomeLossFromContinuingOperationsBeforeIncomeTaxesForeign"
            ),
            "part_tags": sorted(legs),
            "accession": next(iter(accessions)),
            "filing_date": max(r["filed"] for r in legs.values()),
        },
    )


# Tags that evidence preferred or noncontrolling claims anywhere in a filing.
# A member containing any of these cannot use the dual-identity zero-claim
# derivation below: real claims are always tagged somewhere on the face
# statements, so the scan guards against misreading an incomplete build-up
# as a zero. Balance, income, OCI and share tags.
CLAIM_TAGS = frozenset({
    "PreferredStockValue",
    "PreferredStockSharesAuthorized",
    "PreferredStockSharesOutstanding",
    "PreferredStockSharesIssued",
    "PreferredStockParOrStatedValuePerShare",
    "MinorityInterest",
    "NoncontrollingInterestInEquityOfSubsidiary",
    "RedeemableNoncontrollingInterestEquityCarryingAmount",
    "NetIncomeLossAttributableToNoncontrollingInterest",
    "NetIncomeLossAttributableToParent",
    "ComprehensiveIncomeNetOfTaxAttributableToNoncontrollingInterest",
    "OtherComprehensiveIncomeLossNetOfTaxPortionAttributableToNoncontrollingInterest",
    "PreferredStockDividendsIncomeStatementImpact",
    "PreferredStockDividendsAndOtherAdjustments",
    "PreferredStockDividends",
    "DividendsPreferredStock",
    "DividendsPreferredStockCash",
    "CommonStockEquity",
    # NOTE: StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest
    # is deliberately NOT a blanket block: filed total equity including NCI is
    # affirmative evidence about NCI equity (see _sec_total_equity_reconciliation
    # below). A nonzero gap to StockholdersEquity refuses the derivation there;
    # an exact match proves zero NCI equity. Tag absence alone proves nothing.
})


# Verified subsidiary-ownership disclosures that affirmatively support zero
# noncontrolling-interest equity at a filing measurement date. Income equality
# (consolidated ProfitLoss == parent NetIncomeLoss) proves zero NCI *income*
# for the period, but a subsidiary can hold minority-owned equity without
# generating minority-attributable earnings in the year -- so zero NCI equity
# additionally requires either an exact filed total-equity reconciliation or
# one of these registry entries. Each entry is keyed by CIK + filing accession
# (never by ticker alone, never hardcoded per issuer in the derivation) and
# must carry the disclosure location, exact quote, source URL, filing date,
# filing hash and verification date; an entry missing any of these, or bound
# to a different accession than the packet legs, is ignored and the
# derivation is refused. The registry is generic: any issuer's verified
# disclosure can be added following the same schema.
OWNERSHIP_DISCLOSURE_REGISTRY = Path(__file__).resolve().parent / "evidence" / "ownership_disclosures.json"
OWNERSHIP_DISCLOSURE_FIELDS = (
    "cik",
    "accession",
    "location",
    "quote",
    "source_url",
    "filed",
    "filing_sha256",
    "verified_at",
)


def _load_ownership_disclosures(registry=None):
    """Load verified ownership disclosures, or [] when the registry is absent.

    A missing registry file means no disclosure evidence, never an implicit
    pass: the derivation then refuses for lack of equity-level evidence. A
    present-but-corrupt registry raises loudly instead of shipping packets
    that silently lack evidence.
    """
    if registry is not None:
        entries = registry
    else:
        try:
            raw = OWNERSHIP_DISCLOSURE_REGISTRY.read_text()
        except FileNotFoundError:
            return []
        try:
            entries = json.loads(raw).get("disclosures", [])
        except (ValueError, AttributeError) as exc:
            raise ProviderError(f"Ownership disclosure registry is corrupt: {exc}") from None
    if not isinstance(entries, list):
        raise ProviderError("Ownership disclosure registry must hold a disclosures list.")
    return entries


def _verified_ownership_disclosure(cik, accession, registry=None):
    """Return the registry entry verifying wholly owned subsidiaries, or None.

    The entry's CIK (zero-padded) and accession must match the packet legs'
    filing exactly, and every provenance field must be present and non-empty.
    Matching is generic -- no issuer is special-cased here.
    """
    if cik is None or accession is None:
        return None
    want_cik = str(cik).zfill(10)
    for entry in _load_ownership_disclosures(registry):
        if not isinstance(entry, dict):
            continue
        if str(entry.get("cik", "")).zfill(10) != want_cik:
            continue
        if entry.get("accession") != accession:
            continue
        if any(not entry.get(field) for field in OWNERSHIP_DISCLOSURE_FIELDS):
            continue
        return entry
    return None


def _custom_taxonomy_nci_claim(facts):
    """Detect noncontrolling-claim tags outside the standard US GAAP scan.

    Companyfacts members carry standard taxonomies, but a filing can tag
    noncontrolling claims under a company-specific extension namespace that
    the CLAIM_TAGS scan cannot see. Any tag in any namespace whose name
    evidences a noncontrolling or minority claim refuses the derivation:
    extension tags are never assumed to be zero. Returns True when such a
    tag is present.
    """
    namespaces = facts.get("facts", {}) or {}
    if not isinstance(namespaces, dict):
        return False
    # Tags already handled with numeric discipline -- blanket CLAIM_TAGS
    # blocks and the total-equity reconciliation -- never trip this guard.
    handled = set(CLAIM_TAGS) | {
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"
    }
    for tags in namespaces.values():
        if not isinstance(tags, dict):
            continue
        for tag in tags:
            if tag in handled:
                continue
            name = str(tag).lower()
            if "noncontrolling" in name or "minorityinterest" in name or "minority_interest" in name:
                return True
    return False


def _sec_total_equity_reconciliation(facts, end, cutoff, se_row, accession):
    """Prove zero NCI equity from filed total equity including NCI.

    When the filer reports ``StockholdersEquityIncludingPortionAttributableTo-
    NoncontrollingInterest`` (total equity including NCI) for the same period
    in the same 10-K accession as parent ``StockholdersEquity`` and the two
    agree within $1, NCI equity is affirmatively zero. A nonzero gap is a
    filed NCI claim and refuses; absence leaves NCI equity unavailable (never
    zero by default). Returns the total-equity row on a match, else None.
    """
    total = _instant_leg(
        facts, "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", end, cutoff
    )
    if total is None:
        return None
    if total.get("accn") != accession:
        return None
    if abs(_number(total["val"]) - _number(se_row["val"])) > COMMON_INCOME_TOLERANCE_USD:
        return None
    return total


def _sec_zero_claims_from_dual_identity(facts, end, cutoff, source, cik=None, ownership_disclosures=None):
    """Establish zero preferred and zero noncontrolling claims from two identities.

    Taxonomy (US GAAP): ``NetIncomeLoss`` is income attributable to the
    parent, ``ProfitLoss`` is consolidated income including noncontrolling
    interests, and ``NetIncomeLossAvailableToCommonStockholdersBasic`` is
    the direct common-shareholder tag. Parent income is never labeled
    consolidated income here.

    For filers such as Paychex the equity statement carries only common
    components and no preferred/NCI tag exists anywhere in the member. Two
    same-accession, same-annual-period filing identities jointly bound both
    claims at zero, each proving only what it can:
    the balance identity (stockholders equity minus built-up common equity
    is zero, with treasury proven zero by issued-equals-outstanding filed
    share counts) establishes preferred equity at zero -- it says nothing
    about noncontrolling interest, because ``StockholdersEquity`` excludes
    noncontrolling claims by definition; the income identity establishes
    zero NCI *income* affirmatively, by reconciling filed consolidated
    ``ProfitLoss`` to filed parent ``NetIncomeLoss`` for the same annual
    period in the same accession (equal values mean zero NCI income),
    supported by the valid balance identity plus the member-wide claim-tag
    scan. The direct common tag equaling parent income shows no preferred
    distribution was deducted. Zero NCI *equity* -- which zero NCI income
    alone cannot establish, since minority-owned equity can sit idle for a
    year -- additionally requires equity-level evidence from exactly one of
    two reusable paths: an exact same-accession filed total-equity
    reconciliation (total equity including NCI equals parent stockholders
    equity), or a verified wholly owned-subsidiaries ownership disclosure
    from the registry bound to the same CIK and accession. Either residual
    beyond $1, any claim tag anywhere in the member (including
    company-extension namespaces), legs from more than one accession,
    mismatched annual periods, a missing consolidated leg, or missing
    equity-level evidence refuses the derivation -- a lone zero residual is
    never enough, because offsetting unverified components could mimic it,
    and tag absence alone is never proof of zero. Returns
    (preferred_field, nci_field) or (None, None) atomically: the two claims
    are never split from partial evidence.
    """
    if _custom_taxonomy_nci_claim(facts):
        return None, None
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    for tag in CLAIM_TAGS:
        if tag in us_gaap:
            return None, None
    legs = {}
    common_head = None
    for csv_tag, apic_tag in COMMON_HEAD_PAIRS:
        candidate = [_instant_leg(facts, tag, end, cutoff) for tag in (csv_tag, apic_tag)]
        if all(row is not None for row in candidate):
            legs[csv_tag], legs[apic_tag] = candidate
            common_head = _number(candidate[0]["val"]) + _number(candidate[1]["val"])
            break
    if common_head is None:
        combined = _instant_leg(facts, "CommonStocksIncludingAdditionalPaidInCapital", end, cutoff)
        if combined is None:
            return None, None
        legs["CommonStocksIncludingAdditionalPaidInCapital"] = combined
        common_head = _number(combined["val"])
    for tag in ("RetainedEarningsAccumulatedDeficit", "AccumulatedOtherComprehensiveIncomeLossNetOfTax"):
        row = _instant_leg(facts, tag, end, cutoff)
        if row is None:
            return None, None
        legs[tag] = row
    treasury_value = None
    for candidate_tag in ("TreasuryStockValue", "TreasuryStockCommonValue"):
        row = _instant_leg(facts, candidate_tag, end, cutoff)
        if row is not None:
            legs[candidate_tag] = row
            treasury_value = _number(row["val"])
            break
    if treasury_value is None:
        issued = _shares_leg(facts, "CommonStockSharesIssued", end, cutoff)
        outstanding = _shares_leg(facts, "CommonStockSharesOutstanding", end, cutoff)
        if (
            issued is None
            or outstanding is None
            or _number(issued["val"]) != _number(outstanding["val"])
            or issued.get("accn") != outstanding.get("accn")
        ):
            return None, None
        legs["CommonStockSharesIssued"] = issued
        legs["CommonStockSharesOutstanding"] = outstanding
        treasury_value = 0.0
    se_row = _instant_leg(facts, "StockholdersEquity", end, cutoff)
    if se_row is None:
        return None, None
    legs["StockholdersEquity"] = se_row
    accessions = {r.get("accn") for r in legs.values()}
    if len(accessions) != 1:
        return None, None
    common = (
        common_head
        + _number(legs["RetainedEarningsAccumulatedDeficit"]["val"])
        + _number(legs["AccumulatedOtherComprehensiveIncomeLossNetOfTax"]["val"])
        - treasury_value
    )
    if abs(_number(se_row["val"]) - common) > COMMON_INCOME_TOLERANCE_USD:
        return None, None
    # Parent-attributable income, consolidated income (including NCI), and the
    # direct common tag must all describe the same annual period in the same
    # filing: equal end and start dates, one 10-K accession shared with the
    # equity legs. The parent leg's accession is checked too, not just the
    # direct leg's -- pairing income from one filing with equity from another
    # proves nothing.
    parent = _duration_leg(facts, "NetIncomeLoss", end, cutoff)
    consolidated = _duration_leg(facts, "ProfitLoss", end, cutoff)
    direct = _duration_leg(facts, "NetIncomeLossAvailableToCommonStockholdersBasic", end, cutoff)
    if parent is None or consolidated is None or direct is None:
        return None, None
    income_legs = (parent, consolidated, direct)
    starts = {r.get("start") for r in income_legs}
    if len(starts) != 1 or None in starts:
        return None, None
    accession = next(iter(accessions))
    if any(r.get("accn") != accession for r in income_legs):
        return None, None
    if abs(_number(parent["val"]) - _number(direct["val"])) > COMMON_INCOME_TOLERANCE_USD:
        return None, None
    # Affirmative NCI evidence: consolidated income including NCI equals
    # parent-attributable income for the same period, so NCI income is zero.
    # Parent-minus-direct equality alone cannot show this -- it only bounds
    # preferred distributions.
    if abs(_number(consolidated["val"]) - _number(parent["val"])) > COMMON_INCOME_TOLERANCE_USD:
        return None, None
    # Equity-level NCI evidence: zero NCI income does not establish zero NCI
    # equity. Prefer the filed total-equity reconciliation when the filer
    # reports it (numbers beat text); otherwise accept a verified wholly
    # owned-subsidiaries disclosure bound to this CIK and accession. Filed
    # nonzero NCI equity refuses outright and no disclosure can override it.
    resolved_cik = cik if cik is not None else facts.get("cik")
    total_row = _instant_leg(
        facts, "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", end, cutoff
    )
    nci_equity_evidence = None
    ownership = None
    if total_row is not None:
        matched = _sec_total_equity_reconciliation(facts, end, cutoff, se_row, accession)
        if matched is None:
            return None, None
        nci_equity_evidence = "total_equity_reconciliation"
        legs["StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"] = matched
    else:
        ownership = _verified_ownership_disclosure(resolved_cik, accession, ownership_disclosures)
        if ownership is None:
            return None, None
        nci_equity_evidence = "ownership_disclosure"
    filed = max([r["filed"] for r in legs.values()] + [r["filed"] for r in income_legs])
    if nci_equity_evidence == "total_equity_reconciliation":
        equity_note = (
            "filed total equity including NCI equals parent stockholders equity "
            "in the same accession (NCI equity zero)"
        )
    else:
        equity_note = (
            "verified wholly owned-subsidiaries disclosure at "
            + ownership["location"]
            + " in " + ownership["accession"] + " (NCI equity zero)"
        )
    provenance = {
        **source,
        "provider": "SEC companyfacts",
        "formula": (
            "stockholders equity minus built-up parent-common equity is zero "
            "(preferred equity zero; stockholders equity excludes NCI) and filed "
            "consolidated ProfitLoss equals filed parent NetIncomeLoss for the same "
            "annual period in the same accession (NCI income zero), with the filed "
            "direct common basic tag equal to parent (no preferred distribution); "
            "no preferred/NCI tag anywhere in the member (" + ", ".join(sorted(legs)) + "); "
            + equity_note
        ),
        "nci_equity_evidence": nci_equity_evidence,
        "part_tags": sorted(legs),
        "income_identity_tags": [
            "NetIncomeLoss",
            "ProfitLoss",
            "NetIncomeLossAvailableToCommonStockholdersBasic",
        ],
        "income_period_start": next(iter(starts)),
        "accession": accession,
        "filing_date": filed,
        **(
            {
                "ownership_disclosure": {
                    "location": ownership["location"],
                    "quote": ownership["quote"],
                    "source_url": ownership["source_url"],
                    "filed": ownership["filed"],
                    "filing_sha256": ownership["filing_sha256"],
                    "verified_at": ownership["verified_at"],
                }
            }
            if ownership is not None
            else {}
        ),
    }
    return (
        _field(0.0, end, filed, "USD", {**provenance, "claim": "preferred_equity"}),
        _field(0.0, end, filed, "USD", {**provenance, "claim": "minority_interest"}),
    )


def _shares_leg(facts, tag, end, cutoff):
    """Latest-filed 10-K instant shares-unit row for one tag, or None.

    Share-count counterpart to _instant_leg for ownership evidence such as
    CommonStockSharesIssued. Returns None on absence or contradiction.
    """
    candidates = [
        r
        for r in facts.get("facts", {})
        .get("us-gaap", {})
        .get(tag, {})
        .get("units", {})
        .get("shares", [])
        if r.get("end") == end
        and r.get("form") in {"10-K", "10-K/A"}
        and r.get("filed", "9999") <= cutoff
        and not r.get("start")
    ]
    if not candidates:
        return None
    latest = max(r["filed"] for r in candidates)
    top = [r for r in candidates if r["filed"] == latest]
    if len({_number(r["val"]) for r in top}) != 1:
        return None
    return top[0]


def _derived(value, components, formula, unit="USD"):
    return _field(
        value,
        components[0]["period_end"],
        max(x["available_at"] for x in components),
        unit,
        {"provider": "PPE SEC-derived", "formula": formula, "components": components},
    )


def _resolve_canonical_conflict(metric, rows, facts, end):
    """Resolve same-day conflicting canonical lake rows via ordered SEC tags.

    The upstream lake merges synonymous XBRL tags (NetIncomeLoss vs ProfitLoss,
    Revenues vs RevenueFromContractWithCustomerExcludingAssessedTax) into one
    canonical metric. When two values share the latest availability date, prefer
    the value matching the earliest-priority SEC tag -- the same order _sec uses
    -- read in that row's own filing accession. Returns the winning rows, or
    None when facts are absent or no value matches. Never invents a value: an
    unmatched conflict still raises.
    """
    tags = SEC_TAGS.get(metric, [])
    if not facts or not tags:
        return None
    scored = []
    for row in rows:
        try:
            value = _number(row.get("value_decimal", row.get("value")))
        except ProviderError:
            return None
        accession = row.get("source_record_id")
        rank = None
        for i, tag in enumerate(tags):
            try:
                expected = _filing_value(facts, [tag], end, accession)
            except ProviderError:
                return None
            if expected is not None and abs(expected - value) <= COMMON_INCOME_TOLERANCE_USD:
                rank = i
                break
        if rank is None:
            return None
        scored.append((rank, row))
    best = min(rank for rank, _ in scored)
    winners = [row for rank, row in scored if rank == best]
    if len({_number(r.get("value_decimal", r.get("value"))) for r in winners}) != 1:
        return None
    return winners


def _facts_revenue_ends(facts, cutoff):
    """Annual 10-K revenue period ends available in SEC facts at cutoff."""
    ends = set()
    for tag in SEC_TAGS.get("revenue", []):
        for r in facts.get("facts", {}).get("us-gaap", {}).get(tag, {}).get("units", {}).get("USD", []):
            if (
                r.get("form") in {"10-K", "10-K/A"}
                and r.get("filed", "9999") <= cutoff
                and (r.get("end") or "9999") <= cutoff
                and _annual(r.get("start"), r.get("end"))
            ):
                ends.add(r["end"])
    return sorted(ends)


def build_packet(ticker, cik, rows, facts, cutoff, source):
    ticker = ticker_symbol(ticker)
    date.fromisoformat(cutoff)
    if facts and str(facts.get("cik", "")).zfill(10) != cik:
        raise ProviderError("SEC issuer mismatch.")
    groups = {}
    inverse = {v: k for k, v in CANONICAL.items()}
    for row in rows:
        metric = inverse.get(row.get("metric_id"))
        if not metric or row.get("source_id") != "SEC" or row.get("period_type") != "annual":
            continue
        if row.get("quality_status") not in {"REPORTED", "CALCULATED", "VERIFIED"}:
            continue
        entity = row.get("entity_id")
        if entity:
            identity = re.match(r"entity:sec:cik:([0-9]{10})(?:$|[:_])", entity)
            if not identity or identity.group(1) != cik:
                raise ProviderError("PPE observation issuer mismatch.")
        end = row.get("period_end")
        available = row.get("available_at", "")
        if not available or not end or end > cutoff or available[:10] > cutoff:
            continue
        if metric in {"revenue", "ebit", "net_income"}:
            if not _annual(row.get("period_start"), end):
                continue
        elif row.get("period_start") not in {None, "", end}:
            continue
        groups.setdefault(end, {}).setdefault(metric, []).append(row)
    ends = sorted(k for k, v in groups.items() if v.get("revenue"))[-3:]
    if len(ends) < 3 and facts:
        # Upstream coverage gap (e.g. bank revenue never mapped to the canonical
        # lake metric): complete the three annual periods from SEC facts revenue.
        # Every field taken this way carries SEC-companyfacts provenance.
        ends = sorted(set(ends) | set(_facts_revenue_ends(facts, cutoff)))[-3:]
    if not ends:
        raise ProviderError("No eligible annual PPE revenue.")
    selected = {}
    for end in ends:
        selected[end] = {}
        for metric, candidates in groups.get(end, {}).items():
            latest = max(r["available_at"] for r in candidates)
            top = [r for r in candidates if r["available_at"] == latest]
            if any(r.get("unit") != "USD" for r in top):
                raise ProviderError(f"Unexpected PPE unit for {metric}.")
            distinct = {_number(r.get("value_decimal", r.get("value"))) for r in top}
            superseded = []
            if len(distinct) != 1:
                resolved = _resolve_canonical_conflict(metric, top, facts, end)
                if resolved is None:
                    raise ProviderError(f"Conflicting PPE {metric} observations for {end}.")
                winner = _number(resolved[0].get("value_decimal", resolved[0].get("value")))
                superseded = sorted(distinct - {winner})
                top = resolved
            row = top[0]
            selected[end][metric] = _field(
                row.get("value_decimal", row.get("value")),
                end,
                latest,
                "USD",
                {
                    **source,
                    "provider": "PPE SEC canonical",
                    "accession": row.get("source_record_id"),
                    "evidence_id": row.get("evidence_id"),
                    "period_start": row.get("period_start"),
                    "quality_status": row.get("quality_status"),
                    **(
                        {"superseded_canonical_values": superseded}
                        if superseded
                        else {}
                    ),
                },
            )
    groups = selected
    historical = []
    dividends = []
    common_income = []
    bridges = {}
    shares = None
    interest = None
    facts = facts or {}
    sec_source = source.get("sec_source", {})
    for end in ends:
        g = groups.get(end, {})
        f = {
            k: g.get(k) or _sec(facts, k, end, cutoff, sec_source)
            for k in HISTORY_FIELDS
            if k not in {"tax_rate", "nwc"}
        }
        values = {
            k: _sec(facts, k, end, cutoff, sec_source)
            for k in [
                "current_assets",
                "current_liabilities",
                "cash",
                "short_term_debt",
                "current_maturities",
                "short_term_borrowings",
                "long_term_debt",
                "tax_expense",
                "pretax_income",
                "diluted_shares",
                "common_dividends",
                "interest_expense",
                "common_income",
            ]
        }
        if (
            not values["short_term_debt"]
            and values["current_maturities"]
            and values["short_term_borrowings"]
        ):
            c = [values["current_maturities"], values["short_term_borrowings"]]
            values["short_term_debt"] = _derived(
                sum(x["value"] for x in c),
                c,
                "current long-term debt + short-term borrowings/commercial paper",
            )
        nwc = [
            values[k] for k in ["current_assets", "cash", "current_liabilities", "short_term_debt"]
        ]
        f["nwc"] = (
            _derived(
                nwc[0]["value"] - nwc[1]["value"] - nwc[2]["value"] + nwc[3]["value"],
                nwc,
                "(current assets - cash) - (current liabilities - current interest-bearing debt)",
            )
            if all(nwc)
            else None
        )
        if values["pretax_income"] is None:
            values["pretax_income"] = _sec_domestic_plus_foreign_pretax(
                facts, end, cutoff, sec_source
            )
        tax = [values[k] for k in ["tax_expense", "pretax_income"]]
        f["tax_rate"] = (
            _derived(
                tax[0]["value"] / tax[1]["value"], tax, "income tax expense / pretax income", "pure"
            )
            if all(tax) and tax[1]["value"]
            else None
        )
        if f.get("d_and_a") is None:
            derived_da = _sec_depreciation_plus_amortization(facts, end, cutoff, sec_source)
            if derived_da is not None:
                f["d_and_a"] = derived_da
        if f.get("capex"):
            f["capex"]["value"] = abs(f["capex"]["value"])
        f["diluted_shares"] = values["diluted_shares"]
        historical.append({"period_end": end, "fields": f})
        if values["common_dividends"]:
            dividends.append(values["common_dividends"])
        if values["common_income"]:
            # Reject a direct tag whose residual to the same filing's parent income is unexplained.
            verdict = common_income_bridge(facts, end, values["common_income"])
            values["common_income"]["provenance"]["bridge"] = verdict
            if bridge_accepted(verdict):
                common_income.append(values["common_income"])
        bridges = {k: g.get(k) or _sec(facts, k, end, cutoff, sec_source) for k in BRIDGE_FIELDS}
        if bridges.get("long_term_debt") is None:
            # Filers such as AT&T disclose total LongTermDebt (including current)
            # but no Noncurrent split; the noncurrent portion is total less the
            # current portion from the same 10-K accession. Ordered most-standard
            # first; never inferred as zero.
            for total_tag, part_tag in LTD_TOTAL_PAIRS:
                derived = _sec_subtotal_difference(
                    facts,
                    total_tag,
                    part_tag,
                    end,
                    cutoff,
                    sec_source,
                    f"{total_tag} minus {part_tag}",
                )
                if derived is not None:
                    bridges["long_term_debt"] = derived
                    break
    if bridges.get("preferred_equity") is None:
        bridges["preferred_equity"] = _sec_subtotal_difference(
            facts,
            "StockholdersEquity",
            "CommonStockEquity",
            end,
            cutoff,
            sec_source,
            "stockholders equity minus common equity",
        )
    if bridges.get("preferred_equity") is None:
        bridges["preferred_equity"] = _sec_preferred_from_common_buildup(
            facts, end, cutoff, sec_source
        )
    if bridges.get("minority_interest") is None:
        bridges["minority_interest"] = _sec_subtotal_difference(
            facts,
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
            "StockholdersEquity",
            end,
            cutoff,
            sec_source,
            "total equity including noncontrolling interest minus stockholders equity",
        )
    if bridges.get("preferred_equity") is None and bridges.get("minority_interest") is None:
        # Dual-identity zero claims (Paychex pattern) set both bridge claims
        # atomically: the balance identity proves preferred zero only, and
        # zero NCI additionally requires affirmative same-accession
        # consolidated-ProfitLoss-equals-parent-NetIncomeLoss evidence plus a
        # member-wide claim-tag scan (standard and extension namespaces) plus
        # equity-level NCI evidence (filed total-equity reconciliation or a
        # verified ownership disclosure for this CIK and accession). Tag
        # absence alone never proves zero; a missing consolidated leg or
        # missing equity-level evidence leaves NCI unavailable and the packet
        # ineligible. Never splits one identity across claims.
        zero_preferred, zero_nci = _sec_zero_claims_from_dual_identity(
            facts, end, cutoff, sec_source, cik=cik
        )
        if zero_preferred is not None:
            bridges["preferred_equity"] = zero_preferred
            bridges["minority_interest"] = zero_nci
    bridges["short_term_debt"] = values["short_term_debt"]
    shares = values["diluted_shares"]
    interest = values["interest_expense"]
    adjustment_facts = None
    if facts:
        # Fail closed: a supplement that cannot be turned into validated
        # evidence fails publication loudly instead of shipping a packet that
        # silently lacks evidence. Packets built without a supplement (tests,
        # canonical-only builds) simply carry no evidence section.
        from accounting_policy import build_adjustment_facts_from_companyfacts

        try:
            adjustment_facts = build_adjustment_facts_from_companyfacts(
                cik, ends, facts, cutoff, receipt=source.get("sec_source")
            )
        except Exception as exc:
            raise ProviderError(
                f"PPE adjustment evidence build failed for {ticker}: {exc}"
            ) from exc
    packet = {
        "schema_version": SCHEMA,
        "ticker": ticker,
        "cik": cik,
        "cutoff_date": cutoff,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "historical": historical,
        "bridge": bridges,
        "diluted_shares": shares,
        "interest_expense": interest,
        "dividends": dividends,
        "common_income": common_income,
    }
    if adjustment_facts is not None:
        packet["adjustment_facts"] = adjustment_facts
    validate_packet(packet, ticker, cutoff)
    return packet


def _date(value, *, timestamp=False):
    try:
        if not isinstance(value, str):
            raise ValueError()
        parsed = (
            datetime.fromisoformat(value.replace("Z", "+00:00")).date()
            if timestamp and len(value) > 10
            else date.fromisoformat(value)
        )
        if value[:10] != parsed.isoformat():
            raise ValueError()
        return parsed
    except (TypeError, ValueError):
        raise ProviderError("Invalid PPE observation date.") from None


def _validate_annual_series(rows, label, metric, ends, check):
    """Validate a per-period series (dividends, common income) aligned to annual periods."""
    if not isinstance(rows, list) or len(rows) > 3:
        raise ProviderError(f"Invalid PPE {label} coverage.")
    previous = None
    for f in rows:
        if not isinstance(f, dict):
            raise ProviderError(f"Invalid PPE {label} field.")
        end = _date(f.get("period_end"))
        if end not in ends or (previous and end <= previous):
            raise ProviderError(f"Invalid PPE {label} periods.")
        check(f, metric, end)
        previous = end


def validate_packet(packet, ticker, asof):
    if (
        not isinstance(packet, dict)
        or packet.get("schema_version") != SCHEMA
        or packet.get("ticker") != ticker
    ):
        raise ProviderError("PPE packet identity/schema mismatch.")
    cutoff = _date(packet.get("cutoff_date"))
    requested = _date(asof)
    if cutoff > requested:
        raise ProviderError("PPE packet was selected after this valuation cutoff.")
    if not isinstance(packet.get("source"), dict):
        raise ProviderError("Invalid PPE source.")
    history = packet.get("historical")
    if not isinstance(history, list) or not 1 <= len(history) <= 3:
        raise ProviderError("Invalid PPE annual coverage.")

    def field(f, metric, end):
        if f is None:
            return
        if not isinstance(f, dict):
            raise ProviderError("Invalid PPE field shape.")
        if not isinstance(f.get("value"), (int, float)):
            raise ProviderError("Invalid PPE numeric field type.")
        value = _number(f.get("value"))
        expected = (
            "shares" if metric == "diluted_shares" else "pure" if metric == "tax_rate" else "USD"
        )
        if f.get("unit") != expected or not isinstance(f.get("provenance"), dict):
            raise ProviderError("Invalid PPE field provenance/unit.")
        period = _date(f.get("period_end"))
        available = _date(f.get("available_at"), timestamp=True)
        if period != end or period > cutoff or available > cutoff or available < period:
            raise ProviderError("PPE observation unavailable or period mismatched at cutoff.")
        if metric == "diluted_shares" and value <= 0:
            raise ProviderError("Invalid PPE diluted shares.")

    ends = []
    for row in history:
        if not isinstance(row, dict) or not isinstance(row.get("fields"), dict):
            raise ProviderError("Invalid PPE historical row.")
        end = _date(row.get("period_end"))
        if ends and not 330 <= (end - ends[-1]).days <= 400:
            raise ProviderError("PPE annual periods must be chronological and unique.")
        ends.append(end)
        if set(row["fields"]) - (set(HISTORY_FIELDS) | {"diluted_shares"}):
            raise ProviderError("Unknown PPE historical field.")
        if not row["fields"].get("revenue"):
            raise ProviderError("Missing PPE revenue.")
        for metric, f in row["fields"].items():
            field(f, metric, end)
    bridge = packet.get("bridge")
    if not isinstance(bridge, dict) or set(bridge) - set(BRIDGE_FIELDS):
        raise ProviderError("Invalid PPE bridge.")
    for metric, f in bridge.items():
        field(f, metric, ends[-1])
    field(packet.get("diluted_shares"), "diluted_shares", ends[-1])
    field(packet.get("interest_expense"), "interest_expense", ends[-1])
    _validate_annual_series(packet.get("dividends"), "dividend", "common_dividends", ends, field)
    # Optional: packets published before the common-income mapping omit this key.
    _validate_annual_series(
        packet.get("common_income", []), "common income", "common_income", ends, field
    )
    for x in packet.get("common_income", []):
        if not bridge_accepted((x.get("provenance") or {}).get("bridge")):
            raise ProviderError("Common income is not verified against its filing.")
    if "adjustment_facts" in packet:
        _validate_adjustment_evidence(packet["adjustment_facts"], packet, ends, cutoff)
    return packet


def _validate_adjustment_evidence(adj, packet, ends, cutoff):
    """Independently re-check published accounting evidence at the boundary.

    The offline extractor already validates each fact; this validator repeats
    every check that matters for publication (issuer, taxonomy, unit, annual
    duration, filing dates, cutoff, receipts, filing-context agreement) so a
    malformed artifact can never be published or loaded. Anything malformed
    raises; absence of evidence is expressed with explicit unavailable entries,
    never by omitting the section silently.
    """
    if not isinstance(adj, dict) or adj.get("schema_version") != "accounting-adjustments-v1":
        raise ProviderError("Invalid PPE adjustment evidence schema.")
    adj_cik = str(adj.get("cik", "")).zfill(10)
    packet_cik = str(packet.get("cik", "")).zfill(10)
    # Both sides must carry a real issuer identifier: two combined supplements
    # with missing identifiers must never agree with each other by default.
    if (
        not re.fullmatch(r"[0-9]{10}", adj_cik)
        or adj_cik == "0000000000"
        or adj_cik != packet_cik
    ):
        raise ProviderError("PPE adjustment evidence issuer mismatch.")
    if adj.get("taxonomy", "us-gaap") != "us-gaap":
        raise ProviderError("PPE adjustment evidence taxonomy is not us-gaap.")
    end_strings = {e.isoformat() for e in ends}

    def check_fact(fact, label):
        if not isinstance(fact, dict):
            raise ProviderError(f"Invalid PPE adjustment evidence {label}.")
        if fact.get("period_end") not in end_strings:
            raise ProviderError(f"PPE adjustment evidence {label} period mismatch.")
        amount = fact.get("amount")
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise ProviderError(f"Invalid PPE adjustment evidence {label} amount.")
        if fact.get("unit") != "USD":
            raise ProviderError(f"PPE adjustment evidence {label} unit is not USD.")
        if not isinstance(fact.get("tag"), str) or not fact["tag"]:
            raise ProviderError(f"PPE adjustment evidence {label} tag missing.")
        if fact.get("form") not in {"10-K", "10-K/A"}:
            raise ProviderError(f"PPE adjustment evidence {label} form not accepted.")
        try:
            start = date.fromisoformat(str(fact.get("period_start"))[:10])
            end = date.fromisoformat(str(fact.get("period_end"))[:10])
            filed = date.fromisoformat(str(fact.get("filed"))[:10])
        except (TypeError, ValueError):
            raise ProviderError(
                f"PPE adjustment evidence {label} has missing/invalid dates."
            ) from None
        if not 330 <= (end - start).days <= 400:
            raise ProviderError(f"PPE adjustment evidence {label} is not annual duration.")
        if filed > cutoff:
            raise ProviderError(f"PPE adjustment evidence {label} filed after cutoff.")
        if not isinstance(fact.get("accession"), str) or not fact["accession"]:
            raise ProviderError(f"PPE adjustment evidence {label} receipt missing.")

    facts_map = adj.get("facts")
    if not isinstance(facts_map, dict):
        raise ProviderError("Invalid PPE adjustment evidence facts.")
    accessions_by_end = {}
    for kind, items in facts_map.items():
        if not isinstance(kind, str) or not kind or not isinstance(items, list):
            raise ProviderError("Invalid PPE adjustment evidence facts.")
        for fact in items:
            check_fact(fact, "fact")
            accessions_by_end.setdefault(fact["period_end"], set()).add(fact["accession"])
    ebit_facts = adj.get("ebit_facts", [])
    if not isinstance(ebit_facts, list):
        raise ProviderError("Invalid PPE adjustment EBIT evidence.")
    for fact in ebit_facts:
        check_fact(fact, "EBIT fact")
        # The EBIT tie-out is only meaningful within one filing: an EBIT fact
        # whose accession disagrees with the same-period adjustment facts is
        # a contradictory filing context, rejected rather than paired.
        others = accessions_by_end.get(fact["period_end"], set())
        if others and others != {fact["accession"]}:
            raise ProviderError("PPE adjustment EBIT filing context contradicts adjustments.")
    for key in ("unavailable", "conflicts", "future_restatements"):
        if not isinstance(adj.get(key, []), list):
            raise ProviderError("Invalid PPE adjustment evidence diagnostics.")


def apply_packet(document, packet, asof):
    validate_packet(packet, document["company"]["ticker"], asof)
    doc = deepcopy(document)
    coverage = []
    fallback = doc["source"].get("name", "existing source")

    def fallback_period(path):
        if path.startswith("historical."):
            return path.split(".")[1]
        if path.startswith("bridge."):
            return document["bridge"].get("as_of")
        if path.startswith("market.price"):
            return document["market"].get("price_as_of")
        if path == "common_dividends":
            return document["source"].get("common_dividends", {}).get("period_end")
        if path == "common_book_equity":
            return document["source"].get("common_book_equity", {}).get("period_end")
        return document["historical"][-1]["period_end"]

    def choose(path, old, f):
        coverage.append(
            {
                "field": path,
                "status": "PPE" if f else "fallback",
                "provider": f["provenance"].get("provider", "PPE") if f else fallback,
                "period_end": f["period_end"] if f else fallback_period(path),
                "available_at": f["available_at"] if f else document["source"].get("available_at"),
                "value": f["value"] if f else old,
                "provenance": f["provenance"] if f else {},
            }
        )
        return f["value"] if f else old

    matched = []
    common_by_end = {x["period_end"]: x for x in packet.get("common_income", [])}
    for row in doc["historical"]:
        candidates = [
            x
            for x in packet["historical"]
            if abs(
                (date.fromisoformat(x["period_end"]) - date.fromisoformat(row["period_end"])).days
            )
            <= 7
        ]
        p = candidates[0] if len(candidates) == 1 else None
        if p:
            matched.append(p)
        row.setdefault("provenance", {})
        original_end = row["period_end"]
        used_fields = {}
        for key in HISTORY_FIELDS:
            if p and key == "net_income":
                # Consolidated NetIncomeLoss/ProfitLoss never replaces the baseline. Only a
                # direct common-shareholder observation for the same period may.
                f = common_by_end.get(p["period_end"])
            else:
                f = p["fields"].get(key) if p else None
            rejected_tax = f if key == "tax_rate" and f and not 0 <= f["value"] <= 1 else None
            if rejected_tax:
                f = None
            row[key] = choose(f"historical.{original_end}.{key}", row.get(key), f)
            if rejected_tax:
                coverage[-1]["excluded_ppe_observation"] = rejected_tax
                coverage[-1]["reason"] = "Reported SEC tax ratio is outside the model's zero-to-one range; dated baseline tax assumption retained."
                doc["source"].setdefault("warnings", []).append(
                    f"SEC reported tax ratio for {original_end} is {rejected_tax['value']:.2%}; "
                    "the model retains the labeled baseline tax assumption while using other eligible SEC fields."
                )
            if f:
                used_fields[key] = f
                row["provenance"][key] = {
                    **f["provenance"],
                    "period_end": f["period_end"],
                    "available_at": f["available_at"],
                }
        if p and len(used_fields) == len(HISTORY_FIELDS):
            row["period_end"] = p["period_end"]
            row["available_at"] = max(p["fields"][k]["available_at"] for k in HISTORY_FIELDS)
        # Partial fiscal-year matches retain exact dates in each field's provenance.
    latest = packet["historical"][-1]["period_end"]
    aligned = bool(
        any(p["period_end"] == latest for p in matched)
        and abs(
            (
                date.fromisoformat(doc["historical"][-1]["period_end"]) - date.fromisoformat(latest)
            ).days
        )
        <= 7
        and abs((date.fromisoformat(doc["bridge"]["as_of"]) - date.fromisoformat(latest)).days) <= 7
    )
    for key in BRIDGE_FIELDS:
        f = packet["bridge"].get(key) if aligned else None
        doc["bridge"][key] = choose("bridge." + key, doc["bridge"].get(key), f)
        if f:
            doc["source"].setdefault("bridge_provenance", {})[key] = f
    shares = packet.get("diluted_shares") if aligned else None
    doc["market"]["diluted_shares"] = choose(
        "market.diluted_shares", doc["market"].get("diluted_shares"), shares
    )
    if shares:
        doc["market"]["shares_basis"] = (
            "SEC annual weighted-average diluted shares via PPE; " + shares["period_end"]
        )
    dividends = packet.get("dividends", [])
    existing = doc["source"].get("common_dividends", {})
    if aligned and dividends and dividends[-1]["period_end"] == latest:
        d = dividends[-1]
        existing.update(
            value=d["value"],
            period_end=latest,
            unit="USD",
            provenance=d,
            per_share=d["value"] / doc["market"]["diluted_shares"],
        )
        existing["historical"] = [
            {
                "period_end": x["period_end"],
                "value": x["value"],
                "shares": next(
                    (
                        (row["fields"].get("diluted_shares") or {}).get("value")
                        for row in packet["historical"]
                        if row["period_end"] == x["period_end"]
                    ),
                    None,
                ),
            }
            for x in dividends
        ]
        doc["source"]["common_dividends"] = existing
    choose(
        "common_dividends",
        existing.get("value"),
        dividends[-1] if aligned and dividends and dividends[-1]["period_end"] == latest else None,
    )
    choose("common_book_equity", doc["source"].get("common_book_equity", {}).get("value"), None)
    for key in ["price", "price_as_of"]:
        choose("market." + key, doc["market"].get(key), None)
    costs = doc["source"].get("capital_costs", {})
    if costs:
        fallback_interest = (
            costs["reported_cost_of_debt"] * costs.get("debt", 0)
            if costs.get("reported_cost_of_debt") is not None
            else None
        )
        debt = doc["bridge"]["short_term_debt"] + doc["bridge"]["long_term_debt"]
        costs.update(
            debt=debt,
            debt_book_value=debt,
            tax_rate=doc["historical"][-1]["tax_rate"],
        )
        interest = packet.get("interest_expense") if aligned else None
        if interest and debt > 0:
            costs["reported_cost_of_debt"] = interest["value"] / debt
        elif fallback_interest is not None and debt > 0:
            costs["reported_cost_of_debt"] = fallback_interest / debt
            costs["debt_cost_basis"] = (
                "Fallback annual interest expense / merged split debt; review field sources"
            )
        else:
            costs["reported_cost_of_debt"] = None
        if interest and debt > 0:
            costs["debt_cost_basis"] = (
                "SEC annual interest expense / dated split debt; field sources retained in PPE coverage"
            )
        if "risk_free_rate" in costs:
            choose("capital_costs.risk_free_rate", costs["risk_free_rate"], None)
        if "beta" in costs:
            choose("capital_costs.beta", costs["beta"], None)
    doc["source"].update(
        kind="api",
        name="PPE / SEC financials + labeled market fallbacks"
        if any(x["status"] == "PPE" for x in coverage)
        else fallback + " (PPE fiscal periods unmatched)",
        ppe_release=packet["source"],
        ppe_cutoff=packet["cutoff_date"],
        field_coverage=coverage,
    )
    doc["source"].setdefault("warnings", []).append(
        "PPE annual periods match the baseline fiscal end within seven days; actual observation dates and fallback sources are retained per field. Missing PPE fields use the labeled baseline source; common-stockholder income is replaced only by a direct SEC NetIncomeLossAvailableToCommonStockholdersBasic observation. Ordinary-share market equity remains the WACC weight basis; diluted weighted-average shares are used for per-share valuation."
    )
    return doc


def enrich_packet(previous, candidate, asof):
    """Preserve same-period published evidence when a supplement is absent/older."""
    validate_packet(previous, candidate['ticker'], asof)
    validate_packet(candidate, candidate['ticker'], asof)
    if previous.get('cik') != candidate.get('cik'):
        raise ProviderError('PPE enrichment issuer mismatch.')
    result = deepcopy(candidate)

    def choose(old, new):
        if not old or (new and old['period_end'] != new['period_end']):
            return new
        if not new or old['available_at'][:10] > new['available_at'][:10]:
            return deepcopy(old)
        if old['available_at'][:10] == new['available_at'][:10] and old['value'] != new['value']:
            raise ProviderError(f"Conflicting published and incoming PPE values for {old['period_end']} at the same availability date.")
        return new

    prior = {row['period_end']: row for row in previous['historical']}
    for row in result['historical']:
        old = prior.get(row['period_end'], {}).get('fields', {})
        row['fields'] = {k: choose(old.get(k), v) for k, v in row['fields'].items()}
    if previous['historical'][-1]['period_end'] == result['historical'][-1]['period_end']:
        result['bridge'] = {k: choose(previous['bridge'].get(k), v) for k, v in result['bridge'].items()}
        for key in ['diluted_shares', 'interest_expense']:
            result[key] = choose(previous.get(key), result.get(key))
    dividends = {row['period_end']: row for row in previous['dividends']}
    incoming = {row['period_end']: row for row in result['dividends']}
    result['dividends'] = [value for row in result['historical']
        if (value := choose(dividends.get(row['period_end']), incoming.get(row['period_end']))) is not None]
    common = {row['period_end']: row for row in previous.get('common_income', [])}
    incoming_common = {row['period_end']: row for row in result.get('common_income', [])}
    result['common_income'] = [value for row in result['historical']
        if (value := choose(common.get(row['period_end']), incoming_common.get(row['period_end']))) is not None]
    if 'adjustment_facts' not in result and 'adjustment_facts' in previous:
        prev_adj = previous['adjustment_facts']
        prev_ends = {r['period_end'] for r in previous.get('historical', [])}
        result_ends = {r['period_end'] for r in result.get('historical', [])}
        if isinstance(prev_adj, dict) and prev_ends <= result_ends:
            result['adjustment_facts'] = deepcopy(prev_adj)
    return validate_packet(result, result['ticker'], asof)


def supplement_statement_facts(facts, ends, packet, ticker, asof):
    """Fill statement gaps before baseline validation, preserving SEC provenance.

    This is an adapter into the statement assembler's metric vocabulary. It never
    labels SEC evidence as Yahoo or treats general net income as common income.
    """
    validate_packet(packet, ticker, asof)
    result = deepcopy(facts)
    mapping = {'revenue': 'TotalRevenue', 'ebit': 'OperatingIncome',
        'book_value': 'StockholdersEquity', 'capex': 'CapitalExpenditure',
        'd_and_a': 'ReconciledDepreciation', 'nwc': 'PPEOperatingNWC',
        'tax_rate': 'PPEEffectiveTaxRate', 'diluted_shares': 'DilutedAverageShares'}
    latest = packet['historical'][-1]['period_end']
    for end in ends:
        matches = [row for row in packet['historical']
            if abs((date.fromisoformat(row['period_end']) - date.fromisoformat(end)).days) <= 7]
        if len(matches) != 1:
            continue
        row = matches[0]
        fields = {target: row['fields'].get(source) for source, target in mapping.items()}
        if row['period_end'] == latest:
            fields.update({target: packet['bridge'].get(source) for source, target in {
                'short_term_debt': 'CurrentDebt', 'long_term_debt': 'LongTermDebt',
                'cash': 'CashAndCashEquivalents', 'preferred_equity': 'PreferredStockEquity',
                'minority_interest': 'MinorityInterest'}.items()})
            fields['InterestExpense'] = packet.get('interest_expense')
        fields['CommonStockDividendPaid'] = next((d for d in packet['dividends']
            if d['period_end'] == row['period_end']), None)
        fields['NetIncomeCommonStockholders'] = next((d for d in packet.get('common_income', [])
            if d['period_end'] == row['period_end']), None)
        for metric, field in fields.items():
            if field is not None and (end, metric) not in result:
                result[end, metric] = (field['value'], {
                    **field['provenance'], 'period_end': field['period_end'],
                    'available_at': field['available_at'], 'unit': field['unit'],
                    'value': field['value'], 'assembly_metric': metric,
                    'basis': 'Published PPE/SEC statement supplement'})
    return result
