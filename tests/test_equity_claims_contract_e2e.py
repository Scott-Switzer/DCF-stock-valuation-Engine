"""Real, source-backed cross-repo contract test for the Zion equity claims milestone.

This file runs the upstream Zion claims extraction (`equity_claims.build_claims`) over
the actual SEC Company Facts documents downloaded for Alphabet, Apple and Microsoft,
wraps the result exactly the way the Zion route does, and drives the DCF-side consumer
(`equity_claims_provider`) with it. It fails if the producer's evidence digests and the
consumer's recomputation ever disagree.

Every expected value below is the reported filing value for the 2026 valuation date.
The source concept is named in a comment wherever a constant is asserted.
"""
import asyncio
import contextlib
from datetime import date
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlencode

import pytest

ROOT = Path(__file__).resolve().parents[1]
ZION_SRC = Path('/Users/scottthomasswitzer/Documents/zion-valuation-service/deploy/cloudflare-query/src')
FACTS = ROOT / 'artifacts/zero-subscription-integration/companyfacts'

if not (ZION_SRC / 'equity_claims.py').exists() or not (FACTS / '0001652044.json').exists():
    pytest.skip('Zion checkout or downloaded SEC company facts are not present', allow_module_level=True)

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ZION_SRC))

from equity_claims import VERSION, build_claims  # noqa: E402
from equity_claims_provider import (  # noqa: E402
    ProviderError,
    SERVICE_CALLER,
    load_equity_claims,
    term_consistency,
    value_per_share,
    verify_claims,
)
import zion_equity_claims_service as zion_service  # noqa: E402
# The service module translates every claims-contract failure into the transport error
# the DCF app already maps to HTTP 503, so the refusal tests assert on that type.
from dcf_loader import ProviderError as ServiceError  # noqa: E402


@pytest.fixture(autouse=True)
def scoped_service_credential(monkeypatch):
    """The staging-scoped credential this deployment is configured with."""
    monkeypatch.setenv('ZION_SERVICE_TOKEN', 'scoped-service-token')
    monkeypatch.delenv('ZION_EQUITY_CLAIMS_CALLER', raising=False)

ASOF = date(2026, 10, 14)
ASOF_TEXT = '2026-10-14'
RELEASE = 'b' * 64
MEMBER = 'c' * 64
# CIK 0001045810 is NVIDIA CORP, not Microsoft. Microsoft is CIK 0000789019; the identity is
# asserted against the downloaded document below so a mislabelled file can never pass silently.
GOOGL, AAPL, MSFT = '0001652044', '0000320193', '0000789019'

# Offering terms are a caller-supplied document selection, never an XBRL fact. They match
# the terms already used by tests/test_public_sec_equity_bridge.py.
TERMS = {'series': [
    {'name': 'A', 'depositary_shares': 192_500_000, 'depositary_per_preferred': 20,
     'liquidation_preference_per_share': 1000,
     'min_rate_per_preferred': 2.2520, 'max_rate_per_preferred': 2.8160},
    {'name': 'B', 'depositary_shares': 192_500_000, 'depositary_per_preferred': 20,
     'liquidation_preference_per_share': 1000,
     'min_rate_per_preferred': 2.2740, 'max_rate_per_preferred': 2.8420},
]}
GOOGL_ENTERPRISE_VALUE = 2_500_000_000_000.0


def facts_of(cik):
    document = json.loads((FACTS / (cik + '.json')).read_bytes())
    assert str(document['cik']).zfill(10) == cik, (cik, document.get('entityName'))
    return document['facts']


SOURCE_RELEASE = 'a' * 64
SOURCE_MANIFEST = 'f' * 64
CEILING = '2026-09-24T23:59:59.999999999Z'


