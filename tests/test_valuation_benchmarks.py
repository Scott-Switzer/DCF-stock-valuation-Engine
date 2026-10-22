import hashlib
import json
import pytest
from valuation_benchmarks import load_benchmark, apply_benchmarks
from dcf_code import discount_fcff


def release(tmp_path, published=None, evidence=None):
    def encoded(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    data=encoded({'schema_version':'damodaran-assumptions-v1','dataset_id':'cost_of_capital','region':'US',
                  'records':[{'subject':'Software','measure':'wacc','value_decimal':'0.08','unit':'fraction',
                              'classification':'BENCHMARK_ASSUMPTION_NOT_COMPANY_FACT','source_cell':'K3'}]})
    raw=b'public source'
    manifest={'schema_version':'damodaran-assumptions-v1','dataset_id':'cost_of_capital','region':'US',
              'published_at':published,'publication_evidence':evidence,
              'source_url':'https://pages.stern.nyu.edu/~adamodar/pc/datasets/wacc.xls',
              'files':{'source.bin':hashlib.sha256(raw).hexdigest(),'normalized.json':hashlib.sha256(data).hexdigest()}}
    rid=hashlib.sha256(encoded(manifest)).hexdigest();manifest['release_id']=rid
    p=tmp_path/rid;p.mkdir();(p/'manifest.json').write_bytes(encoded(manifest));(p/'normalized.json').write_bytes(data);(p/'source.bin').write_bytes(raw)
    return rid


def test_selects_explicit_assumption_with_hash_and_unit(tmp_path):
    rid=release(tmp_path)
    selected=load_benchmark(tmp_path,rid,'Software','wacc')
    assert selected['value_decimal']=='0.08'
    result=apply_benchmarks({'revenue_growth_rates':[.05]*5}, {'wacc_override':selected})
    assert result['wacc_override']==.08
    assert result['benchmark_sources']['wacc_override']['release_id']==rid


def test_unknown_publication_cannot_be_backdated(tmp_path):
    rid=release(tmp_path)
    with pytest.raises(ValueError,match='NO_PUBLICATION_DATE'):
        load_benchmark(tmp_path,rid,'Software','wacc',as_of='2025-01-01')


def evidence(observed='2026-01-06T12:00:00Z'):
    return {'method':'FIRST_OBSERVED','source_url':'https://pages.stern.nyu.edu/~adamodar/datahistory.html',
            'observed_at':observed}


def test_a_publication_date_without_evidence_cannot_be_used_historically(tmp_path):
    rid=release(tmp_path,published='2026-01-05')
    assert load_benchmark(tmp_path,rid,'Software','wacc')['published_at']=='2026-01-05'
    with pytest.raises(ValueError,match='NO_REVIEWED_PUBLICATION_EVIDENCE'):
        load_benchmark(tmp_path,rid,'Software','wacc',as_of='2026-02-01')


def test_reviewed_evidence_enables_historical_selection_after_publication(tmp_path):
    rid=release(tmp_path,published='2026-01-05',evidence=evidence())
    selected=load_benchmark(tmp_path,rid,'Software','wacc',as_of='2026-02-01')
    assert selected['selection_mode']=='HISTORICAL_PUBLISHED'
    assert selected['publication_method']=='FIRST_OBSERVED'
    with pytest.raises(ValueError,match='published after cutoff'):
        load_benchmark(tmp_path,rid,'Software','wacc',as_of='2026-01-04')


def test_tampered_release_is_rejected(tmp_path):
    rid=release(tmp_path);(tmp_path/rid/'normalized.json').write_text('{}')
    with pytest.raises(ValueError):load_benchmark(tmp_path,rid,'Software','wacc')


def test_existing_dcf_discount_core_values_five_periods_without_bridge():
    rows=[{'Year':y,'UFCF':100,'NOPAT':120} for y in range(1,6)]
    result=discount_fcff(rows,.10,0)
    assert result['enterprise_value']==pytest.approx(1000)
    assert 'intrinsic_value' not in result


def test_normalized_terminal_requires_explicit_roic():
    rows=[{'Year':y,'UFCF':100,'NOPAT':120} for y in range(1,6)]
    with pytest.raises(ValueError):discount_fcff(rows,.1,.02,terminal_mode='normalized')


def test_benchmark_cannot_silently_override_an_existing_assumption(tmp_path):
    rid=release(tmp_path);selected=load_benchmark(tmp_path,rid,'Software','wacc')
    with pytest.raises(ValueError):apply_benchmarks({'wacc_override':.12},{'wacc_override':selected})


def test_existing_calculate_api_consumes_selected_benchmark(tmp_path,monkeypatch):
    from app import app
    from dcf_loader import demo_document
    rid=release(tmp_path);monkeypatch.setenv('DAMODARAN_RELEASE_ROOT',str(tmp_path))
    doc=demo_document()
    doc['valuation_date']=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).date().isoformat()
    response=app.test_client().post('/api/calculate',json={'financials':doc,
        'assumptions':{'revenue_growth_rates':[.05]*5,'terminal_growth_rate':.02},
        'benchmark_selections':{'wacc_override':{'release_id':rid,'subject':'Software','measure':'wacc','mode':'current'}}})
    assert response.status_code==200, response.json
    assert response.json['wacc']==.08


def test_assumption_api_exposes_versioned_record(tmp_path,monkeypatch):
    from app import app
    rid=release(tmp_path);monkeypatch.setenv('DAMODARAN_RELEASE_ROOT',str(tmp_path))
    response=app.test_client().get('/api/assumptions/damodaran/'+rid+'?subject=Software&measure=wacc&mode=current')
    assert response.status_code==200
    assert response.json['release_id']==rid


def test_incomplete_evidence_is_reported_as_incomplete(tmp_path):
    rid=release(tmp_path,published='2026-01-05',evidence={'method':'FIRST_OBSERVED'})
    with pytest.raises(ValueError,match='INCOMPLETE_PUBLICATION_EVIDENCE'):
        load_benchmark(tmp_path,rid,'Software','wacc',as_of='2026-02-01')


def test_selected_wacc_cannot_be_overwritten_by_recalculated_mode(tmp_path,monkeypatch):
    from datetime import datetime,timezone
    from app import app
    from dcf_loader import demo_document
    rid=release(tmp_path);monkeypatch.setenv('DAMODARAN_RELEASE_ROOT',str(tmp_path))
    doc=demo_document();doc['valuation_date']=datetime.now(timezone.utc).date().isoformat()
    doc['source']['capital_costs']={'market_equity_value':1000,'debt':200,'cost_of_equity':.1,
                                  'cost_of_debt':.05,'tax_rate':.21,'wacc':.09}
    response=app.test_client().post('/api/calculate',json={'financials':doc,
        'assumptions':{'revenue_growth_rates':[.05]*5,'terminal_growth_rate':.02,'wacc_mode':'recalculated'},
        'benchmark_selections':{'wacc_override':{'release_id':rid,'subject':'Software','measure':'wacc','mode':'current'}}})
    assert response.status_code==400
    assert 'WACC' in response.json['error']
