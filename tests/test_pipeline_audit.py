from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app import app
from company_packets import assemble_packet, transport_evidence
from dcf_loader import demo_document, ProviderError
import ppe_provider
from scripts import audit_pipeline as audit
from tests.test_ppe_packets import packet


@pytest.mark.parametrize('outcome,state', [('missing', 'NOT_FOUND'), ('error', 'ERROR'), ('absent', 'NOT_CONFIGURED')])
def test_r2_receipt_preserves_service_outcome(monkeypatch, outcome, state):
    env = SimpleNamespace(PPE_DATA=object())
    if outcome != 'absent':
        env.ZION_VALUATIONS = object()
    monkeypatch.setitem(app.config, 'CLOUDFLARE', True)
    key = 'gold/valuation/releases/' + 'a' * 64 + '/companies/AAPL.json'
    pointer = {'schema_version': 'ppe-valuation-index-v1', 'companies': {'AAPL': {'key': key, 'sha256': 'b' * 64}}}
    with app.test_request_context(environ_overrides={'workers.env': env}):
        with patch('ppe_provider._service_packet', return_value=None, side_effect=ProviderError('Unavailable') if outcome == 'error' else None):
            with patch('ppe_provider._object_json', side_effect=[pointer, packet()]):
                result = ppe_provider.load_packet('AAPL', '2026-10-10')
    receipt = result['source']['transport_receipt']
    assert receipt['kind'] == 'DIRECT_R2' and receipt['service_state'] == state
    assert receipt['storage_cache'] == 'NOT_ESTABLISHED' and receipt['origin_seconds'] >= 0


def test_service_receipt_is_request_scoped_and_r2_not_read(monkeypatch):
    monkeypatch.setitem(app.config, 'CLOUDFLARE', True)
    env = SimpleNamespace(ZION_VALUATIONS=object(), PPE_DATA=object())
    with app.test_request_context(environ_overrides={'workers.env': env}):
        with patch('ppe_provider._service_packet', return_value=packet()):
            with patch('ppe_provider._object_json') as r2:
                result = ppe_provider.load_packet('AAPL', '2026-10-10')
    r2.assert_not_called()
    assert result['source']['transport_receipt']['service_state'] == 'SUCCESS'
    assert result['source']['transport_receipt']['kind'] == 'ZION_SERVICE_BINDING'


def test_assembly_hit_does_not_claim_current_service_invocation():
    doc = demo_document()
    doc['source']['ppe_release'] = {'transport': 'Zion private service binding', 'release_id': 'r'}
    evidence = transport_evidence(doc, {'state': 'HIT'})
    assert evidence['request_path'] == 'ASSEMBLY_CACHE'
    assert evidence['snapshot_origin'] == 'ZION_SERVICE_BINDING'
    assert evidence['receipt_basis'] == 'LEGACY_LABEL'
    assert transport_evidence({'source': {'ppe_status': 'No packet; Yahoo fallback.'}})['snapshot_origin'] == 'BASELINE_ONLY'
    assert transport_evidence(demo_document())['snapshot_origin'] == 'UNKNOWN'
    p = assemble_packet({'financials': doc, 'load_summary': {'assembly_cache': {'state': 'HIT'}}})
    assert p['transport'] == evidence
    assert p['independent_source_verification'] == 'NOT_ESTABLISHED'


def test_packet_routes_cache_public_packets_and_sample(monkeypatch, tmp_path):
    monkeypatch.setitem(app.config, 'STATE_PATH', str(tmp_path / 'state.sqlite3'))
    monkeypatch.setattr('company_packets.load_company_packet', lambda *a: {'status': 'BLOCKED'})
    monkeypatch.setattr(ppe_provider, 'load_packet', lambda *a: packet())
    with app.test_client() as client:
        for path in ['/api/company/AAPL', '/api/company/AAPL/packet']:
            assert client.get(path).headers['Cache-Control'].startswith('public, max-age=300')
        assert 'public' in client.get('/api/sample').headers['Cache-Control']


def test_percentile_and_failed_samples_are_not_hidden():
    assert audit.distribution([])['p95_seconds'] is None
    assert audit.percentile(list(range(1, 21)), .95) == 19
    groups = audit.summarize([
        {'endpoint': 'compact', 'status': 'PASS', 'seconds': .2},
        {'endpoint': 'compact', 'status': 'FAIL', 'seconds': 30},
    ])['compact:NOT_APPLICABLE']
    assert groups['attempts'] == 2 and groups['failures'] == 1
    assert groups['successful_latency']['p95_seconds'] == .2
    assert groups['failed_latency']['max_seconds'] == 30


@pytest.mark.parametrize('mutate', ['ticker', 'unit', 'future', 'nan'])
def test_bad_compact_contract_fails_even_with_200(mutate):
    p = packet()
    if mutate == 'ticker': p['ticker'] = 'MSFT'
    if mutate == 'unit': p['historical'][0]['fields']['revenue']['unit'] = 'EUR'
    if mutate == 'future': p['cutoff_date'] = '2099-01-01'
    if mutate == 'nan': p['historical'][0]['fields']['revenue']['value'] = float('nan')
    record = {'status': 'PASS', 'seconds': 1}
    audit.contract_record(record, p, 'compact', 'AAPL', '2026-10-10')
    assert record['status'] == 'FAIL'


