"""Tests for the Zion equity claims consumer.

Payloads are valid by construction: every claim and source digest is computed with the
same canonical JSON encoding the provider verifies, so a rejection test can reseal a
mutation and prove that the *semantics* are what fails closed rather than a stale hash.
"""
import copy
from decimal import Decimal
import hashlib
import json

import pytest

from enterprise_valuation import equity_bridge
from equity_claims_provider import (
    ADAPTER_VERSION,
    CLAIMS_PATH,
    DEDUCT_CLAIMS,
    ADD_CLAIMS,
    NONCONTROLLING_POLICIES,
    REQUIRED_CLAIMS,
    SERVICE_CALLER,
    ProviderError,
    bridge_inputs,
    claim_amount,
    claims_headers,
    load_equity_claims,
    term_consistency,
    unresolved_claims,
    value_per_share,
    verify_claims,
)

ASOF = '2026-10-14'
CIK = '0001652044'
RELEASE = 'a' * 64
MEMBER = 'b' * 64


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def dec(value):
    return format(Decimal(str(value)).normalize(), 'f')


def source(concept='us-gaap:LongTermDebtNoncurrent', value='600', unit='USD',
           period_end='2026-06-30', form='10-Q', accession='0001652044-26-000071',
           filed='2026-07-23'):
    taxonomy, _, tag = concept.partition(':')
    body = dict(concept=concept, unit=unit, reported_token=value, period_end=period_end,
                form=form, accession=accession, filed=filed)
    record = dict(body, value_decimal=value, available_at=filed,
                  availability_granularity='FILING_DATE_ONLY')
    record['evidence_digest'] = digest(dict(body, taxonomy=taxonomy, concept_short=tag))
    return record


def claim(value, state='REPORTED', unit='USD', sources=None, extra=None, notes=None,
          measure='measure', selection_rule='rule'):
    sources = list(sources) if sources is not None else (
        [] if value is None else [source(value=value)])
    body = {
        'value_decimal': value,
        'unit': unit,
        'evidence_state': state,
        'measure': measure,
        'selection_rule': selection_rule,
        'period_end': sources[0]['period_end'] if sources else None,
        'available_at': sources[0]['available_at'] if sources else None,
        'availability_granularity': 'FILING_DATE_ONLY',
        'sources': sources,
        'notes': list(notes or []),
    }
    if extra:
        body.update(extra)
    return reseal(body)


def reseal(record):
    record.pop('evidence_digest', None)
    record['evidence_digest'] = digest(record)
    return record


def aggregate_for(claims, *, status=None, deduct=None, add=None, missing=None, absent=None):
    computed_missing, computed_deduct, computed_add, computed_absent = [], Decimal(0), Decimal(0), []
    for name in DEDUCT_CLAIMS + ADD_CLAIMS:
        item = claims.get(name)
        if item is None:
            computed_missing.append(name)
            continue
        if item['value_decimal'] is None:
            if item['evidence_state'] == 'REVIEWED_ABSENT':
                computed_absent.append(name)
            else:
                computed_missing.append(name)
        elif item['evidence_state'] not in ('REPORTED', 'DERIVED_VERIFIED', 'REVIEWED_ABSENT') \
                or item.get('permitted_for_valuation') is False:
            computed_missing.append(name)
        else:
            amount = Decimal(item['value_decimal'])
            if name in DEDUCT_CLAIMS:
                computed_deduct += amount
            else:
                computed_add += amount
    if missing is not None or computed_missing:
        return {'status': status or 'UNAVAILABLE',
                'missing': sorted(computed_missing if missing is None else missing),
                'verified_absent': sorted(absent if absent is not None else computed_absent)}
    return {'status': status or 'AVAILABLE',
            'deduct_claims_decimal': dec(computed_deduct if deduct is None else deduct),
            'add_claims_decimal': dec(computed_add if add is None else add),
            'verified_absent': sorted(absent if absent is not None else computed_absent)}


