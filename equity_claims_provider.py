"""Zion equity claims consumer for the existing DCF application.

Deliverable B. This module consumes the versioned Zion equity claims contract
(`zion-equity-claims-v1`) served by the Zion financial data worker, verifies its
release pin, member digest and every per-claim and per-source evidence digest, and
maps the verified claims into the enterprise-to-equity bridge that already exists in
`enterprise_valuation`. The enterprise valuation engine is neither duplicated nor
replaced: `enterprise_valuation.equity_bridge` remains the only place that turns an
enterprise value into common equity value.

Discipline borrowed from the native history consumer:
- nothing is fetched twice and no fallback source is substituted;
- a claim that is not in a certified evidence state is not used;
- a conflicting claim fails closed instead of being reconciled silently;
- verified-absent claims are documented zeros, and unknown claims stay unknown.
"""
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re

from enterprise_valuation import equity_bridge
from scripts.public_sec_equity_bridge import preferred_terms_scenarios

ADAPTER_VERSION = 'zion-equity-claims-v1'
CLAIMS_PATH = '/private/v1/equity-claims'
SERVICE_CALLER = 'dcf-valuation-engine'
CERTIFIED_STATES = ('REPORTED', 'DERIVED_VERIFIED', 'REVIEWED_ABSENT')
REQUIRED_CLAIMS = ('debt', 'finance_leases', 'operating_leases', 'cash', 'nonoperating_assets',
                   'preferred_equity', 'noncontrolling_interests', 'common_shares')
DEDUCT_CLAIMS = ('debt', 'finance_leases', 'preferred_equity', 'noncontrolling_interests')
ADD_CLAIMS = ('cash', 'nonoperating_assets')
NONCONTROLLING_POLICIES = ('DEDUCT_REPORTED', 'EXCLUDE_WITH_SENSITIVITY')
PREFERRED_SCENARIOS = ('AS_CONVERTED_MAX_RATE', 'AS_CONVERTED_MIN_RATE', 'LIQUIDATION_PREFERENCE')


class ProviderError(ValueError):
    """Raised when Zion equity claims cannot be used as verified bridge input."""