def route_envelope(**overrides):
    """The blocks the Zion route adds to the claims contract it serves.

    The route extracts from a companion Company Facts release and separately confirms that
    the engine release pins the digest of the same raw archive member, so the consumer sees
    two independently published releases that must name the same bytes.
    """
    envelope = {
        'source_release_id': SOURCE_RELEASE,
        'source_schema_version': 'sec-companyfacts-source-v1',
        'source_manifest_sha256': SOURCE_MANIFEST,
        'source_bundle': {
            'issuer': {'cik': None, 'entity_name': None, 'engine_label': None},
            'engine_release': {'release_id': RELEASE, 'raw_archive_member_sha256': MEMBER,
                               'registry_sha256': 'd' * 64},
            'companyfacts_release': {'release_id': SOURCE_RELEASE, 'member_sha256': MEMBER,
                                     'schema_version': 'sec-companyfacts-source-v1',
                                     'snapshot_date': '2026-09-24', 'rights': 'PUBLIC_SEC_ONLY',
                                     'manifest_sha256': SOURCE_MANIFEST},
            'reconciliation': {'status': 'MEMBER_SHA256_AGREES_WITH_ENGINE_PINNED_MEMBER',
                               'engine_raw_member_sha256': MEMBER,
                               'companion_member_sha256': MEMBER,
                               'bulk_archive': 'etag-27',
                               'bulk_archive_declared_sha256': 'e' * 64},
            'cutoff_ceiling_utc': CEILING,
            'extraction': {'claims_schema_version': VERSION,
                           'availability_policy': 'DATE_ONLY_END_OF_DAY_UTC_V1'},
        },
        'cutoff': {'requested': ASOF_TEXT, 'policy': 'DATE_ONLY_END_OF_DAY_UTC_V1',
                   'resolved_utc': ASOF_TEXT + 'T23:59:59.999999999Z', 'day_complete': True,
                   'valuation_date': ASOF_TEXT, 'source_ceiling_utc': CEILING},
    }
    envelope.update(overrides)
    return envelope


def contract(cik, *, preferred_terms=None):
    """Build upstream claims and wrap them the way the Zion route does."""
    payload = build_claims(facts_of(cik), ASOF, cik=cik, preferred_terms=preferred_terms)
    assert payload['schema_version'] == VERSION
    return dict(payload, release_id=RELEASE, member_sha256=MEMBER,
                registry_sha256='d' * 64, manifest_sha256='e' * 64,
                company_label='SEC company facts fixture',
                provenance={'source_lineage': {'rights': 'PUBLIC_SEC_ONLY', 'licensed_sources_used': False}},
                **route_envelope())


def amount(claim):
    return Decimal(claim['value_decimal'])


def test_alphabet_contract_verifies_across_the_two_repositories():
    verified = verify_claims(contract(GOOGL))
    assert verified['schema_version'] == VERSION
    assert verified['rights'] == 'PUBLIC_SEC_ONLY'
    assert verified['source']['release_id'] == RELEASE
    assert verified['source']['member_sha256'] == MEMBER
    assert verified['source']['adapter_version'] == 'zion-equity-claims-v1'
    assert verified['source']['warnings'], 'consumer must carry the certification warnings'
    assert verified['cik'] == GOOGL and verified['valuation_date'] == ASOF_TEXT