def base_claims():
    return {
        'debt': claim('1000', extra={'current_decimal': '400', 'noncurrent_decimal': '600'}, sources=[
            source(concept='us-gaap:LongTermDebtCurrent', value='400'),
            source(concept='us-gaap:LongTermDebtNoncurrent', value='600')]),
        'finance_leases': claim('100', extra={'current_decimal': '30', 'noncurrent_decimal': '70'}, sources=[
            source(concept='us-gaap:FinanceLeaseLiabilityCurrent', value='30'),
            source(concept='us-gaap:FinanceLeaseLiabilityNoncurrent', value='70')]),
        'operating_leases': claim('500', extra={'included_in_enterprise_bridge': False},
                                  sources=[source(concept='us-gaap:OperatingLeaseLiability', value='500')]),
        'cash': claim('200', sources=[source(concept='us-gaap:CashAndCashEquivalentsAtCarryingValue', value='200')]),
        'nonoperating_assets': claim('700', sources=[
            source(concept='us-gaap:CashAndCashEquivalentsAtCarryingValue', value='200'),
            source(concept='us-gaap:MarketableSecuritiesCurrent', value='500')]),
        'preferred_equity': claim(None, state='REVIEWED_ABSENT', notes=['no preferred equity reported']),
        'noncontrolling_interests': claim('50', extra={'deduction_permitted': True,
                                                       'treatment': 'DEDUCT_FROM_CONSOLIDATED_ENTERPRISE_VALUE'},
                                          sources=[source(concept='us-gaap:NoncontrollingInterestInVariableInterestEntity',
                                                          value='50')]),
        'common_shares': claim('1000', unit='shares',
                               extra={'basis': 'BALANCE_SHEET_ALL_CLASSES', 'dated_observations': []},
                               sources=[source(concept='us-gaap:CommonStockSharesOutstanding', value='1000',
                                               unit='shares')]),
    }


def payload(claims=None, **overrides):
    claims = base_claims() if claims is None else claims
    root = {
        'schema_version': ADAPTER_VERSION,
        'rights': 'PUBLIC_SEC_ONLY',
        'release_id': RELEASE,
        'member_sha256': MEMBER,
        'registry_sha256': 'c' * 64,
        'manifest_sha256': 'd' * 64,
        'cik': CIK,
        'valuation_date': ASOF,
        'company_label': 'Alphabet Inc.',
        'claims': claims,
        'aggregate_claims': aggregate_for(claims),
        'provenance': {'source_lineage': {'rights': 'PUBLIC_SEC_ONLY', 'licensed_sources_used': False}},
        'audit': {'authenticated_via': 'BEARER'},
        'certification': 'FILING_BACKED_CLAIMS;NOT_A_MARKET_OR_ACCOUNTING_ATTESTATION',
    }
    root.update(overrides)
    return root


GOOGL_TERMS = {'series': [
    dict(name='A', depositary_shares=192_500_000, depositary_per_preferred=20,
         liquidation_preference_per_share=1000, min_rate_per_preferred=2.2520,
         max_rate_per_preferred=2.8160),
    dict(name='B', depositary_shares=192_500_000, depositary_per_preferred=20,
         liquidation_preference_per_share=1000, min_rate_per_preferred=2.2740,
         max_rate_per_preferred=2.8420),
]}
MAX_ADDED = 9_625_000 * 2.8160 + 9_625_000 * 2.8420
MIN_ADDED = 9_625_000 * 2.2520 + 9_625_000 * 2.2740


