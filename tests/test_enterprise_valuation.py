from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import pytest
from test_zion_history_provider import make_leaf, page
from zion_history_provider import history_document, sign_evidence
from enterprise_valuation import equity_bridge, value_enterprise

SECRET = 'test-zion-evidence-secret'


def document(secret=SECRET):
    data=page()
    for row in list(data['observations']):
        amount = str(Decimal(row['value_decimal']) * Decimal('0.2'))
        sid, leaf = make_leaf(
            data['cik'], 'OperatingIncomeLoss', 'USD', 'USD',
            row['period_start'], row['period_end'], amount, row['available_at']
        )
        ebit=deepcopy(row)
        ebit.update(
            metric='operating_income', concept=leaf['concept'], value_decimal=amount,
            source_observation_ids=[sid], source_terms=[{'source_observation_id':sid,'coefficient':1}]
        )
        data['observations'].append(ebit)
        data['source_records'][sid]=leaf
    doc = history_document([data],'AAPL','2026-09-24',data['cik'])
    if secret is not None:
        doc['source']['evidence_attestation'] = sign_evidence([data], 'AAPL', '2026-09-24', data['cik'], secret)
    return doc


def benchmarks():
    return {k:dict(measure=m,unit=u,value_decimal=v,release_id='a'*64,source_url='https://pages.stern.nyu.edu/',
                   classification='BENCHMARK_ASSUMPTION_NOT_COMPANY_FACT',selection_mode='HISTORICAL_PUBLISHED',published_at='2026-01-01')
            for k,m,u,v in [('wacc','wacc','fraction','0.1'),('tax_rate','tax_rate','fraction','0.25'),('sales_capital','sales_capital','ratio','2')]}


def test_actual_operating_inputs_value_enterprise_without_inventing_bridge():
    result=value_enterprise(document(),benchmarks(),[0]*5,0,.15,valuation_date='2026-09-24',suitable=True,evidence_secret=SECRET)
    assert result['enterprise_value']==pytest.approx(181.5)
    assert result['equity_value'] is None and result['intrinsic_value'] is None
    assert result['projections'][0]['UFCF']==pytest.approx(18.15)
    assert result['source']['release_id']=='r1'


def test_served_sales_capital_measure_name_is_accepted_and_other_names_are_not():
    # The published DDFI corpus names the sales/capital ratio `sales_to_invested_capital`; the
    # earlier file-based releases named the same measure, from the same source bytes,
    # `sales_capital`. The served name is recorded on the result as served, and a different
    # concept selected into the same target is still refused.
    served=benchmarks()
    served['sales_capital']=dict(served['sales_capital'],measure='sales_to_invested_capital')
    result=value_enterprise(document(),served,[0]*5,0,.15,valuation_date='2026-09-24',suitable=True,evidence_secret=SECRET)
    assert result['benchmark_assumptions']['sales_capital']['measure']=='sales_to_invested_capital'
    assert result['enterprise_value']==pytest.approx(181.5)
    wrong=benchmarks()
    wrong['sales_capital']=dict(wrong['sales_capital'],measure='net_capex_to_sales')
    with pytest.raises(ValueError,match='Explicit compatible benchmark required: sales_capital'):
        value_enterprise(document(),wrong,[0]*5,0,.15,valuation_date='2026-09-24',suitable=True,evidence_secret=SECRET)
    substituted=benchmarks()
    substituted['wacc']=dict(substituted['wacc'],measure='cost_of_equity')
    with pytest.raises(ValueError,match='Explicit compatible benchmark required: wacc'):
        value_enterprise(document(),substituted,[0]*5,0,.15,valuation_date='2026-09-24',suitable=True,evidence_secret=SECRET)


def complete_bridge(**overrides):
    bridge=dict(short_term_debt=10.0,long_term_debt=20.0,cash=5.0,preferred_equity=0.0,
                minority_interest=0.0,other_nonoperating_assets=1.0)
    bridge.update(overrides)
    return bridge


def test_equity_bridge_reports_every_missing_claim_and_never_zeroes_them():
    result=equity_bridge(dict(cash=35.9e9,short_term_debt=None,long_term_debt=None,
                              preferred_equity=None,minority_interest=None,
                              other_nonoperating_assets=None),181.5e9)
    assert result['status']=='UNAVAILABLE' and result['equity_value'] is None
    assert result['value_per_share'] is None
    assert set(result['missing'])=={'short_term_debt','long_term_debt','preferred_equity','minority_interest','other_nonoperating_assets','shares_outstanding'}


