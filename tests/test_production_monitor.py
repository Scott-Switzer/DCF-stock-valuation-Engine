import io
from pathlib import Path
import runpy
import zipfile

from app import app
from dcf_loader import demo_document
from scripts import smoke_public


def mock_public(monkeypatch, *, corrupt=False, stale=False):
    client = app.test_client()
    doc = demo_document()
    doc['company']['ticker'] = 'AAPL'
    doc['source']['kind'] = 'api'
    from datetime import date

    doc['valuation_date'] = date.today().isoformat()
    for row in doc['historical']:
        row['available_at'] = date.today().isoformat()
    if not stale:
        doc['market']['price_as_of'] = date.today().isoformat()
    original = smoke_public.fetch

    def fetch(base, path, *, timeout, payload=None, maximum=2_000_000):
        import json

        if path == '/api/load/dcf':
            return json.dumps({'financials':doc}).encode(), 0.1
        if path == '/api/search?q=AAPL':
            return b'[{"symbol":"AAPL"}]', 0.1
        if path == '/api/preview/dcf' and payload['financials']['company']['ticker'] == 'AAPL' and corrupt:
            response = client.post(path, json=payload).get_json()
            response['intrinsic_value'] += 1
            return json.dumps(response).encode(), 0.1
        response = client.get(path) if payload is None else client.post(path, json=payload)
        assert response.status_code == 200, response.data
        return response.data, 0.1

    monkeypatch.setattr(smoke_public, 'fetch', fetch)
    assert original is not fetch


def test_real_company_monitor_reconciles_non_saving_preview_and_workbook(monkeypatch):
    mock_public(monkeypatch)
    results = smoke_public.run('https://unit.invalid', 10, real_ticker='AAPL', max_financial_age=10000)
    assert all(r['status'] == 'PASS' for r in results), results
    assert {'real_dcf_arithmetic', 'real_xlsx_export', 'source_freshness'} <= {r['check'] for r in results}


def test_monitor_detects_math_regression(monkeypatch):
    mock_public(monkeypatch, corrupt=True)
    results = smoke_public.run('https://unit.invalid', 10, real_ticker='AAPL', max_financial_age=10000)
    failed = next(r for r in results if r['check'] == 'real_dcf_arithmetic')
    assert failed['status'] == 'FAIL'
    mismatch = next(d for d in failed['differences'] if d['field'] == 'intrinsic_value')
    assert mismatch['actual'] == mismatch['expected'] + 1


def test_monitor_detects_stale_market_source_and_wrong_release(monkeypatch):
    mock_public(monkeypatch, stale=True)
    results = smoke_public.run('https://unit.invalid', 10, real_ticker='AAPL', expected_commit='wrong', max_price_age=0)
    health = next(r for r in results if r['check'] == 'health')
    assert health['status'] == 'FAIL'
    assert health['release']['commit'] == 'local'
    assert health['release']['tracked_dirty'] is True
    assert any('freshness' in r.get('detail', '') for r in results)


def test_generated_worker_build_identity_and_stale_module_cleanup():
    root = Path(__file__).resolve().parents[1]
    stale = root / 'worker_runtime/obsolete_test_module.py'
    stale.parent.mkdir(exist_ok=True)
    stale.write_text('unused = True\n')
    runpy.run_path(str(root / 'scripts/embed_assets.py'))
    assert not stale.exists()
    generated = runpy.run_path(str(root / 'embedded_assets.py'))
    assert len(generated['BUILD']['commit']) == 40
    assert len(generated['BUILD']['asset_sha256']) == 64
    assert isinstance(generated['BUILD']['tracked_dirty'], bool)


def test_export_is_formula_workbook():
    client = app.test_client()
    response = client.post('/export/xlsx', json={'financials':demo_document(), 'assumptions':smoke_public.ASSUMPTIONS})
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.data)) as workbook:
        assert any(b'<f>' in workbook.read(p) for p in workbook.namelist() if p.startswith('xl/worksheets/'))