def preferred_with_terms(terms=GOOGL_TERMS, carrying='18023', liquidation='19000000000'):
    from scripts.public_sec_equity_bridge import preferred_terms_scenarios
    scenarios = preferred_terms_scenarios(terms, 0.0, dict(value=1.0))
    return claim(
        carrying,
        extra={
            'carrying_value_decimal': carrying,
            'shares_outstanding_decimal': '19000000',
            'liquidation_preference_per_share_decimal': '1000',
            'liquidation_preference_total_decimal': liquidation,
            'dividend_rate_decimal': '0.0625',
            'conflicts': [],
            'dilution_terms': {
                'preferred_shares_decimal': dec(scenarios['preferred_shares']),
                'liquidation_preference_total_decimal': dec(scenarios['liquidation_preference_total']),
                'min_converted_common_shares_decimal': dec(scenarios['as_converted_min_rate']['shares_added']),
                'max_converted_common_shares_decimal': dec(scenarios['as_converted_max_rate']['shares_added']),
                'evidence_state': 'ASSUMED',
                'basis': 'EXPLICIT_SELECTION_FROM_OFFERING_DOCUMENT;NOT_XBRL_VERIFIED',
                'permitted_for_valuation': True,
                'terms': terms,
            },
        },
        sources=[source(concept='us-gaap:ConvertiblePreferredStockNonredeemableOrRedeemableIssuerOptionValue',
                        value=carrying),
                 source(concept='us-gaap:PreferredStockLiquidationPreference', value='1000',
                        unit='USD/shares')],
    )


def test_valid_payload_verifies_and_carries_its_release_identity():
    verified = verify_claims(payload())
    assert verified['source']['adapter_version'] == ADAPTER_VERSION
    assert verified['source']['release_id'] == RELEASE
    assert verified['source']['member_sha256'] == MEMBER
    assert verified['source']['registry_sha256'] == 'c' * 64
    assert verified['source']['valuation_date'] == ASOF
    assert verified['source']['audit'] == {'authenticated_via': 'BEARER'}
    assert verified['source']['warnings']


def test_tampered_claim_value_source_token_or_state_fails_closed():
    tampered = payload()
    tampered['claims']['cash']['value_decimal'] = '999'
    with pytest.raises(ProviderError, match='claim evidence digest mismatch for cash'):
        verify_claims(tampered)

    tampered = payload()
    tampered['claims']['cash']['sources'][0]['reported_token'] = '999'
    reseal(tampered['claims']['cash'])
    with pytest.raises(ProviderError, match='source evidence digest mismatch for cash'):
        verify_claims(tampered)

    tampered = payload()
    tampered['claims']['cash']['evidence_state'] = 'CONFLICTING'
    with pytest.raises(ProviderError, match='claim evidence digest mismatch for cash'):
        verify_claims(tampered)

    tampered = payload()
    tampered['claims']['cash']['sources'][0]['value_decimal'] = '201'
    reseal(tampered['claims']['cash'])
    with pytest.raises(ProviderError, match='normalized value differs from the reported token'):
        verify_claims(tampered)

    tampered = payload()
    tampered['claims']['cash']['sources'][0]['form'] = '8-K'
    reseal(tampered['claims']['cash'])
    with pytest.raises(ProviderError, match='source evidence digest mismatch for cash'):
        verify_claims(tampered)


@pytest.mark.parametrize('mutation,message', [
    ('schema', 'unsupported schema version'),
    ('rights', 'only the public SEC claims contract is supported'),
    ('release', 'missing release identity'),
    ('member', 'missing archive member identity'),
    ('licensed', 'only public-SEC-only claims are supported'),
    ('missing_claim', 'claim cash is missing'),
    ('no_value', 'certified claim cash has no value'),
    ('no_sources', 'claim cash has no source evidence'),
    ('absent_with_value', 'reviewed-absent claim preferred_equity must not carry a value'),
    ('negative_add', 'nonoperating claim nonoperating_assets is negative'),
    ('share_basis', 'share count basis must be a point-in-time common share count'),
])
def test_invalid_payloads_are_rejected(mutation, message):
    broken = payload()
    if mutation == 'schema':
        broken['schema_version'] = 'zion-equity-claims-v2'
    elif mutation == 'rights':
        broken['rights'] = 'LICENSED_SOURCES_ALLOWED'
    elif mutation == 'release':
        broken['release_id'] = 'not-a-hash'
    elif mutation == 'member':
        broken['member_sha256'] = None
    elif mutation == 'licensed':
        broken['provenance']['source_lineage']['licensed_sources_used'] = True
    elif mutation == 'missing_claim':
        del broken['claims']['cash']
    elif mutation == 'no_value':
        broken['claims']['cash'] = reseal(dict(broken['claims']['cash'], value_decimal=None))
    elif mutation == 'no_sources':
        broken['claims']['cash'] = reseal(dict(broken['claims']['cash'], sources=[]))
    elif mutation == 'absent_with_value':
        broken['claims']['preferred_equity'] = reseal(
            dict(broken['claims']['preferred_equity'], value_decimal='5'))
    elif mutation == 'negative_add':
        broken['claims']['nonoperating_assets'] = reseal(
            dict(broken['claims']['nonoperating_assets'], value_decimal='-5'))
    elif mutation == 'share_basis':
        broken['claims']['common_shares'] = reseal(
            dict(broken['claims']['common_shares'], basis='WEIGHTED_AVERAGE_DILUTED_SHARES'))
    broken['aggregate_claims'] = aggregate_for(broken['claims'])
    with pytest.raises(ProviderError, match=message):
        verify_claims(broken)