def test_alphabet_claims_match_the_june_2026_10q():
    claims = verify_claims(contract(GOOGL))['claims']
    debt = claims['debt']
    # us-gaap:LongTermDebtCurrent 1,999,000,000 + us-gaap:LongTermDebtNoncurrent 98,165,000,000
    assert debt['evidence_state'] == 'REPORTED'
    assert amount(debt) == Decimal('100164000000')
    assert debt['current_decimal'] == '1999000000'
    assert debt['noncurrent_decimal'] == '98165000000'
    # us-gaap:FinanceLeaseLiability total, with its reported split
    assert amount(claims['finance_leases']) == Decimal('2590000000')
    assert claims['finance_leases']['current_decimal'] == '449000000'
    assert claims['finance_leases']['noncurrent_decimal'] == '2141000000'
    # us-gaap:OperatingLeaseLiability total, reported but excluded from the bridge
    assert amount(claims['operating_leases']) == Decimal('18037000000')
    assert claims['operating_leases']['included_in_enterprise_bridge'] is False
    # us-gaap:CashAndCashEquivalentsAtCarryingValue 55,911,000,000
    assert amount(claims['cash']) == Decimal('55911000000')
    # cash plus us-gaap:MarketableSecuritiesCurrent 186,563,000,000 (Alphabet reports no
    # ShortTermInvestments and no MarketableSecuritiesNoncurrent)
    assert amount(claims['nonoperating_assets']) == Decimal('242474000000')
    assert 'us-gaap:MarketableSecuritiesCurrent' in {
        source['concept'] for source in claims['nonoperating_assets']['sources']}
    preferred = claims['preferred_equity']
    # us-gaap:ConvertiblePreferredStockNonredeemableOrRedeemableIssuerOptionValue 18,023,000,000.
    # Alphabet does not file PreferredStockValue, so the carrying value must come from this concept.
    assert preferred['carrying_concept'] == 'us-gaap:ConvertiblePreferredStockNonredeemableOrRedeemableIssuerOptionValue'
    assert preferred['dividend_rate_decimal'] == '0.0625'
    assert amount(preferred) == Decimal('18023000000')
    # us-gaap:PreferredStockDividendRatePercentage 6.25%, us-gaap:PreferredStockSharesOutstanding
    # 19,000,000, us-gaap:PreferredStockLiquidationPreference 1,000 per share
    assert preferred['dividend_rate_decimal'] == '0.0625'
    assert preferred['shares_outstanding_decimal'] == '19000000'
    assert preferred['liquidation_preference_per_share_decimal'] == '1000'
    noncontrolling = claims['noncontrolling_interests']
    # us-gaap:NoncontrollingInterestInVariableInterestEntity 7,100,000,000. Alphabet files no
    # us-gaap:MinorityInterest, so the claim must be reported from the VIE disclosure measure
    # rather than labelled absent.
    assert noncontrolling['evidence_state'] == 'REPORTED'
    assert amount(noncontrolling) == Decimal('7100000000')
    assert noncontrolling['classification'] == 'VIE_DISCLOSURE_NONCONTROLLING_INTEREST'
    assert noncontrolling['treatment'] == 'DEDUCT_FROM_CONSOLIDATED_ENTERPRISE_VALUE'
    assert noncontrolling['redeemable_subset']['evidence_state'] == 'UNAVAILABLE'
    assert 'double count' in noncontrolling['redeemable_subset']['note']
    # us-gaap:CommonStockSharesOutstanding 12,230,000,000 at 2026-06-30
    assert amount(claims['common_shares']) == Decimal('12230000000')
    assert claims['common_shares']['basis'] == 'BALANCE_SHEET_ALL_CLASSES'
    assert claims['common_shares']['classes']['evidence_state'] == 'UNAVAILABLE'
    # Reconciliation evidence, not a claim: us-gaap:StockholdersEquity 640,480,000,000
    totals = {row['concept']: row['value_decimal']
              for row in verified_report_totals(GOOGL)}
    assert totals['us-gaap:StockholdersEquity'] == '640480000000'
    aggregate = verify_claims(contract(GOOGL))['aggregate_claims']
    assert aggregate['status'] == 'AVAILABLE'
    assert Decimal(aggregate['deduct_claims_decimal']) == (
        Decimal('100164000000') + Decimal('2590000000') + Decimal('18023000000') + Decimal('7100000000'))
    assert Decimal(aggregate['add_claims_decimal']) == Decimal('55911000000') + Decimal('242474000000')
    assert aggregate['verified_absent'] == []


def verified_report_totals(cik):
    return verify_claims(contract(cik))['reconciliation']['reported_equity_totals']


