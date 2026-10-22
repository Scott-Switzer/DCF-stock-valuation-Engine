import pytest
from model_bundle import stamp_model_result

SNAPSHOT = {'bundle_id': 'a'*64, 'source_releases': {'SEC': 'sec-original'}}


def model():
    return {'financials': {'source': {'name': 'live-provider', 'field_coverage': [{'field':'market.price','provider':'live-provider','period_end':'2026-10-21','status':'fallback','value':100}]},
                            'historical': [{'period_end': '2025-12-31'}], 'market': {'price':100,'price_as_of': '2026-10-21'}},
            'form': {'wacc':'10'}, 'preview': {'forecast': [{'period_end': '2030-12-31'}]}}


def test_mixed_model_keeps_functionality_and_records_exact_inputs():
    original = model()
    result = stamp_model_result(original, SNAPSHOT)
    assert result['bundle_id'] == SNAPSHOT['bundle_id']
    assert result['data_as_of'] == '2026-10-21'
    assert result['financials'] == original['financials']
    assert result['input_snapshot_id'] == stamp_model_result(model(), SNAPSHOT)['input_snapshot_id']
    assert result['input_provenance']['outside_bundle'][0]['provider'] == 'live-provider'
    assert result['input_provenance']['outside_bundle'][0]['data_as_of'] == '2026-10-21'
    assert {'financials', 'form'} <= {r['field'] for r in result['input_provenance']['outside_bundle']}
    changed = model(); changed['financials']['market']['price'] = 101
    assert stamp_model_result(changed, SNAPSHOT)['input_snapshot_id'] != result['input_snapshot_id']
    changed = model(); changed['form']['wacc'] = '11'
    assert stamp_model_result(changed, SNAPSHOT)['input_snapshot_id'] != result['input_snapshot_id']
    # Calculated forecasts are outputs, never evidence of source freshness.
    changed = model(); changed['preview'] = {'forecast':[{'period_end':'2040-12-31'}]}
    assert stamp_model_result(changed, SNAPSHOT)['input_snapshot_id'] == result['input_snapshot_id']


def test_mixed_model_still_rejects_another_stored_bundle():
    with pytest.raises(ValueError, match='RELEASE_MISMATCH'):
        stamp_model_result({**model(), 'bundle_id':'b'*64}, SNAPSHOT)


def test_existing_model_endpoint_preserves_live_inputs_and_returns_the_receipt(monkeypatch):
    import company_packets
    import model_bundle
    from app import app
    monkeypatch.setattr(model_bundle, 'read_snapshot', lambda env: SNAPSHOT)
    monkeypatch.setattr(company_packets, 'load_cached_method', lambda *args, **kwargs: model())
    response = app.test_client().post('/api/load/dcf', json={'ticker':'TEST'}, headers={'x-zion-bundle-id':SNAPSHOT['bundle_id']})
    assert response.status_code == 200
    data = response.get_json()
    assert data['financials']['market']['price'] == 100
    assert data['input_snapshot_id'] == stamp_model_result(model(), SNAPSHOT)['input_snapshot_id']
    mismatch = app.test_client().post('/api/load/dcf', json={'ticker':'TEST'}, headers={'x-zion-bundle-id':'b'*64})
    assert mismatch.status_code == 409
    assert mismatch.get_json()['error'] == 'RELEASE_MISMATCH'