def test_aggregate_block_must_agree_with_the_claims_it_summarizes():
    broken = payload()
    broken['aggregate_claims']['deduct_claims_decimal'] = '999'
    with pytest.raises(ProviderError, match='deduct aggregate does not equal the certified claims'):
        verify_claims(broken)

    broken = payload()
    broken['aggregate_claims']['verified_absent'] = []
    with pytest.raises(ProviderError, match='verified-absent claims do not agree'):
        verify_claims(broken)

    broken = payload()
    broken['claims']['debt'] = reseal(dict(broken['claims']['debt'], evidence_state='CONFLICTING'))
    with pytest.raises(ProviderError, match='aggregate claim block does not agree'):
        verify_claims(broken)

    consistent = payload()
    consistent['claims']['debt'] = reseal(dict(consistent['claims']['debt'], evidence_state='CONFLICTING'))
    consistent['aggregate_claims'] = aggregate_for(consistent['claims'])
    assert consistent['aggregate_claims']['status'] == 'UNAVAILABLE'
    assert consistent['aggregate_claims']['missing'] == ['debt']
    verify_claims(consistent)


def test_claim_amount_distinguishes_verified_absent_from_unknown():
    claims = payload()
    assert claim_amount(claims, 'preferred_equity') == 0.0
    assert claim_amount(claims, 'preferred_equity', allow_verified_absent_as_zero=False) is None
    assert claim_amount(claims, 'cash') == 200.0

    claims['claims']['debt'] = reseal(dict(claims['claims']['debt'], evidence_state='UNAVAILABLE',
                                           value_decimal=None))
    assert claim_amount(claims, 'debt') is None

    claims['claims']['noncontrolling_interests'] = reseal(
        dict(claims['claims']['noncontrolling_interests'], permitted_for_valuation=False))
    assert claim_amount(claims, 'noncontrolling_interests') is None


def test_bridge_inputs_carry_debt_and_leases_without_changing_the_claim_total():
    mapped = bridge_inputs(payload())
    assert mapped['bridge']['short_term_debt'] == 430.0
    assert mapped['bridge']['long_term_debt'] == 670.0
    assert mapped['bridge']['short_term_debt'] + mapped['bridge']['long_term_debt'] == \
        claim_amount(payload(), 'debt') + claim_amount(payload(), 'finance_leases')
    assert mapped['bridge']['cash'] == 200.0
    assert mapped['bridge']['other_nonoperating_assets'] == 500.0
    assert mapped['bridge']['preferred_equity'] == 0.0
    assert mapped['bridge']['minority_interest'] == 50.0
    assert mapped['bridge']['as_of'] == ASOF
    assert mapped['basis']['debt'].startswith('Interest-bearing borrowings only')
    assert mapped['unavailable'] == []

    unsplit_lease = payload()
    unsplit_lease['claims']['finance_leases'] = claim(
        '100', sources=[source(concept='us-gaap:FinanceLeaseLiability', value='100')])
    unsplit_lease['aggregate_claims'] = aggregate_for(unsplit_lease['claims'])
    mapped = bridge_inputs(unsplit_lease)
    assert mapped['bridge']['short_term_debt'] == 400.0
    assert mapped['bridge']['long_term_debt'] == 700.0
    assert any('split is not part of the claims contract' in note for note in mapped['notes'])

    unsplit_debt = payload()
    unsplit_debt['claims']['debt'] = claim('1000', sources=[
        source(concept='us-gaap:LongTermDebt', value='1000')])
    unsplit_debt['aggregate_claims'] = aggregate_for(unsplit_debt['claims'])
    mapped = bridge_inputs(unsplit_debt)
    assert mapped['bridge']['short_term_debt'] == 30.0
    assert mapped['bridge']['long_term_debt'] == 1000.0 + 70.0
    assert any('does not expose a current/noncurrent split' in note for note in mapped['notes'])