def test_equity_bridge_rejects_weighted_average_shares():
    with pytest.raises(ValueError, match='point-in-time'):
        equity_bridge(complete_bridge(),100.0,shares_outstanding=10.0,shares_basis='WEIGHTED_AVERAGE_DILUTED')


def test_equity_bridge_computes_per_share_only_when_complete():
    result=equity_bridge(complete_bridge(),100.0,shares_outstanding=10.0,shares_basis='COMMON_SHARES_OUTSTANDING')
    assert result['status']=='AVAILABLE' and result['missing']==[]
    # 100 + cash 5 + other 1 - debt 30 - preferred 0 - minority 0 = 76 equity
    assert result['equity_value']==pytest.approx(76.0)
    assert result['value_per_share']==pytest.approx(7.6)


def test_enterprise_result_keeps_equity_null_when_bridge_is_incomplete():
    result=value_enterprise(document(),benchmarks(),[0]*5,0,.15,valuation_date='2026-09-24',suitable=True,evidence_secret=SECRET)
    assert result['equity_value'] is None and result['intrinsic_value'] is None
    assert result['equity_bridge']['status']=='UNAVAILABLE'
    assert 'shares_outstanding' in result['equity_bridge']['missing']


def test_enterprise_requires_suitability_confirmation():
    with pytest.raises(ValueError):value_enterprise(document(),benchmarks(),[0]*5,0,.15,valuation_date='2026-09-24',suitable=False,evidence_secret=SECRET)


def test_future_benchmark_cannot_enter_a_historical_valuation():
    selected=benchmarks();selected['wacc']['published_at']='2027-01-01'
    with pytest.raises(ValueError):value_enterprise(document(),selected,[0]*5,0,.15,valuation_date='2026-09-24',suitable=True,evidence_secret=SECRET)


def test_unattested_or_tampered_caller_evidence_bundle_is_rejected():
    # 1. Missing attestation on a self-consistent forged bundle is rejected.
    unattested = document(secret=None)
    with pytest.raises(ValueError, match='unattested'):
        value_enterprise(unattested, benchmarks(), [0]*5, 0, .15, valuation_date='2026-09-24', suitable=True, evidence_secret=SECRET)

    # 2. Wrong server secret / forged HMAC is rejected.
    wrong_key = document(secret='attacker-secret')
    with pytest.raises(ValueError, match='attestation mismatch'):
        value_enterprise(wrong_key, benchmarks(), [0]*5, 0, .15, valuation_date='2026-09-24', suitable=True, evidence_secret=SECRET)

    # 3. Mutating native_history observations + source_records after server attestation is rejected.
    tampered = document(secret=SECRET)
    raw_page = tampered['source']['native_history'][0]
    rev_obs = next(r for r in raw_page['observations'] if r['metric'] == 'revenue' and r['period_end'] == '2024-12-31')
    forged_sid, forged_leaf = make_leaf(
        raw_page['cik'], 'Revenues', 'USD', 'USD',
        rev_obs['period_start'], rev_obs['period_end'], '999999', rev_obs['available_at']
    )
    rev_obs['value_decimal'] = '999999'
    rev_obs['source_observation_ids'] = [forged_sid]
    rev_obs['source_terms'] = [{'source_observation_id': forged_sid, 'coefficient': 1}]
    raw_page['source_records'][forged_sid] = forged_leaf
    with pytest.raises(ValueError, match='attestation mismatch'):
        value_enterprise(tampered, benchmarks(), [0]*5, 0, .15, valuation_date='2026-09-24', suitable=True, evidence_secret=SECRET)


def test_caller_edited_bridge_or_subject_cannot_alter_attested_result():
    base=value_enterprise(document(),benchmarks(),[0]*5,0,.15,valuation_date='2026-09-24',suitable=True,evidence_secret=SECRET)
    # Editing the caller-visible bridge does not change the verified cash used for the equity bridge.
    forged=document();forged['bridge']['cash']=1e15
    assert value_enterprise(forged,benchmarks(),[0]*5,0,.15,valuation_date='2026-09-24',suitable=True,evidence_secret=SECRET)['equity_bridge']['missing']==base['equity_bridge']['missing']
    # Changing the subject (ticker) invalidates the server signature over the evidence.
    relabelled=document();relabelled['company']['ticker']='MSFT'
    with pytest.raises(ValueError, match='attestation mismatch'):
        value_enterprise(relabelled,benchmarks(),[0]*5,0,.15,valuation_date='2026-09-24',suitable=True,evidence_secret=SECRET)


def test_valuation_date_before_financial_cutoff_is_rejected():
    with pytest.raises(ValueError, match='cutoff'):
        value_enterprise(document(),benchmarks(),[0]*5,0,.15,valuation_date='2026-01-01',suitable=True,evidence_secret=SECRET)