def test_alphabet_share_vintage_is_the_newest_filed_period():
    shares = verify_claims(contract(GOOGL))['claims']['common_shares']
    dated = shares['dated_observations']
    assert dated, 'dated share observations are required to justify the vintage'
    assert dated[0]['period_end'] == '2026-06-30', 'the newest filed period must be the selected one'
    assert dated[0]['value_decimal'] == shares['value_decimal'] == '12230000000'
    assert shares['not_a_weighted_average'] is True
    older = [row for row in dated if row['period_end'] < dated[0]['period_end']]
    assert older, 'the earlier filing vintage must remain visible in the evidence'
    assert any(row['period_end'] == '2025-12-31' for row in older)
    assert all(row['value_decimal'] != shares['value_decimal'] for row in older)
    assert [row['period_end'] for row in dated] == sorted(
        (row['period_end'] for row in dated), reverse=True), 'observations must be newest first'


def test_alphabet_preferred_terms_are_assumed_and_agree_with_the_contract():
    claims = verify_claims(contract(GOOGL, preferred_terms=TERMS))
    preferred = claims['claims']['preferred_equity']
    terms = preferred['dilution_terms']
    assert terms['evidence_state'] == 'ASSUMED'
    assert terms['basis'] == 'EXPLICIT_SELECTION_FROM_OFFERING_DOCUMENT;NOT_XBRL_VERIFIED'
    assert terms['permitted_for_valuation'] is True
    assert Decimal(terms['preferred_shares_decimal']) == Decimal('19250000')
    assert Decimal(terms['liquidation_preference_total_decimal']) == Decimal('19250000000')
    assert Decimal(terms['min_converted_common_shares_decimal']) == Decimal('43562750')
    assert Decimal(terms['max_converted_common_shares_decimal']) == Decimal('54458250')
    # Terms that agree with the reported count leave the claim certified; a carrying value is
    # still reported, so the state is derived rather than an assumption substituting for one.
    assert preferred['evidence_state'] == 'DERIVED_VERIFIED'
    consistency = term_consistency(claims, TERMS)
    assert consistency['status'] == 'CONSISTENT', consistency
    assert term_consistency(verify_claims(contract(GOOGL)), TERMS)['status'] == 'NOT_COMPARABLE'


def test_apple_and_microsoft_absent_claims_are_reviewed_not_assumed():
    for cik in (AAPL, MSFT):
        claims = verify_claims(contract(cik))['claims']
        noncontrolling = claims['noncontrolling_interests']
        assert noncontrolling['evidence_state'] == 'REVIEWED_ABSENT', cik
        assert noncontrolling['value_decimal'] is None
        assert noncontrolling['verified_absent'] is True
        assert noncontrolling['permitted_for_valuation'] is not False
        assert 'not evidence of a zero claim' in ' '.join(noncontrolling['notes'])
        preferred = claims['preferred_equity']
        # Neither Apple nor Microsoft files a preferred carrying amount, so the claim is reviewed
        # absent for both; a filed zero would be REPORTED instead, which the upstream claim tests pin.
        assert preferred['evidence_state'] == 'REVIEWED_ABSENT', cik
        assert preferred['value_decimal'] is None
        assert preferred['verified_absent'] is True
        assert 'not evidence of a zero claim' in ' '.join(preferred['notes'])
        if cik == MSFT:
            # us-gaap:FinanceLeaseLiability 66,594,000,000 at 2026-06-30 in the fiscal 2026 10-K.
            assert amount(claims['finance_leases']) == Decimal('66594000000')
        else:
            # us-gaap:FinanceLeaseLiability 1,230,000,000 at 2025-09-27, still inside the age cap.
            assert amount(claims['finance_leases']) == Decimal('1230000000')