def test_bridge_inputs_applies_the_noncontrolling_policy_explicitly():
    deducted = bridge_inputs(payload())
    assert deducted['bridge']['minority_interest'] == 50.0

    excluded = bridge_inputs(payload(), noncontrolling_policy='EXCLUDE_WITH_SENSITIVITY')
    assert excluded['bridge']['minority_interest'] == 0.0
    assert any('excluded from the primary bridge by an explicit policy selection' in note
               for note in excluded['notes'])
    assert 'EXCLUDE_WITH_SENSITIVITY' in excluded['basis']['minority_interest']
    assert set(NONCONTROLLING_POLICIES) == {'DEDUCT_REPORTED', 'EXCLUDE_WITH_SENSITIVITY'}

    with pytest.raises(ProviderError, match='unsupported noncontrolling policy'):
        bridge_inputs(payload(), noncontrolling_policy='IGNORE')


def test_uncertifiable_debt_is_reported_unavailable_and_never_zeroed():
    claims = payload()
    claims['claims']['debt'] = reseal(dict(claims['claims']['debt'], evidence_state='CONFLICTING'))
    claims['aggregate_claims'] = aggregate_for(claims['claims'])
    mapped = bridge_inputs(claims)
    assert mapped['bridge']['short_term_debt'] is None
    assert mapped['bridge']['long_term_debt'] is None
    assert mapped['unavailable'] == ['debt']


def test_preferred_scenarios_never_count_the_instrument_twice():
    claims = payload()
    claims['claims']['preferred_equity'] = preferred_with_terms()
    claims['aggregate_claims'] = aggregate_for(claims['claims'])
    verified = verify_claims(claims)

    result = value_per_share(1_000_000.0, verified, preferred_terms=GOOGL_TERMS,
                             scenario='AS_CONVERTED_MAX_RATE')
    assert result['primary_scenario'] == 'AS_CONVERTED_MAX_RATE'
    assert set(result['scenarios']) == {'AS_CONVERTED_MAX_RATE', 'AS_CONVERTED_MIN_RATE',
                                        'LIQUIDATION_PREFERENCE'}
    assert result['scenarios']['AS_CONVERTED_MAX_RATE']['claim'] == 0.0
    assert result['scenarios']['AS_CONVERTED_MAX_RATE']['shares_added'] == pytest.approx(MAX_ADDED)
    assert result['scenarios']['AS_CONVERTED_MIN_RATE']['shares_added'] == pytest.approx(MIN_ADDED)
    assert result['scenarios']['LIQUIDATION_PREFERENCE']['shares_added'] == 0.0
    assert result['scenarios']['LIQUIDATION_PREFERENCE']['claim'] == pytest.approx(19_000_000_000.0)
    assert result['shares_basis'] == 'COMMON_SHARES_OUTSTANDING'
    assert result['shares_outstanding'] == 1000.0
    assert result['preferred_evidence_state'] == 'REPORTED'

    as_converted = dict(result['bridge_inputs'], preferred_equity=0.0)
    expected = equity_bridge(as_converted, 1_000_000.0,
                             shares_outstanding=1000.0 + MAX_ADDED,
                             shares_basis='COMMON_SHARES_OUTSTANDING')
    assert result['primary']['value_per_share'] == pytest.approx(expected['value_per_share'])
    assert result['primary']['equity_value'] == pytest.approx(expected['equity_value'])
    assert result['primary']['status'] == 'AVAILABLE'

    liquidation = equity_bridge(dict(result['bridge_inputs'], preferred_equity=19_000_000_000.0),
                                1_000_000.0, shares_outstanding=1000.0,
                                shares_basis='COMMON_SHARES_OUTSTANDING')
    assert result['scenarios']['LIQUIDATION_PREFERENCE']['value_per_share'] == \
        pytest.approx(liquidation['value_per_share'])
    assert result['scenarios']['AS_CONVERTED_MAX_RATE']['value_per_share'] > \
        result['scenarios']['LIQUIDATION_PREFERENCE']['value_per_share']


