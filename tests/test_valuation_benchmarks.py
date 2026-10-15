import hashlib
import json
import pytest
from valuation_benchmarks import load_benchmark, apply_benchmarks
from dcf_code import discount_fcff


def release(tmp_path, published=None):
    def encoded(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    data=encoded({'schema_version':'damodaran-assumptions-v1','dataset_id':'cost_of_capital','region':'US',
                  'records':[{'subject':'Software','measure':'wacc','value_decimal':'0.08','unit':'fraction',
                              'classification':'BENCHMARK_ASSUMPTION_NOT_COMPANY_FACT','source_cell':'K3'}]})
    raw=b'public source'
    manifest={'schema_version':'damodaran-assumptions-v1','dataset_id':'cost_of_capital','region':'US',
              'published_at':published,'source_url':'https://pages.stern.nyu.edu/~adamodar/pc/datasets/wacc.xls',
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
    with pytest.raises(ValueError):load_benchmark(tmp_path,rid,'Software','wacc',as_of='2025-01-01')


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