def test_debt_claims_agree_with_the_reported_total_without_netting_it():
    microsoft = verify_claims(contract(MSFT))['claims']['debt']
    # us-gaap:LongTermDebtCurrent 9,227,000,000 at 2026-06-30 plus
    # us-gaap:LongTermDebtNoncurrent 31,067,000,000; the reported us-gaap:LongTermDebt total of
    # 40,294,000,000 equals that sum exactly, so no disagreement is recorded.
    assert microsoft['evidence_state'] == 'REPORTED'
    assert amount(microsoft) == Decimal('40294000000')
    assert microsoft['current_decimal'] == '9227000000'
    assert microsoft['noncurrent_decimal'] == '31067000000'
    assert not microsoft['notes']
    assert microsoft['potential_duplicate_concepts'] == []
    apple = verify_claims(contract(AAPL))['claims']['debt']
    # us-gaap:LongTermDebtCurrent 11,007,000,000 + us-gaap:CommercialPaper 1,997,000,000 +
    # us-gaap:LongTermDebtNoncurrent 71,340,000,000; the combined us-gaap:LongTermDebt total of
    # 82,300,000,000 is 47,000,000 below the long-term component sum and is reported, not netted.
    assert amount(apple) == Decimal('84344000000')
    assert any('differs from the reported components by -47000000' in note for note in apple['notes'])


def test_share_count_basis_matches_each_filers_disclosure():
    apple = verify_claims(contract(AAPL))['claims']['common_shares']
    # dei:EntityCommonStockSharesOutstanding 14,594,180,000 at 2026-07-17 (cover page)
    assert apple['basis'] == 'COVER_PAGE_DEI'
    assert amount(apple) == Decimal('14594180000')
    microsoft = verify_claims(contract(MSFT))['claims']['common_shares']
    # dei:EntityCommonStockSharesOutstanding 24,100,000,000 at 2026-08-21 (cover page)
    # dei:EntityCommonStockSharesOutstanding 7,425,545,491 at 2026-07-23 (cover page)
    assert microsoft['basis'] == 'COVER_PAGE_DEI'
    assert amount(microsoft) == Decimal('7425545491')
    assert verify_claims(contract(GOOGL))['claims']['common_shares']['basis'] == 'BALANCE_SHEET_ALL_CLASSES'


def test_microsoft_nonoperating_assets_use_only_the_concepts_it_reports():
    claims = verify_claims(contract(MSFT))['claims']
    # us-gaap:CashAndCashEquivalentsAtCarryingValue 20,935,000,000 plus
    # us-gaap:ShortTermInvestments 55,908,000,000 at 2026-06-30. Microsoft reports no marketable
    # securities concept and no long-term investment concept in the eligible window, so nothing is
    # invented and nothing is silently dropped.
    assert amount(claims['nonoperating_assets']) == Decimal('76843000000')
    assert claims['nonoperating_assets']['excluded_concepts'] == ['us-gaap:LongTermInvestments']
    assert 'us-gaap:LongTermInvestments' in ' '.join(claims['nonoperating_assets']['notes'])
    assert {source['concept'] for source in claims['nonoperating_assets']['sources']} == {
        'us-gaap:CashAndCashEquivalentsAtCarryingValue', 'us-gaap:ShortTermInvestments'}