def test_preferred_without_terms_uses_the_reported_preference():
    claims = payload()
    claims['claims']['preferred_equity'] = claim(
        '18023',
        extra={'carrying_value_decimal': '18023',
               'liquidation_preference_per_share_decimal': '1000',
               'shares_outstanding_decimal': '19000000',
               'liquidation_preference_total_decimal': '19000000000',
               'conflicts': []},
        sources=[source(concept='us-gaap:ConvertiblePreferredStockNonredeemableOrRedeemableIssuerOptionValue',
                        value='18023')])
    claims['aggregate_claims'] = aggregate_for(claims['claims'])
    result = value_per_share(1_000_000.0, verify_claims(claims), scenario='LIQUIDATION_PREFERENCE')
    assert set(result['scenarios']) == {'LIQUIDATION_PREFERENCE'}
    assert result['scenarios']['LIQUIDATION_PREFERENCE']['claim'] == pytest.approx(19_000_000_000.0)
    assert result['scenarios']['LIQUIDATION_PREFERENCE']['shares_added'] == 0.0

    derived = payload()
    derived['claims']['preferred_equity'] = claim(
        '18023',
        extra={'liquidation_preference_per_share_decimal': '1000',
               'liquidation_preference_total_decimal': None,
               'shares_outstanding_decimal': '19000000'},
        sources=[source(concept='us-gaap:ConvertiblePreferredStockNonredeemableOrRedeemableIssuerOptionValue',
                        value='18023')])
    derived['aggregate_claims'] = aggregate_for(derived['claims'])
    result = value_per_share(1_000_000.0, verify_claims(derived), scenario='LIQUIDATION_PREFERENCE')
    assert result['scenarios']['LIQUIDATION_PREFERENCE']['claim'] == pytest.approx(19_000_000_000.0)


def test_verified_absent_preferred_deducts_nothing_and_adds_no_shares():
    result = value_per_share(1_000_000.0, verify_claims(payload()))
    assert set(result['scenarios']) == {'NO_PREFERRED_OUTSTANDING'}
    assert result['scenarios']['NO_PREFERRED_OUTSTANDING']['claim'] == 0.0
    assert result['scenarios']['NO_PREFERRED_OUTSTANDING']['shares_added'] == 0.0
    expected = equity_bridge(result['bridge_inputs'], 1_000_000.0, shares_outstanding=1000.0,
                             shares_basis='COMMON_SHARES_OUTSTANDING')
    assert result['primary']['value_per_share'] == pytest.approx(expected['value_per_share'])


def test_term_consistency_must_agree_with_the_claims_contract():
    claims = payload()
    claims['claims']['preferred_equity'] = preferred_with_terms()
    claims['aggregate_claims'] = aggregate_for(claims['claims'])
    verified = verify_claims(claims)
    assert term_consistency(verified, GOOGL_TERMS) == {'status': 'CONSISTENT', 'mismatches': []}

    other = copy.deepcopy(GOOGL_TERMS)
    other['series'][0]['max_rate_per_preferred'] = 2.5
    verdict = term_consistency(verified, other)
    assert verdict['status'] == 'CONFLICTING'
    assert any(item['field'] == 'max_converted_common_shares_decimal'
               for item in verdict['mismatches'])

    none = term_consistency(verify_claims(payload()), GOOGL_TERMS)
    assert none['status'] == 'NOT_COMPARABLE'


