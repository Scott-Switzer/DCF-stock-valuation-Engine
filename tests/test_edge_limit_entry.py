"""The entrypoint limiter is what the Pyodide WSGI hook cannot be: awaited."""
import asyncio
import sys
from types import SimpleNamespace

import pytest


class _Response:
    def __init__(self, body=None, status=200, headers=None):
        self.body, self.status, self.headers = body, status, headers or {}


@pytest.fixture(autouse=True)
def _workers_module():
    previous = sys.modules.get('workers')
    sys.modules['workers'] = SimpleNamespace(Response=_Response)
    sys.modules.pop('edge_limits', None)
    try:
        yield
    finally:
        sys.modules.pop('edge_limits', None)
        if previous is not None:
            sys.modules['workers'] = previous


class _HTTPMethod:
    """Mirrors workers' HTTPMethod enum: str() is not the method name."""

    def __init__(self, name):
        self.value = name

    def __str__(self):
        return '<HTTPMethod.' + str(self.value) + '>'


@pytest.mark.parametrize('value,expected', [
    ('GET', 'GET'),
    ('post', 'POST'),
    (_HTTPMethod('GET'), 'GET'),
    (_HTTPMethod('DELETE'), 'DELETE'),
    (SimpleNamespace(value='POST'), 'POST'),
])
def test_request_method_normalises_the_runtime_enum(value, expected):
    from edge_limits import request_method
    assert request_method(value) == expected


def request(path, method='GET', ip='203.0.113.9'):
    return SimpleNamespace(
        url='https://dcf.example' + path,
        method=method,
        headers=SimpleNamespace(get=lambda name: ip if name == 'CF-Connecting-IP' else None),
    )


def env(binding=None, name='REFERENCE_LIMIT', salt='test-only-salt', environment='staging'):
    values = {'RECORD_SALT': salt, 'DEPLOY_ENVIRONMENT': environment}
    if binding is not None:
        values[name] = binding
    return SimpleNamespace(**values)


def enforce(target_env, target_request):
    from edge_limits import enforce as run
    return asyncio.run(run(target_env, target_request))


@pytest.mark.parametrize('path,method,binding', [
    ('/api/references/AAPL', 'GET', 'REFERENCE_LIMIT'),
    ('/api/data/query', 'GET', 'REFERENCE_LIMIT'),
    ('/api/company/AAPL/packet', 'GET', 'REFERENCE_LIMIT'),
    ('/research/report/export/xlsx', 'GET', 'REFERENCE_LIMIT'),
    ('/mcp', 'POST', 'MCP_LIMIT'),
    ('/api/preview/dcf', 'POST', 'PREVIEW_LIMIT'),
    ('/api/watchlist', 'DELETE', 'WRITE_LIMIT'),
    ('/api/load/dcf', 'POST', 'WRITE_LIMIT'),
    ('/', 'GET', None),
    ('/api/search', 'GET', None),
])
def test_binding_name(path, method, binding):
    from edge_limits import binding_name
    assert binding_name(path, method) == binding


def test_allows_within_limit():
    calls = []

    async def limit(payload):
        calls.append(payload)
        return SimpleNamespace(success=True)

    assert enforce(env(SimpleNamespace(limit=limit)), request('/api/references/AAPL')) is None
    assert calls[0]['key'].startswith('dcf:edge:')
    assert 'test-only-salt' not in calls[0]['key']
    assert '203.0.113.9' not in calls[0]['key']


def test_blocks_over_limit():
    async def limit(payload):
        return SimpleNamespace(success=False)

    response = enforce(env(SimpleNamespace(limit=limit)), request('/api/data/query'))
    assert response.status == 429
    assert 'Too many requests' in response.body


def test_unlimited_path_never_calls_binding():
    async def limit(payload):
        raise AssertionError('unlimited path must not be counted')

    assert enforce(env(SimpleNamespace(limit=limit)), request('/')) is None


def test_missing_binding_and_errors_fail_open():
    async def broken(payload):
        raise RuntimeError('binding unavailable')

    assert enforce(env(), request('/api/data/query')) is None
    assert enforce(env(SimpleNamespace(limit=broken)), request('/api/data/query')) is None