def test_end_to_end_bridge_matches_independent_decimal_arithmetic():
    claims = verify_claims(contract(GOOGL, preferred_terms=TERMS))
    result = value_per_share(GOOGL_ENTERPRISE_VALUE, claims, scenario='AS_CONVERTED_MAX_RATE')
    assert result['primary']['status'] == 'AVAILABLE'
    assert result['unresolved']['blocking'] == []

    contract_claims = claims['claims']
    shares = amount(contract_claims['common_shares'])
    # Independent arithmetic from the documented bridge definition: the debt claim and the lease
    # claim are each counted exactly once, and cash is added once through the nonoperating claim
    # (the bridge's "other nonoperating assets" is the nonoperating claim less the cash already added).
    expected_short_term = (Decimal(contract_claims['debt']['current_decimal'])
                           + Decimal(contract_claims['finance_leases']['current_decimal']))
    expected_long_term = (Decimal(contract_claims['debt']['noncurrent_decimal'])
                          + Decimal(contract_claims['finance_leases']['noncurrent_decimal']))
    expected_debt = expected_short_term
    expected_added = amount(contract_claims['nonoperating_assets'])
    expected_preferred = Decimal('0')  # as-converted deducts no preferred claim
    expected_shares_added = Decimal('54458250')
    expected_equity = (Decimal(str(GOOGL_ENTERPRISE_VALUE)) + expected_added - expected_debt
                       - expected_long_term - amount(contract_claims['noncontrolling_interests'])
                       - expected_preferred)
    expected_per_share = expected_equity / (shares + expected_shares_added)
    assert abs(Decimal(str(result['primary']['equity_value'])) - expected_equity) / expected_equity < Decimal('1e-12')
    assert abs(Decimal(str(result['primary']['value_per_share'])) - expected_per_share) / expected_per_share < Decimal('1e-12')
    assert Decimal(str(result['bridge_inputs']['short_term_debt'])) == expected_debt
    assert Decimal(str(result['bridge_inputs']['long_term_debt'])) == expected_long_term
    assert Decimal(str(result['bridge_inputs']['other_nonoperating_assets'])) == Decimal('186563000000')

    liquidation = value_per_share(GOOGL_ENTERPRISE_VALUE, claims, scenario='LIQUIDATION_PREFERENCE')
    # The preference is the reported per-share value times the reported share count, and the
    # instrument is never counted both as a claim and as converted shares.
    assert Decimal(str(liquidation['scenarios']['LIQUIDATION_PREFERENCE']['claim'])) == Decimal('19000000000')
    assert liquidation['scenarios']['LIQUIDATION_PREFERENCE']['shares_added'] == 0.0
    assert result['scenarios']['AS_CONVERTED_MAX_RATE']['claim'] == 0.0
    assert (liquidation['scenarios']['LIQUIDATION_PREFERENCE']['value_per_share']
            < result['scenarios']['AS_CONVERTED_MAX_RATE']['value_per_share'])
    assert Decimal(str(liquidation['primary']['equity_value'])) == (
        expected_equity - Decimal('19000000000'))
    assert result['preferred_evidence_state'] == 'DERIVED_VERIFIED'
    assert result['source']['release_id'] == RELEASE
    assert result['noncontrolling_policy'] == 'DEDUCT_REPORTED'


def test_service_credential_transport_replaces_the_production_bearer():
    payload = contract(GOOGL)
    calls = []

    class Transport:
        def get(self, url, headers=None, params=None):
            calls.append(dict(url=url, headers=dict(headers or {}), params=dict(params or {})))
            return payload

    loaded = load_equity_claims('GOOGL', ASOF_TEXT, Transport(), cik=GOOGL,
                                base='https://zion.internal/', service_token='scoped-service-token',
                                caller=SERVICE_CALLER, expected_release_id=RELEASE)
    assert loaded['source']['ticker'] == 'GOOGL'
    assert loaded['source']['identity_status'] == 'EXPLICIT_USER_CIK_NOT_TICKER_CERTIFIED'
    call = calls[0]
    assert call['url'] == 'https://zion.internal/private/v1/equity-claims'
    assert call['headers']['x-zion-service-token'] == 'scoped-service-token'
    assert call['headers']['x-zion-service-caller'] == SERVICE_CALLER == 'dcf-valuation-engine'
    assert 'Authorization' not in call['headers'], 'a service credential must not send the private bearer'
    # The route resolves a date-only cutoff as the whole UTC day (its named
    # DATE_ONLY_END_OF_DAY_UTC_V1 policy), which is the resolution this consumer requires; an
    # explicit instant inside the day would be honoured and would drop the day's filings.
    assert call['params'] == dict(cik=GOOGL, as_of=ASOF_TEXT,
                                  recipient='human_research', expected_release_id=RELEASE, release_id=RELEASE)
    # What the source resolved is read back, not assumed from what was asked for.
    assert loaded['source']['cutoff_policy'] == 'DATE_ONLY_END_OF_DAY_UTC_V1'
    assert loaded['source']['served_cutoff_utc'] == ASOF_TEXT + 'T23:59:59.999999999Z'

    # A release pin that is not what the source served is refused, and neither transport
    # nor caller mismatch can silently fall back to an unpinned read.
    with pytest.raises(ProviderError):
        load_equity_claims('GOOGL', ASOF_TEXT, Transport(), cik=GOOGL, base='https://zion.internal',
                           service_token='scoped-service-token', caller=SERVICE_CALLER,
                           expected_release_id='f' * 64)
    with pytest.raises(ProviderError):
        load_equity_claims('GOOGL', ASOF_TEXT, Transport(), cik=GOOGL, base='https://zion.internal')
    with pytest.raises(ProviderError):
        load_equity_claims('GOOGL', ASOF_TEXT, Transport(), cik=GOOGL, base='https://zion.internal',
                           service_token='scoped-service-token', caller='someone-else')