def fail(message):
    raise ProviderError('Zion equity claims: ' + message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def number(token, label):
    """Exact decimal from the contract; float round-tripping is never accepted."""
    if not isinstance(token, str) or not re.fullmatch(r'-?\d{1,80}(?:\.\d{1,40})?', token):
        fail('invalid exact decimal for ' + label)
    try:
        value = Decimal(token)
    except InvalidOperation:
        fail('invalid exact decimal for ' + label)
    if not value.is_finite():
        fail('nonfinite decimal for ' + label)
    return value


def verify_source(source, claim_name):
    """Recompute a source evidence digest from the fields it commits to."""
    if not isinstance(source, dict):
        fail('source record required for ' + claim_name)
    concept = source.get('concept')
    if not isinstance(concept, str) or ':' not in concept:
        fail('qualified concept required for ' + claim_name)
    taxonomy, _, tag = concept.partition(':')
    keys = ('concept', 'unit', 'reported_token', 'period_end', 'form', 'accession', 'filed')
    if any(key not in source for key in keys):
        fail('incomplete source evidence for ' + claim_name)
    expected = digest(dict({key: source[key] for key in keys}, taxonomy=taxonomy, concept_short=tag))
    if source.get('evidence_digest') != expected:
        fail('source evidence digest mismatch for ' + claim_name)
    if source.get('value_decimal') is not None:
        if number(source['value_decimal'], claim_name) != number(source['reported_token'], claim_name):
            fail('normalized value differs from the reported token for ' + claim_name)
    return expected


def verify_claim(claim, name):
    if not isinstance(claim, dict):
        fail('claim ' + name + ' is missing')
    if claim.get('evidence_state') not in CERTIFIED_STATES + ('ASSUMED', 'CONFLICTING', 'UNAVAILABLE'):
        fail('unknown evidence state for ' + name)
    body = {key: value for key, value in claim.items() if key != 'evidence_digest'}
    if claim.get('evidence_digest') != digest(body):
        fail('claim evidence digest mismatch for ' + name)
    for source in claim.get('sources') or []:
        verify_source(source, name)
    if claim['evidence_state'] in CERTIFIED_STATES:
        if claim.get('value_decimal') is None and claim['evidence_state'] != 'REVIEWED_ABSENT':
            fail('certified claim ' + name + ' has no value')
        if claim.get('value_decimal') is not None:
            amount = number(claim['value_decimal'], name)
            if claim['evidence_state'] == 'REVIEWED_ABSENT':
                fail('reviewed-absent claim ' + name + ' must not carry a value')
            if not claim.get('sources'):
                fail('claim ' + name + ' has no source evidence')
            if amount < 0 and name in ADD_CLAIMS:
                fail('nonoperating claim ' + name + ' is negative')
    return claim


def verify_claims(payload):
    """Verify a Zion equity claims response and return it with a normalized source block."""
    if not isinstance(payload, dict):
        fail('a JSON object response is required')
    if payload.get('schema_version') != ADAPTER_VERSION:
        fail('unsupported schema version ' + str(payload.get('schema_version')))
    if payload.get('rights') != 'PUBLIC_SEC_ONLY':
        fail('only the public SEC claims contract is supported')
    release = payload.get('release_id')
    member = payload.get('member_sha256')
    if not isinstance(release, str) or not re.fullmatch(r'[0-9a-f]{64}', release):
        fail('missing release identity')
    if not isinstance(member, str) or not re.fullmatch(r'[0-9a-f]{64}', member):
        fail('missing archive member identity')
    provenance = payload.get('provenance') or {}
    if provenance.get('source_lineage', {}).get('licensed_sources_used') is not False:
        fail('only public-SEC-only claims are supported')
    claims = payload.get('claims')
    if not isinstance(claims, dict):
        fail('claims block is required')
    for name in REQUIRED_CLAIMS:
        verify_claim(claims.get(name), name)
    _verify_aggregate(payload, claims)
    shares = claims['common_shares']
    if shares['evidence_state'] not in CERTIFIED_STATES or shares.get('value_decimal') is None:
        fail('a point-in-time common share count is required')
    if shares.get('basis') not in ('COVER_PAGE_DEI', 'BALANCE_SHEET_ALL_CLASSES'):
        fail('share count basis must be a point-in-time common share count')
    return dict(payload, source={
        'name': 'Zion filing-backed equity claims',
        'adapter_version': ADAPTER_VERSION,
        'release_id': release,
        'member_sha256': member,
        'registry_sha256': payload.get('registry_sha256'),
        'manifest_sha256': payload.get('manifest_sha256'),
        'valuation_date': payload.get('valuation_date'),
        'audit': payload.get('audit'),
        'certification': payload.get('certification'),
        'warnings': [
            'Claim evidence states are filing-derived; a scenario is not source-certified merely '
            'because its arithmetic reconciles.',
            'Offering terms supplied by a caller are ASSUMED, not XBRL verified.',
        ],
    })


def _verify_aggregate(payload, claims):
    aggregate = payload.get('aggregate_claims')
    if not isinstance(aggregate, dict):
        fail('aggregate claim block is required')
    missing, deduct, add, absent = [], Decimal(0), Decimal(0), []
    for name in DEDUCT_CLAIMS + ADD_CLAIMS:
        claim = claims[name]
        if claim.get('value_decimal') is None:
            if claim['evidence_state'] == 'REVIEWED_ABSENT':
                absent.append(name)
            else:
                missing.append(name)
        elif claim['evidence_state'] not in CERTIFIED_STATES or claim.get('permitted_for_valuation') is False:
            missing.append(name)
        else:
            amount = number(claim['value_decimal'], name)
            if name in DEDUCT_CLAIMS:
                deduct += amount
            else:
                add += amount
    if missing:
        if aggregate.get('status') != 'UNAVAILABLE' or sorted(missing) != sorted(aggregate.get('missing') or []):
            fail('aggregate claim block does not agree with the claims it summarizes')
        return
    if aggregate.get('status') != 'AVAILABLE':
        fail('aggregate claims are reported unavailable although every claim is certified')
    if number(aggregate['deduct_claims_decimal'], 'deduct aggregate') != deduct:
        fail('deduct aggregate does not equal the certified claims')
    if number(aggregate['add_claims_decimal'], 'add aggregate') != add:
        fail('add aggregate does not equal the certified claims')
    if sorted(absent) != sorted(aggregate.get('verified_absent') or []):
        fail('verified-absent claims do not agree with the aggregate block')


def claims_headers(*, token=None, service_token=None, caller=None):
    """Transport headers for either the private bearer or the scoped service credential."""
    if token:
        return {'Authorization': 'Bearer ' + token, 'User-Agent': 'Zion-DCF-EquityClaims/1'}
    if service_token and caller:
        if caller != SERVICE_CALLER:
            fail('internal service caller must be ' + SERVICE_CALLER)
        return {'x-zion-service-token': service_token, 'x-zion-service-caller': caller,
                'User-Agent': 'Zion-DCF-EquityClaims/1'}
    fail('a private bearer credential or an internal service credential is required')


def load_equity_claims(ticker, asof, http, *, cik, base, token=None, service_token=None,
                       caller=None, expected_release_id=None):
    """Fetch and verify the Zion equity claims contract for one filer.

    `http` is the caller's transport with a requests-compatible `get`, exactly as the
    native history consumer uses it, so the same local, service-binding or staging
    transport works here.
    """
    if not isinstance(cik, str) or not re.fullmatch(r'\d{10}', cik):
        fail('explicit ten-digit CIK required')
    if not isinstance(asof, str):
        fail('valuation date must be an ISO date string')
    asof_date = date.fromisoformat(asof)
    headers = claims_headers(token=token, service_token=service_token, caller=caller)
    params = dict(cik=cik, as_of=asof_date.isoformat(), recipient='human_research')
    if expected_release_id:
        params['expected_release_id'] = expected_release_id
    page = http.get(base.rstrip('/') + CLAIMS_PATH, headers=headers, params=dict(params))
    claims = verify_claims(page)
    if claims.get('valuation_date') != asof:
        fail('claims were extracted at a different valuation date')
    if claims.get('cik') != cik:
        fail('claims identity does not match the requested CIK')
    if expected_release_id and claims['source']['release_id'] != expected_release_id:
        fail('release mismatch; the pinned release was not served')
    claims['source'].update(ticker=ticker,
                            company_label=claims.get('company_label'),
                            identity_status='EXPLICIT_USER_CIK_NOT_TICKER_CERTIFIED')
    return claims


def claim_amount(claims, name, *, allow_verified_absent_as_zero=True):
    """Certified amount for one claim, or None when the claim cannot be used.

    A REVIEWED_ABSENT claim is a documented zero. A claim whose evidence state is not
    certified, or which is flagged as conflicting, is never converted into a number.
    """
    claim = claims['claims'][name]
    if claim['evidence_state'] in ('REVIEWED_ABSENT',):
        return 0.0 if allow_verified_absent_as_zero else None
    if claim['evidence_state'] not in CERTIFIED_STATES or claim.get('permitted_for_valuation') is False:
        return None
    if claim.get('value_decimal') is None:
        return None
    return float(number(claim['value_decimal'], name))


def unresolved_claims(claims):
    """Unresolved evidence that a consumer must report rather than hide."""
    blocking, advisory = [], []
    for name in REQUIRED_CLAIMS:
        claim = claims['claims'][name]
        if claim['evidence_state'] not in CERTIFIED_STATES:
            blocking.append(dict(claim=name, evidence_state=claim['evidence_state'],
                                 notes=claim.get('notes') or []))
        elif claim.get('permitted_for_valuation') is False:
            blocking.append(dict(claim=name, evidence_state=claim['evidence_state'],
                                 notes=claim.get('conflicts') or []))
    for name in ('operating_leases',):
        claim = claims['claims'][name]
        if claim.get('included_in_enterprise_bridge') is False:
            advisory.append(dict(claim=name, reason='CLASSIFIED_SEPARATELY_FROM_THE_BRIDGE'))
    return dict(blocking=blocking, advisory=advisory)


def bridge_inputs(claims, *, noncontrolling_policy='DEDUCT_REPORTED'):
    """Map verified claims onto the enterprise-to-equity bridge fields.

    Every field is explicit. A claim that cannot be certified makes the whole bridge
    unavailable instead of being replaced by a zero.
    """
    if noncontrolling_policy not in NONCONTROLLING_POLICIES:
        fail('unsupported noncontrolling policy ' + str(noncontrolling_policy))
    debt = claims['claims']['debt']
    leases = claims['claims']['finance_leases']
    cash = claim_amount(claims, 'cash')
    nonoperating = claim_amount(claims, 'nonoperating_assets')
    preferred = claim_amount(claims, 'preferred_equity')
    noncontrolling = claim_amount(claims, 'noncontrolling_interests')
    notes = []
    unavailable = []
    debt_current = debt.get('current_decimal')
    debt_noncurrent = debt.get('noncurrent_decimal')
    if claim_amount(claims, 'debt') is None:
        unavailable.append('debt')
    if claim_amount(claims, 'finance_leases') is None:
        unavailable.append('finance_leases')
    lease_amount = claim_amount(claims, 'finance_leases') or 0.0
    lease_current = leases.get('current_decimal')
    short_term = float(number(debt_current, 'current debt')) if debt_current else 0.0
    long_term = float(number(debt_noncurrent, 'noncurrent debt')) if debt_noncurrent else 0.0
    if leases['evidence_state'] == 'REVIEWED_ABSENT':
        notes.append('No finance lease liability is reported; verified absent, carried as zero.')
    elif lease_current is not None and leases.get('noncurrent_decimal') is not None:
        short_term += float(number(lease_current, 'current finance lease'))
        long_term += float(number(leases['noncurrent_decimal'], 'noncurrent finance lease'))
    else:
        long_term += lease_amount
        notes.append('The reported finance lease split is not part of the claims contract; the '
                     'lease claim is carried in long-term debt so the claim total is unchanged.')
    if debt_current is None and debt_noncurrent is None:
        long_term += float(number(debt['value_decimal'], 'debt')) if debt.get('value_decimal') else 0.0
        notes.append('The debt claim does not expose a current/noncurrent split; it is carried in '
                     'long-term debt so the claim total is unchanged.')
    other_nonoperating = None
    if cash is not None and nonoperating is not None:
        other_nonoperating = round(nonoperating - cash, 10)
        if other_nonoperating < 0:
            fail('nonoperating assets are smaller than cash; the claims contract is inconsistent')
    if noncontrolling_policy == 'EXCLUDE_WITH_SENSITIVITY' and noncontrolling is not None:
        notes.append('Reported noncontrolling interests are excluded from the primary bridge by an '
                     'explicit policy selection; they remain in the sensitivity.')
    bridge = dict(
        short_term_debt=short_term if 'debt' not in unavailable else None,
        long_term_debt=long_term if 'debt' not in unavailable else None,
        cash=cash,
        preferred_equity=preferred,
        minority_interest=(0.0 if noncontrolling_policy == 'EXCLUDE_WITH_SENSITIVITY' else noncontrolling),
        other_nonoperating_assets=other_nonoperating,
        as_of=claims.get('valuation_date'),
    )
    basis = {
        'debt': 'Interest-bearing borrowings only, excluding leases.',
        'finance_leases': 'Separate claim; carried with debt in the bridge schedule.',
        'cash': 'Cash and cash equivalents only.',
        'other_nonoperating_assets': 'Nonoperating assets less the cash already claimed.',
        'preferred_equity': 'Reported carrying value; replaceable by a conversion or liquidation scenario.',
        'minority_interest': 'Reported noncontrolling interests under policy ' + noncontrolling_policy + '.',
        'excluded': 'Operating leases and long-term investments are not bridge claims.',
    }
    return dict(bridge=bridge, notes=notes, basis=basis, unavailable=sorted(unavailable))


def _caller_dilution_terms(terms):
    """Offering terms supplied by the consumer, normalized the same way the contract does."""
    if not isinstance(terms, dict) or not isinstance(terms.get('series'), list) or not terms['series']:
        fail('malformed offering terms')
    preferred_shares, liquidation, minimum, maximum = Decimal(0), Decimal(0), Decimal(0), Decimal(0)
    for series in terms['series']:
        per_depositary = Decimal(str(series['depositary_per_preferred']))
        if per_depositary <= 0:
            fail('malformed offering terms')
        count = Decimal(str(series['depositary_shares'])) / per_depositary
        preferred_shares += count
        liquidation += count * Decimal(str(series['liquidation_preference_per_share']))
        minimum += count * Decimal(str(series['min_rate_per_preferred']))
        maximum += count * Decimal(str(series['max_rate_per_preferred']))
    return {
        'preferred_shares_decimal': format(preferred_shares.normalize(), 'f'),
        'liquidation_preference_total_decimal': format(liquidation.normalize(), 'f'),
        'min_converted_common_shares_decimal': format(minimum.normalize(), 'f'),
        'max_converted_common_shares_decimal': format(maximum.normalize(), 'f'),
        'terms': terms,
    }


def term_consistency(claims, terms):
    """The consumer's offering terms must agree with the claims contract's dilution terms."""
    reported = claims['claims']['preferred_equity'].get('dilution_terms')
    if not isinstance(reported, dict):
        return dict(status='NOT_COMPARABLE', detail='the claims contract carries no dilution terms')
    expected = preferred_terms_scenarios(terms, 0.0, dict(value=1.0))
    pairs = (
        ('preferred_shares_decimal', expected['preferred_shares']),
        ('liquidation_preference_total_decimal', expected['liquidation_preference_total']),
        ('max_converted_common_shares_decimal', expected['as_converted_max_rate']['shares_added']),
        ('min_converted_common_shares_decimal', expected['as_converted_min_rate']['shares_added']),
    )
    mismatches = []
    for key, value in pairs:
        if reported.get(key) is None:
            mismatches.append(dict(field=key, reason='MISSING_FROM_CLAIMS_CONTRACT'))
        else:
            # Decimal comparison only: the offering terms are exact decimals, so returning
            # CONFLICTING because of a binary float artifact would be a false alarm.
            contract = number(reported[key], key)
            consumer = Decimal(str(value)).normalize()
            if contract.normalize() != consumer:
                mismatches.append(dict(field=key, claims=reported[key], consumer=str(value)))
    return dict(status='CONSISTENT' if not mismatches else 'CONFLICTING', mismatches=mismatches)


def value_per_share(enterprise_value, claims, *, preferred_terms=None,
                    scenario='AS_CONVERTED_MAX_RATE', noncontrolling_policy='DEDUCT_REPORTED'):
    """Per-share common equity using the existing bridge, with preferred scenarios.

    The instrument is never counted twice: the as-converted scenarios deduct no
    preferred claim and add the converted shares, and the liquidation scenario deducts
    the preference and adds no shares.
    """
    if scenario not in PREFERRED_SCENARIOS:
        fail('unsupported preferred scenario ' + str(scenario))
    mapped = bridge_inputs(claims, noncontrolling_policy=noncontrolling_policy)
    shares = claim_amount(claims, 'common_shares', allow_verified_absent_as_zero=False)
    if shares is None:
        fail('a point-in-time common share count is required')
    preferred = claims['claims']['preferred_equity']
    carrying = claim_amount(claims, 'preferred_equity')
    scenarios, primary_bridge = {}, dict(mapped['bridge'])
    shares_basis = 'COMMON_SHARES_OUTSTANDING'
    terms = preferred.get('dilution_terms')
    if terms is None and preferred_terms is not None:
        # The contract carries no dilution terms for this filer; the caller's own documented
        # offering terms are used and remain labelled as an assumption.
        terms = dict(_caller_dilution_terms(preferred_terms),
                     evidence_state='ASSUMED',
                     basis='EXPLICIT_SELECTION_FROM_OFFERING_DOCUMENT;NOT_XBRL_VERIFIED')
    reported_liquidation = preferred.get('liquidation_preference_total_decimal')
    if reported_liquidation is None and preferred.get('liquidation_preference_per_share_decimal'):
        reported_liquidation = format(
            number(preferred['liquidation_preference_per_share_decimal'], 'liquidation preference')
            * number(preferred['shares_outstanding_decimal'], 'preferred shares'), 'f')
    if preferred['evidence_state'] == 'REVIEWED_ABSENT' or (carrying == 0.0 and preferred.get('shares_outstanding_decimal') in (None, '0')):
        # A verified-absent claim or a reported zero carrying amount with no shares outstanding:
        # there is no preferred instrument to convert or to deduct.
        scenarios = {'NO_PREFERRED_OUTSTANDING': dict(claim=0.0, shares_added=0.0)}
    elif terms is None:
        scenarios = {'LIQUIDATION_PREFERENCE': dict(claim=float(number(reported_liquidation, 'liquidation preference'))
                                                    if reported_liquidation else carrying,
                                                    shares_added=0.0)}
    else:
        consumer = preferred_terms_scenarios(terms['terms'], 0.0, dict(value=float(shares)))
        scenarios = {
            'AS_CONVERTED_MAX_RATE': dict(claim=0.0, shares_added=consumer['as_converted_max_rate']['shares_added'],
                                          contract_decimal=terms.get('max_converted_common_shares_decimal')),
            'AS_CONVERTED_MIN_RATE': dict(claim=0.0, shares_added=consumer['as_converted_min_rate']['shares_added'],
                                          contract_decimal=terms.get('min_converted_common_shares_decimal')),
            'LIQUIDATION_PREFERENCE': dict(claim=float(number(reported_liquidation, 'liquidation preference'))
                                           if reported_liquidation else float(consumer['liquidation_preference_total']),
                                           shares_added=0.0),
        }
    applied = scenario if scenario in scenarios else None
    if applied is None and len(scenarios) == 1:
        # A filer with no preferred claim has one meaningful scenario; report it as applied
        # rather than echoing a requested scenario that was not used.
        applied = next(iter(scenarios))
    notes = list(mapped['notes'])
    if applied != scenario:
        notes.append('Requested preferred scenario ' + scenario + ' is not available for this filer; '
                     + ('applied ' + applied if applied else 'the carrying-value bridge is reported'))
    if applied is not None:
        primary_bridge['preferred_equity'] = scenarios[applied]['claim']
        shares_added = scenarios[applied]['shares_added']
    else:
        shares_added = 0.0
    results = {}
    for name, values in scenarios.items():
        bridge = dict(mapped['bridge'])
        bridge['preferred_equity'] = values['claim']
        outcome = equity_bridge(bridge, enterprise_value,
                                shares_outstanding=float(shares) + values['shares_added'],
                                shares_basis=shares_basis)
        results[name] = dict(claim=values['claim'], shares_added=values['shares_added'],
                             shares_outstanding=float(shares) + values['shares_added'],
                             status=outcome['status'], equity_value=outcome['equity_value'],
                             value_per_share=outcome['value_per_share'], missing=outcome['missing'])
    primary = equity_bridge(primary_bridge, enterprise_value,
                            shares_outstanding=float(shares) + shares_added,
                            shares_basis=shares_basis)
    unresolved = unresolved_claims(claims)
    return dict(
        schema_version='zion-equity-bridge-v1',
        ticker=claims['source'].get('ticker'), valuation_date=claims.get('valuation_date'),
        enterprise_value=enterprise_value, primary_scenario=applied or 'UNAVAILABLE',
        requested_scenario=scenario, scenario_notes=notes,
        primary=dict(status=primary['status'], equity_value=primary['equity_value'],
                     value_per_share=primary['value_per_share'], missing=primary['missing']),
        scenarios=results, bridge=primary_bridge, bridge_inputs=dict(mapped['bridge']),
        bridge_basis=mapped['basis'], bridge_notes=notes,
        shares_outstanding=float(shares), shares_basis=shares_basis,
        noncontrolling_policy=noncontrolling_policy,
        preferred_evidence_state=preferred['evidence_state'],
        unresolved=unresolved,
        assumptions=[
            'Preferred conversion is conditional on the filed terms; the as-converted scenario is a '
            'sensitivity, not a certified outcome.',
            'Operating leases are excluded because EBIT is after operating lease cost.',
            'Noncontrolling interests are deducted once from the consolidated enterprise value.',
        ],
        source=claims['source'],
    )
