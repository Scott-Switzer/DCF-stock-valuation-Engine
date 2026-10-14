from copy import deepcopy
import pytest
from zion_history_provider import history_document, load_history
from dcf_loader import ProviderError, parse_document


def page():
    rows, leaves = [], {}
    for year, amount in [(2022, '100'), (2023, '110'), (2024, '121')]:
        sid = str(year)
        row = dict(metric='revenue', unit='USD', currency='USD', period_start=f'{year}-01-01',
                   period_end=f'{year}-12-31', value_decimal=amount, available_at=f'{year+1}-02-01T05:00:00Z',
                   frequency='annual', member_sha256='m', source_observation_ids=[sid],
                   source_terms=[{'source_observation_id': sid, 'coefficient': 1}])
        rows.append(row)
        leaves[sid] = dict(row, cik='0000320193', source_record={'val': amount})
    return dict(schema_version='sec-financial-engine-v2', cik='0000320193', frequency='annual',
                as_of='2026-09-24T00:00:00Z', member_sha256='m', registry_version='v2',
                provenance={'release_id':'r1','registry_sha256':'registry','manifest_sha256':'manifest',
                            'source_lineage':{'rights':'PUBLIC_SEC_ONLY'}},
                observations=rows, source_records=leaves, coverage_gaps=[], accounting_checks=[],
                pagination={'offset':0,'returned_items':3,'total_items':3,'next_cursor':None})


def test_native_history_maps_real_contract_without_filling_gaps():
    result = history_document([page()], 'AAPL', '2026-09-24', '0000320193')
    assert [r['revenue'] for r in result['historical']] == [100, 110, 121]
    assert result['historical'][-1]['nwc'] is None
    assert result['bridge']['short_term_debt'] is None
    assert result['market']['price'] is None
    assert result['source']['native_history'][0]['source_records']['2024']['value_decimal'] == '121'
    assert result['source']['release_id'] == 'r1'
    assert 'historical.2024-12-31.nwc' in result['source']['missing_fields']
    with pytest.raises(ValueError):
        parse_document(result)


@pytest.mark.parametrize('mutation', ['cik', 'unit', 'future', 'leaf', 'release', 'duplicate', 'period'])
def test_incompatible_history_fails_closed(mutation):
    first = page()
    pages = [first]
    if mutation == 'cik': first['cik'] = '0000000001'
    if mutation == 'unit': first['observations'][0]['unit'] = 'USD millions'
    if mutation == 'future': first['observations'][0]['available_at'] = '2027-01-01T00:00:00Z'
    if mutation == 'leaf': first['source_records']['2022']['source_record']['val'] = '999'
    if mutation == 'release':
        other = deepcopy(first)
        other['provenance']['release_id'] = 'r2'
        pages.append(other)
    if mutation == 'duplicate':
        other = deepcopy(first['observations'][0]); other['value_decimal'] = '999'
        first['observations'].append(other)
    if mutation == 'period': first['observations'][0]['period_start'] = '2022-10-01'
    with pytest.raises(ProviderError): history_document(pages, 'AAPL', '2026-09-24', '0000320193')


def test_pagination_pins_release_and_collects_all_leaves():
    first, second = page(), page()
    first['observations'] = first['observations'][:1]
    first['source_records'] = {'2022': first['source_records']['2022']}
    first['pagination'].update(returned_items=1, next_cursor='next')
    second['observations'] = second['observations'][1:]
    second['source_records'].pop('2022')
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


def test_api_advertises_native_provider_without_secrets():
    from app import app
    response = app.test_client().get('/api/providers')
    assert response.json['providers']['zion_history']['kind'] == 'private_financial_history'


def test_nonmonetary_share_observation_has_no_currency():
    data = page()
    share = deepcopy(data['observations'][-1])
    share.update(metric='diluted_shares', unit='shares', currency=None)
    share['source_observation_ids'] = ['shares']
    share['source_terms'] = [{'source_observation_id':'shares', 'coefficient':1}]
    data['source_records']['shares'] = dict(share, cik=data['cik'], source_record={'val':'121'})
    data['observations'].append(share)
    assert history_document([data], 'AAPL','2026-09-24',data['cik'])['market']['diluted_shares'] == 121