def test_tampered_evidence_is_refused_rather_than_reconciled():
    payload = contract(GOOGL)
    payload['claims']['debt']['value_decimal'] = '100164000001'
    with pytest.raises(ProviderError):
        verify_claims(payload)
    payload = contract(GOOGL)
    payload['claims']['noncontrolling_interests']['sources'][0]['reported_token'] = '999'
    # Tampering with the reported token breaks the source digest first.
    with pytest.raises(ProviderError):
        verify_claims(payload)
    payload = contract(GOOGL)
    payload['claims']['noncontrolling_interests']['value_decimal'] = None
    with pytest.raises(ProviderError):
        verify_claims(payload)


# --- the DCF Worker's own service-binding transport ----------------------------------
#
# `dispatch` is the only step that needs a Worker runtime, so the transport, the scoped
# credential headers, the contract verification and the bridge arithmetic below run as
# written in production. A binding double stands in for `env.ZION_FINANCIAL_QUERY`.


class _BindingResponse:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    async def text(self):
        return json.dumps(self.payload)


class _Binding:
    """Stands in for the JS Fetcher on the other side of the service binding."""

    def __init__(self, payload):
        self.payload = payload
        self.requests = []

    async def fetch(self, target):
        self.requests.append(target)
        return _BindingResponse(self.payload)


class _Transport(zion_service.ServiceBindingHTTP):
    async def dispatch(self, target, headers):
        self.headers = headers
        return await self.binding.fetch(target)


@contextlib.contextmanager
def worker_runtime():
    """The Worker's async-to-sync bridge, without the Pyodide runtime."""
    original = zion_service.sync
    zion_service.sync = lambda awaitable: asyncio.run(awaitable)
    try:
        yield
    finally:
        zion_service.sync = original


def bridge_over_binding(payload, **overrides):
    binding = _Binding(payload)
    transport = _Transport(binding)
    options = dict(cik=GOOGL, enterprise_value=GOOGL_ENTERPRISE_VALUE, http=transport,
                   expected_release_id=RELEASE, preferred_terms=TERMS)
    options.update(overrides)
    with worker_runtime():
        result = zion_service.bridge_scenario('GOOGL', ASOF_TEXT, **options)
    return result, binding, transport