def test_calculate_enterprise_api_enforces_server_evidence_attestation(tmp_path, monkeypatch):
    from app import app
    import hashlib, json

    def encoded(v):
        return json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

    records = [
        {'subject': 'Software', 'measure': 'wacc', 'value_decimal': '0.1', 'unit': 'fraction',
         'classification': 'BENCHMARK_ASSUMPTION_NOT_COMPANY_FACT', 'source_cell': 'K3'},
        {'subject': 'Software', 'measure': 'tax_rate', 'value_decimal': '0.25', 'unit': 'fraction',
         'classification': 'BENCHMARK_ASSUMPTION_NOT_COMPANY_FACT', 'source_cell': 'E3'},
        {'subject': 'Software', 'measure': 'sales_capital', 'value_decimal': '2', 'unit': 'ratio',
         'classification': 'BENCHMARK_ASSUMPTION_NOT_COMPANY_FACT', 'source_cell': 'F3'},
    ]
    data = encoded({'schema_version': 'damodaran-assumptions-v1', 'dataset_id': 'cost_of_capital', 'region': 'US', 'records': records})
    raw = b'public source'
    manifest = {
        'schema_version': 'damodaran-assumptions-v1', 'dataset_id': 'cost_of_capital', 'region': 'US',
        'published_at': '2026-01-01', 'source_url': 'https://pages.stern.nyu.edu/~adamodar/pc/datasets/wacc.xls',
        'publication_evidence': {'method': 'FIRST_OBSERVED',
                                 'source_url': 'https://pages.stern.nyu.edu/~adamodar/datahistory.html',
                                 'observed_at': '2026-01-02T00:00:00Z'},
        'files': {'source.bin': hashlib.sha256(raw).hexdigest(), 'normalized.json': hashlib.sha256(data).hexdigest()},
    }
    rid = hashlib.sha256(encoded(manifest)).hexdigest()
    manifest['release_id'] = rid
    p = tmp_path / rid
    p.mkdir()
    (p / 'manifest.json').write_bytes(encoded(manifest))
    (p / 'normalized.json').write_bytes(data)
    (p / 'source.bin').write_bytes(raw)

    monkeypatch.setenv('DAMODARAN_RELEASE_ROOT', str(tmp_path))
    monkeypatch.setenv('ZION_HISTORY_TOKEN', SECRET)

    selections = {
        k: {'release_id': rid, 'subject': 'Software', 'measure': k, 'mode': 'historical'}
        for k in ('wacc', 'tax_rate', 'sales_capital')
    }
    today = datetime.now(timezone.utc).date().isoformat()
    client = app.test_client()

    # Forged / unattested payload is rejected with HTTP 400.
    bad_resp = client.post('/api/calculate/enterprise', json={
        'financials': document(secret=None),
        'valuation_date': today,
        'benchmark_selections': selections,
        'revenue_growth_rates': [0.0]*5,
        'terminal_growth': 0.0,
        'terminal_roic': 0.15,
        'suitable': True,
    })
    assert bad_resp.status_code == 400
    assert 'unattested' in bad_resp.json['error']

    # Server-attested payload succeeds.
    ok_resp = client.post('/api/calculate/enterprise', json={
        'financials': document(secret=SECRET),
        'valuation_date': today,
        'benchmark_selections': selections,
        'revenue_growth_rates': [0.0]*5,
        'terminal_growth': 0.0,
        'terminal_roic': 0.15,
        'suitable': True,
    })
    assert ok_resp.status_code == 200, ok_resp.json
    assert ok_resp.json['enterprise_value'] == pytest.approx(181.5)



def test_enterprise_uses_verified_latest_year_even_when_other_years_are_missing():
    full = document()
    pages = deepcopy(full['source']['native_history'])
    latest = max(row['period_end'] for row in pages[0]['observations'])
    pages[0]['observations'] = [row for row in pages[0]['observations'] if row['period_end'] == latest]
    sparse = history_document(pages, 'AAPL', '2026-09-24', pages[0]['cik'])
    sparse['source']['evidence_attestation'] = sign_evidence(pages, 'AAPL', '2026-09-24', pages[0]['cik'], SECRET)
    result = value_enterprise(sparse, benchmarks(), [0]*5, 0, .15,
                              valuation_date='2026-09-24', suitable=True, evidence_secret=SECRET)
    assert result['enterprise_value'] == pytest.approx(181.5)
    assert result['source']['history_coverage']['observed_periods'] == 1
    assert result['source']['history_coverage']['missing_periods_imputed'] is False
    assert result['intrinsic_value'] is None