def test_outer_cache_is_not_fresh_invocation_evidence():
    p = packet()
    p['source']['transport'] = 'Zion private service binding'
    for headers, expected in [({'Cache-Control': 'no-store'}, 'RESPONSE_ORIGIN_RECEIPT'),
                              ({'Cache-Control': 'no-store', 'Age': '1'}, 'CACHED_SNAPSHOT_ORIGIN_ONLY'),
                              ({'CF-Cache-Status': 'HIT'}, 'CACHED_SNAPSHOT_ORIGIN_ONLY'),
                              ({}, 'REPORTED_ORIGIN_OUTER_CACHE_NOT_EXCLUDED')]:
        record = {'status': 'PASS', 'headers': headers}
        audit.contract_record(record, p, 'compact', 'AAPL', '2026-10-10')
        assert record['invocation_evidence'] == expected


class Response:
    def __init__(self, body, status=200, content_type='application/json'):
        self.body, self.status_code = body, status
        self.headers = {'Content-Type': content_type}
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def iter_content(self, size): yield self.body


@pytest.mark.parametrize('response', [Response(b'{}', 429), Response(b'{'), Response(b'{"x":NaN}'),
                                       Response(b'[]'), Response(b'{}', content_type='text/html'),
                                       Response(b'{"saved_record_id":1}'), Response(b'x' * (audit.MAXIMUM + 1))])
def test_http_errors_and_invalid_or_oversized_bodies_retained(response):
    session = SimpleNamespace(request=lambda *a, **kw: response)
    client = audit.Client('http://127.0.0.1:5001', 1, 0, session=session)
    record, value = client.fetch('/api/company/AAPL')
    assert value is None and record['status'] == 'FAIL' and record['seconds'] >= 0


class FakeClient:
    base, delay, timeout = 'http://127.0.0.1:5001', 7, 1
    def __init__(self, *, mismatch=False, changed_release=False):
        self.calls, self.mismatch, self.changed_release = [], mismatch, changed_release
        self.doc = demo_document()
        self.doc['company']['ticker'] = 'AAPL'
        self.doc['valuation_date'] = '2026-10-10'
        self.doc['source']['kind'] = 'api'
        for row in self.doc['historical']:
            row['available_at'] = '2026-10-10'
        self.doc['source']['ppe_release'] = {'transport': 'Zion private service binding'}
    def fetch(self, path, payload=None):
        self.calls.append((path, payload))
        if path == '/health':
            value = {'status': 'healthy', 'release': {'commit': 'b' if self.changed_release and len(self.calls) > 1 else 'a'}}
        elif path == '/ready': value = {'status': 'ready'}
        elif path.endswith('/packet?as_of=2026-10-10'):
            value = assemble_packet({'financials': self.doc}, ticker='AAPL', asof='2026-10-10')
        elif path.startswith('/api/company/'):
            value = packet(); value['source']['transport'] = 'Zion private service binding'
        elif path == '/api/load/dcf': value = {'financials': deepcopy(self.doc)}
        else:
            from app import evaluate, assumptions_from_json
            value = evaluate(payload['financials'], assumptions_from_json(payload['assumptions']))
            if self.mismatch: value['intrinsic_value'] += 1
        return {'path': path, 'seconds': .1, 'status': 'PASS', 'headers': {'Cache-Control': 'no-store'}}, value


def test_full_audit_only_calls_non_saving_interfaces_and_writes_reports(tmp_path):
    client = FakeClient()
    report = audit.run(client, ['AAPL'], '2026-10-10', 2, flow=True, require_zion=True)
    assert report['status'] == 'PASS'
    assert report['target_acceptance'].startswith('NOT_ESTABLISHED')
    assert all(path in {'/health', '/ready', '/api/load/dcf', '/api/preview/dcf'} or path.startswith('/api/company/') for path, _ in client.calls)
    assert report['summary']['load_preview_flow:UNKNOWN']['successful_latency']['p95_seconds'] == .2
    path = tmp_path / 'audit.json'
    audit.write_json_atomic(path, report)
    assert json.loads(path.read_text())['schema_version'] == audit.VERSION
    assert 'NOT ESTABLISHED' in audit.markdown(report)


@pytest.mark.parametrize('kwargs', [{'mismatch': True}, {'changed_release': True}])
def test_arithmetic_or_release_mismatch_fails_run(kwargs):
    report = audit.run(FakeClient(**kwargs), ['AAPL'], '2026-10-10', 1, flow=True)
    assert report['status'] == 'FAIL'


@pytest.mark.parametrize('args', [['--base', 'https://user:secret@example.com'], ['--base', 'http://example.com'],
                                  ['--samples', '0'], ['--delay', 'nan'], ['--delay', '1'], ['--tickers', '']])
def test_invalid_cli_inputs_rejected_without_network(tmp_path, args):
    with pytest.raises(SystemExit) as exc:
        audit.main(['--output', str(tmp_path / 'audit.json'), *args])
    assert exc.value.code == 2


def test_output_must_not_overwrite_json_with_markdown(tmp_path):
    with pytest.raises(SystemExit) as exc:
        audit.main(['--output', str(tmp_path / 'audit.md')])
    assert exc.value.code == 2
    assert not (tmp_path / 'audit.md').exists()


def test_empty_health_and_readiness_cannot_pass():
    class MissingHealth(FakeClient):
        def fetch(self, path, payload=None):
            record, value = super().fetch(path, payload)
            return record, {} if path in {'/health', '/ready'} else value
    report = audit.run(MissingHealth(), ['AAPL'], '2026-10-10', 1)
    assert report['status'] == 'FAIL'
    assert len([r for r in report['records'] if r['status'] == 'FAIL']) == 3