def test_service_binding_carries_the_verified_contract_to_a_per_share_scenario():
    result, binding, transport = bridge_over_binding(contract(GOOGL, preferred_terms=TERMS))

    # One request, over the binding, with the scoped service credential and no bearer.
    assert len(binding.requests) == 1
    assert binding.requests[0] == 'https://zion.internal/private/v1/equity-claims?' + urlencode(
        dict(cik=GOOGL, as_of=ASOF_TEXT, recipient='human_research',
             expected_release_id=RELEASE, release_id=RELEASE))
    assert transport.headers['x-zion-service-token'] == 'scoped-service-token'
    assert transport.headers['x-zion-service-caller'] == SERVICE_CALLER
    assert 'Authorization' not in transport.headers

    # The consumer recomputed every digest over the real filing-backed contract, and the
    # release pin it recorded is the one the source actually served.
    assert result['attestation']['transport'] == 'CLOUDFLARE_SERVICE_BINDING'
    assert result['attestation']['release_id'] == RELEASE
    assert result['attestation']['member_sha256'] == MEMBER
    assert result['attestation']['digest_proves_authenticity'] is False
    assert result['attestation']['claim_evidence_digests'] == 'RECOMPUTED_BY_CONSUMER'
    assert result['cik'] == GOOGL and result['valuation_date'] == ASOF_TEXT
    assert result['source']['release_id'] == RELEASE

    # The binding path produces exactly the scenario the direct contract produces.
    direct = value_per_share(GOOGL_ENTERPRISE_VALUE, verify_claims(contract(GOOGL, preferred_terms=TERMS)),
                             preferred_terms=TERMS, scenario='AS_CONVERTED_MAX_RATE')
    assert result['primary'] == direct['primary']
    assert result['scenarios'] == direct['scenarios']
    assert result['term_consistency']['status'] == 'CONSISTENT'
    assert result['unresolved'] == direct['unresolved']


def test_service_binding_refuses_a_substituted_release_before_bridging():
    # A substituted release is one that is internally consistent: both the engine pin and the
    # bundle agree on a release that is simply not the one this consumer asked for. Changing
    # only the top-level pin would leave a self-contradictory payload, which the bundle check
    # refuses first, so the pin comparison is exercised on a payload that has no other fault.
    other = contract(GOOGL)
    other['release_id'] = 'f' * 64
    other['source_bundle']['engine_release']['release_id'] = 'f' * 64
    with pytest.raises(ServiceError, match='release mismatch'):
        bridge_over_binding(other)


def test_service_binding_refuses_a_cutoff_resolved_inside_the_evidence_day():
    # The served contract names its own resolution, and a resolution that never completed the
    # evidence day would silently drop every filing dated it.
    intraday = contract(GOOGL)
    intraday['cutoff'] = dict(intraday['cutoff'], policy='EXPLICIT_INSTANT', day_complete=False,
                              resolved_utc=ASOF_TEXT + 'T12:00:00Z')
    with pytest.raises(ServiceError, match='evidence day incomplete'):
        bridge_over_binding(intraday)

    other_day = contract(GOOGL)
    other_day['cutoff'] = dict(other_day['cutoff'], requested='2026-10-13')
    with pytest.raises(ServiceError, match='different cutoff than the requested evidence date'):
        bridge_over_binding(other_day)


def test_service_binding_refuses_a_payload_whose_claims_were_edited_in_flight():
    tampered = contract(GOOGL)
    tampered['claims']['finance_leases']['value_decimal'] = '2590000001'
    with pytest.raises(ServiceError, match='evidence digest mismatch'):
        bridge_over_binding(tampered)


def test_service_binding_refuses_a_claim_that_stops_being_certified():
    # Demoting a certified claim to an assumption cannot silently become a
    # zero-or-ignored bridge input: the aggregate block stops agreeing with it.
    demoted = contract(GOOGL, preferred_terms=TERMS)
    preferred = demoted['claims']['preferred_equity']
    preferred['evidence_state'] = 'ASSUMED'
    reseal_claim(preferred)
    with pytest.raises(ServiceError, match='aggregate claim block'):
        bridge_over_binding(demoted)


def reseal_claim(claim):
    claim.pop('evidence_digest', None)
    claim['evidence_digest'] = hashlib.sha256(
        json.dumps({key: value for key, value in claim.items()}, sort_keys=True,
                   separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    return claim
