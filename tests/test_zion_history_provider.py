from copy import deepcopy
import hashlib
import json
import pytest
from zion_history_provider import history_document, load_history, sign_evidence, verify_evidence
from dcf_loader import ProviderError, parse_document


def _encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def make_leaf(cik, concept, unit, currency, start, end, amount, available_at, accn='0000320193-25-000001', form='10-K'):
    record = {'accn': accn, 'end': end, 'filed': available_at[:10], 'form': form, 'val': amount}
    if start is not None:
        record['start'] = start
    sid = hashlib.sha256(_encoded({'cik': cik, 'concept': concept, 'unit': unit, 'source_record': record})).hexdigest()
    return sid, dict(
        cik=cik, concept='us-gaap:' + concept, unit=unit, currency=currency,
        period_start=start, period_end=end, value_decimal=amount, available_at=available_at,
        accession=accn, form=form, member_sha256='m', source_observation_id=sid,
        source_record=record,
    )


def page():
    cik = '0000320193'
    rows, leaves = [], {}
    for year, amount in [(2022, '100'), (2023, '110'), (2024, '121')]:
        start, end, avail = f'{year}-01-01', f'{year}-12-31', f'{year+1}-02-01T05:00:00Z'
        sid, leaf = make_leaf(cik, 'Revenues', 'USD', 'USD', start, end, amount, avail)
        row = dict(metric='revenue', concept='us-gaap:Revenues', unit='USD', currency='USD',
                   period_start=start, period_end=end, value_decimal=amount, available_at=avail,
                   accession=leaf['accession'], form='10-K', frequency='annual', member_sha256='m',
                   source_observation_ids=[sid], source_terms=[{'source_observation_id': sid, 'coefficient': 1}])
        rows.append(row)
        leaves[sid] = leaf
    return dict(schema_version='sec-financial-engine-v2', cik=cik, frequency='annual',
                as_of='2026-09-24T00:00:00Z', member_sha256='m', registry_version='v2',
                provenance={'release_id':'r1','registry_sha256':'registry','manifest_sha256':'manifest',
                            'source_lineage':{'rights':'PUBLIC_SEC_ONLY'}},
                observations=rows, source_records=leaves, coverage_gaps=[], accounting_checks=[],
                pagination={'offset':0,'returned_items':3,'total_items':3,'next_cursor':None})


def test_native_history_maps_real_contract_without_filling_gaps():
    p = page()
    last_sid = p['observations'][-1]['source_observation_ids'][0]
    result = history_document([p], 'AAPL', '2026-09-24', '0000320193')
    assert [r['revenue'] for r in result['historical']] == [100, 110, 121]
    assert result['historical'][-1]['nwc'] is None
    assert result['bridge']['short_term_debt'] is None
    assert result['market']['price'] is None
    assert result['source']['native_history'][0]['source_records'][last_sid]['value_decimal'] == '121'
    assert result['source']['release_id'] == 'r1'
    assert 'historical.2024-12-31.nwc' in result['source']['missing_fields']
    with pytest.raises(ValueError):
        parse_document(result)


@pytest.mark.parametrize('mutation', ['cik', 'unit', 'future', 'leaf', 'leaf_hash', 'release', 'duplicate', 'period'])
def test_incompatible_history_fails_closed(mutation):
    first = page()
    sid0 = first['observations'][0]['source_observation_ids'][0]
    pages = [first]
    if mutation == 'cik': first['cik'] = '0000000001'
    if mutation == 'unit': first['observations'][0]['unit'] = 'USD millions'
    if mutation == 'future': first['observations'][0]['available_at'] = '2027-01-01T00:00:00Z'
    if mutation == 'leaf': first['source_records'][sid0]['source_record']['val'] = '999'
    if mutation == 'leaf_hash':
        first['observations'][0]['value_decimal'] = '999'
        first['source_records'][sid0]['value_decimal'] = '999'
        first['source_records'][sid0]['source_record']['val'] = '999'
    if mutation == 'release':
        other = deepcopy(first)
        other['provenance']['release_id'] = 'r2'
        pages.append(other)
    if mutation == 'duplicate':
        other = deepcopy(first['observations'][0]); other['value_decimal'] = '999'
        first['observations'].append(other)
    if mutation == 'period': first['observations'][0]['period_start'] = '2022-10-01'
    with pytest.raises(ProviderError): history_document(pages, 'AAPL', '2026-09-24', '0000320193')


