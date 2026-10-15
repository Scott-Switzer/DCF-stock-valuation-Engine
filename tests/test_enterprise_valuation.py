from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import pytest
from test_zion_history_provider import make_leaf, page
from zion_history_provider import history_document, sign_evidence
from enterprise_valuation import value_enterprise

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