def test_conflicting_claims_stay_visible_and_block_the_valuation():
    claims = payload()
    claims['claims']['noncontrolling_interests'] = reseal(
        dict(claims['claims']['noncontrolling_interests'], evidence_state='CONFLICTING',
             permitted_for_valuation=False, conflicts=['reported measures disagree'],
             value_decimal='7100'))
    claims['aggregate_claims'] = aggregate_for(claims['claims'])
    verified = verify_claims(claims)
    unresolved = unresolved_claims(verified)
    assert [item['claim'] for item in unresolved['blocking']] == ['noncontrolling_interests']
    assert unresolved['advisory'] == [{'claim': 'operating_leases',
                                       'reason': 'CLASSIFIED_SEPARATELY_FROM_THE_BRIDGE'}]

    result = value_per_share(1_000_000.0, verified)
    assert result['primary']['status'] == 'UNAVAILABLE'
    assert result['primary']['value_per_share'] is None
    assert 'minority_interest' in result['primary']['missing']
    assert result['unresolved']['blocking']


class FakeHttp:
    def __init__(self, page):
        self.page = page
        self.calls = []

    def get(self, url, headers=None, params=None):
        self.calls.append(dict(url=url, headers=headers, params=params))
        return self.page


def test_load_equity_claims_uses_the_scoped_transport_and_pins_the_served_identity():
    http = FakeHttp(payload())
    loaded = load_equity_claims('GOOGL', ASOF, http, cik=CIK, base='https://zion.example/',
                                token='owned-token')
    assert http.calls[0]['url'] == 'https://zion.example' + CLAIMS_PATH
    assert http.calls[0]['headers']['Authorization'] == 'Bearer owned-token'
    assert http.calls[0]['params'] == {'cik': CIK, 'as_of': ASOF, 'recipient': 'human_research'}
    assert loaded['source']['ticker'] == 'GOOGL'
    assert loaded['source']['company_label'] == 'Alphabet Inc.'
    assert loaded['source']['identity_status'] == 'EXPLICIT_USER_CIK_NOT_TICKER_CERTIFIED'

    service = FakeHttp(payload())
    load_equity_claims('GOOGL', ASOF, service, cik=CIK, base='https://zion.example',
                       service_token='internal-token', caller=SERVICE_CALLER,
                       expected_release_id=RELEASE)
    assert service.calls[0]['headers']['x-zion-service-token'] == 'internal-token'
    assert service.calls[0]['headers']['x-zion-service-caller'] == SERVICE_CALLER
    assert service.calls[0]['params']['expected_release_id'] == RELEASE

    assert claims_headers(token='t')['Authorization'] == 'Bearer t'
    assert claims_headers(service_token='s', caller=SERVICE_CALLER)['x-zion-service-caller'] == SERVICE_CALLER
    with pytest.raises(ProviderError, match='internal service caller must be'):
        claims_headers(service_token='s', caller='some-other-worker')
    with pytest.raises(ProviderError, match='a private bearer credential or an internal service credential'):
        claims_headers()


def test_load_equity_claims_fails_closed_on_identity_mismatch():
    with pytest.raises(ProviderError, match='different valuation date'):
        load_equity_claims('GOOGL', ASOF, FakeHttp(payload(valuation_date='2026-10-13')),
                           cik=CIK, base='https://zion.example', token='t')

    with pytest.raises(ProviderError, match='does not match the requested CIK'):
        load_equity_claims('GOOGL', ASOF, FakeHttp(payload(cik='0000320193')),
                           cik=CIK, base='https://zion.example', token='t')

    with pytest.raises(ProviderError, match='release mismatch'):
        load_equity_claims('GOOGL', ASOF, FakeHttp(payload()), cik=CIK,
                           base='https://zion.example', token='t', expected_release_id='f' * 64)

    with pytest.raises(ProviderError, match='explicit ten-digit CIK required'):
        load_equity_claims('GOOGL', ASOF, FakeHttp(payload()), cik='1652044',
                           base='https://zion.example', token='t')

    with pytest.raises(ProviderError, match='a private bearer credential or an internal service credential'):
        load_equity_claims('GOOGL', ASOF, FakeHttp(payload()), cik=CIK, base='https://zion.example')