def test_stale_release_is_rejected_when_caller_pins_a_different_release():
    class HTTP:
        def get(self, url, *, headers, params):
            # Server serves release r1 while the caller pinned r9: a stale or drifted release.
            return page()
    with pytest.raises(ProviderError, match='release mismatch'):
        load_history('AAPL', '2026-09-24', HTTP(), cik='0000320193', base='https://example.test',
                     token='t', expected_release_id='r9')


def test_pagination_pins_release_and_collects_all_leaves():
    first, second = page(), page()
    sid0 = first['observations'][0]['source_observation_ids'][0]
    first['observations'] = first['observations'][:1]
    first['source_records'] = {sid0: first['source_records'][sid0]}
    first['pagination'].update(returned_items=1, next_cursor='next')
    second['observations'] = second['observations'][1:]
    second['source_records'].pop(sid0)
    second['pagination'].update(offset=1, returned_items=2)
    class HTTP:
        def get(self, url, *, headers, params):
            assert url == 'https://example.test/private/v1/financial-history'
            if params.get('cursor') == 'next':
                assert params['expected_release_id'] == 'r1'
                return second
            return first
    result = load_history('AAPL','2026-09-24', HTTP(), cik='0000320193',base='https://example.test',token='local')
    assert len(result['historical']) == 3
    assert verify_evidence(result, 'local')['historical'][-1]['revenue'] == 121


def test_api_advertises_native_provider_without_secrets():
    from app import app
    response = app.test_client().get('/api/providers')
    assert response.json['providers']['zion_history']['kind'] == 'private_financial_history'


def test_nonmonetary_share_observation_has_no_currency():
    data = page()
    last = data['observations'][-1]
    sid, leaf = make_leaf(
        data['cik'], 'WeightedAverageNumberOfDilutedSharesOutstanding', 'shares', None,
        last['period_start'], last['period_end'], '121', last['available_at']
    )
    share = deepcopy(last)
    share.update(
        metric='diluted_shares', concept=leaf['concept'], unit='shares', currency=None,
        source_observation_ids=[sid], source_terms=[{'source_observation_id': sid, 'coefficient': 1}]
    )
    data['source_records'][sid] = leaf
    data['observations'].append(share)
    assert history_document([data], 'AAPL','2026-09-24',data['cik'])['market']['diluted_shares'] == 121


def test_verify_evidence_rejects_unsigned_or_forged_bundles():
    p = page()
    doc = history_document([p], 'AAPL', '2026-09-24', '0000320193')
    with pytest.raises(ProviderError, match='unattested'):
        verify_evidence(doc, 'server-secret')
    doc['source']['evidence_attestation'] = sign_evidence([p], 'AAPL', '2026-09-24', '0000320193', 'wrong-secret')
    with pytest.raises(ProviderError, match='attestation mismatch'):
        verify_evidence(doc, 'server-secret')
    doc['source']['evidence_attestation'] = sign_evidence([p], 'AAPL', '2026-09-24', '0000320193', 'server-secret')
    assert verify_evidence(doc, 'server-secret')['historical'][-1]['revenue'] == 121
    # Mutating the embedded evidence after signing must fail closed.
    tampered = deepcopy(doc)
    tampered['company']['ticker'] = 'MSFT'
    with pytest.raises(ProviderError, match='attestation mismatch'):
        verify_evidence(tampered, 'server-secret')

