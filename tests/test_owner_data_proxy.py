"""The production-origin proxy must never turn DCF access into data-owner access."""
import asyncio
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import owner_data_proxy as proxy


class Headers(dict):
    def get(self, key, default=None):
        return super().get(key.lower(), default)


class Request:
    def __init__(self, url, method='GET', headers=None, **kwargs):
        self.url, self.method = url, method
        self.headers = Headers({k.lower(): v for k, v in (headers or {}).items()})
        self.js_object = self
        self.options = kwargs


class Response:
    def __init__(self, body=None, status=200, headers=None):
        self.body, self.status = body, status
        self.headers = Headers(headers or {})


class Source:
    def __init__(self, status=206):
        self.requests = []
        self.stream = object()
        self.status = status

    async def fetch(self, request):
        self.requests.append(request)
        return Response(self.stream, self.status, {
            'content-type': 'application/octet-stream', 'content-range': 'bytes 0-3/9000000',
            'etag': '"pin"', 'cache-control': 'public,max-age=9999',
            'set-cookie': 'bad=source', 'access-control-allow-origin': '*',
            'location': 'https://other.invalid', 'vary': 'Cookie',
        })


@pytest.fixture(autouse=True)
def worker_sdk(monkeypatch):
    monkeypatch.setitem(sys.modules, 'workers', SimpleNamespace(Request=Request, Response=Response))


def fetch(path='/api/data/historical-series', headers=None, method='GET', source=None):
    source = source or Source()
    env = SimpleNamespace(ZION_FINANCIAL_QUERY=source, ZION_PRIVATE_API_TOKEN='server-owner',
                          ZION_SERVICE_TOKEN='server-service', ZION_HISTORY_TOKEN='server-history')
    request = Request('https://dcf.invalid' + path, method, headers)
    return asyncio.run(proxy.handle(request, env)), source


@pytest.mark.parametrize('headers', [None, {'Cookie': 'session=owner'}, {'Authorization': 'Basic abc'},
    {'Authorization': 'Bearer '}, {'Authorization': 'Bearer abc def'},
    {'Authorization': 'Bearer abc\r\nX-Owner: yes'}, {'X-Zion-Principal': 'private-owner'}])
@pytest.mark.parametrize('prefix', ['/api/data', '/private/v1'])
def test_no_bearer_rejected_without_using_any_server_credential(headers, prefix):
    response, source = fetch(prefix + '/historical-series', headers=headers)
    assert response.status == 401
    assert source.requests == []
    assert response.headers['cache-control'] == 'private, no-store'
    assert response.headers['vary'] == 'Authorization'


@pytest.mark.parametrize('method', ['POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def test_non_read_methods_never_reach_source(method):
    response, source = fetch(headers={'Authorization': 'Bearer incoming-owner'}, method=method)
    assert response.status == 405
    assert not source.requests


@pytest.mark.parametrize('path', ['/api/data/../equity-claims', '/api/data/datasets//financial/object',
    '/api/data/%2e%2e/research-prices', '/api/data/%252e%252e/research-prices',
    '/api/data/research-prices%2fextra', '/api/data/https://evil.invalid',
    '/api/data/datasets\\financial\\object', '/api/data/financial-jobs', '/api/data/query',
    '/api/data/datasets/unknown/action'])
def test_route_escapes_and_non_allowlisted_paths_never_reach_source(path):
    response, source = fetch(path, {'Authorization': 'Bearer incoming-owner'})
    assert response.status in (400, 404)
    assert not source.requests


@pytest.mark.parametrize('query', ['?limit=1&limit=2', '?cursor=' + 'x' * 4097,
    '?url=https://evil.invalid', '?authorization=secret', '?x=' + 'a' * 8200,
    '?search=%0d%0afoo', '?search=%ZZ', '?search=%FF', '?' + '&'.join('k'+str(i)+'=x' for i in range(33))])
def test_unbounded_or_credential_query_refused(query):
    response, source = fetch('/api/data/research-prices' + query,
                             {'Authorization': 'Bearer incoming-owner'})
    assert response.status == 400
    assert not source.requests


def test_exact_owner_and_query_forwarded_with_no_privilege_escalation_or_public_cache():
    query = '?path=private%2Ffile.parquet&offset=0&length=4'
    response, source = fetch('/api/data/datasets/research/object' + query, {
        'Authorization': 'Bearer incoming-owner', 'Cookie': 'session=admin',
        'If-Match': '"pin"', 'Range': 'bytes=0-3', 'X-Zion-Principal': 'private-owner',
        'X-Zion-Service-Token': 'attack', 'Origin': 'https://public.invalid',
    })
    request = source.requests[0]
    assert request.url == 'https://zion.internal/private/v1/datasets/research/object' + query
    assert request.method == 'GET'
    assert request.headers == {'authorization': 'Bearer incoming-owner', 'if-match': '"pin"',
                               'range': 'bytes=0-3'}
    assert request.options['redirect'] == 'manual'
    assert response.status == 206
    assert response.body is source.stream
    assert response.headers == {'content-type': 'application/octet-stream',
        'content-range': 'bytes 0-3/9000000', 'etag': '"pin"',
        'cache-control': 'private, no-store', 'vary': 'Authorization',
        'x-content-type-options': 'nosniff'}


@pytest.mark.parametrize('route,target', [('catalog', 'datasets/catalog'),
    ('datasets', 'datasets'), ('readiness', 'readiness'),
    ('historical-series', 'historical-series'), ('research-prices', 'research-prices'),
    ('financial-history', 'financial-history'), ('stock-history', 'stock-history'),
    ('datasets/financial-query', 'datasets/financial-query'),
    ('datasets/catalog/' + 'a' * 32, 'datasets/catalog/' + 'a' * 32)])
def test_allowed_routes_preserve_source_identity(route, target):
    response, source = fetch('/api/data/' + route, {'Authorization': 'Bearer owner'})
    assert source.requests[0].url == 'https://zion.internal/private/v1/' + target
    assert response.status == 206


@pytest.mark.parametrize('prefix', ['/api/data', '/private/v1'])
def test_source_authentication_failure_is_preserved_and_head_has_no_body(prefix):
    response, source = fetch(prefix + '/historical-series',
                             headers={'Authorization': 'Bearer wrong-owner'}, source=Source(401))
    assert response.status == 401
    assert source.requests[0].headers['authorization'] == 'Bearer wrong-owner'
    response, source = fetch(headers={'Authorization': 'Bearer owner'}, method='HEAD')
    assert source.requests[0].method == 'HEAD'
    assert response.body is None


def test_unavailable_binding_or_source_fails_closed_without_credentials_in_error():
    request = Request('https://dcf.invalid/api/data/catalog', headers={'Authorization': 'Bearer owner'})
    response = asyncio.run(proxy.handle(request, SimpleNamespace()))
    assert response.status == 503
    assert 'owner' not in response.body

    class Broken:
        async def fetch(self, request):
            raise RuntimeError('secret incoming-owner server-owner')

    response, _ = fetch(headers={'Authorization': 'Bearer incoming-owner'}, source=Broken())
    assert response.status == 503
    assert 'secret' not in response.body and 'incoming-owner' not in response.body


def test_source_redirect_refused_without_forwarding_token_to_another_origin():
    response, source = fetch(headers={'Authorization': 'Bearer owner'}, source=Source(302))
    assert response.status == 502
    assert len(source.requests) == 1
    assert 'location' not in response.headers


def test_production_entrypoint_keeps_normal_wsgi_routes(monkeypatch):
    calls = []
    async def wsgi_fetch(app, request, env):
        calls.append((app, request, env))
        return 'normal-wsgi'
    async def handle(request, env):
        return 'owner-proxy'
    app = SimpleNamespace(config={}, jinja_loader=None)
    monkeypatch.setitem(sys.modules, 'workers', SimpleNamespace(
        WorkerEntrypoint=object, wsgi=SimpleNamespace(fetch=wsgi_fetch)))
    monkeypatch.setitem(sys.modules, 'app', SimpleNamespace(app=app))
    monkeypatch.setitem(sys.modules, 'embedded_assets', SimpleNamespace(ASSETS={}))
    monkeypatch.setattr(proxy, 'handle', handle)
    spec = importlib.util.spec_from_file_location('production_worker_under_test',
             Path(__file__).resolve().parents[1] / 'production_worker.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    worker = module.Default()
    worker.env = object()
    normal = Request('https://dcf.invalid/api/company/AAPL')
    assert asyncio.run(worker.fetch(normal)) == 'normal-wsgi'
    assert calls == [(app, normal, worker.env)]
    assert asyncio.run(worker.fetch(Request('https://dcf.invalid/api/data/catalog'))) == 'owner-proxy'
    assert asyncio.run(worker.fetch(Request('https://dcf.invalid/private/v1/stock-history'))) == 'owner-proxy'


def test_raw_control_characters_cannot_be_normalized_into_an_allowed_route():
    response, source = fetch('/api/data/ca\ntalog', {'Authorization': 'Bearer owner'})
    assert response.status == 400
    assert not source.requests


@pytest.mark.parametrize('prefix', ['/api/data', '/private/v1'])
@pytest.mark.parametrize('route', ['equity-claims', 'capabilities', 'financial-history/batch',
                                    'stock-history', 'historical-series'])
def test_cli_alias_preserves_the_exact_owner_authenticated_source_request(prefix, route):
    response, source = fetch(prefix + '/' + route + '?limit=1',
                             {'Authorization': 'Bearer owner', 'Cookie': 'session=admin',
                              'X-Zion-Service-Token': 'not-owner'})
    assert response.status == 206
    assert source.requests[0].url == 'https://zion.internal/private/v1/' + route + '?limit=1'
    assert source.requests[0].headers == {'authorization': 'Bearer owner'}
    assert response.headers['cache-control'] == 'private, no-store'
    assert response.headers['vary'] == 'Authorization'


@pytest.mark.parametrize('path', ['/private/v1/query', '/private/v1/financial-jobs',
    '/private/v1/%2e%2e/query', '/private/v1/datasets//research/object',
    '/private/v1/equity-claims/extra', '/private/v10/capabilities'])
def test_private_alias_still_refuses_non_allowlisted_or_escaped_routes(path):
    response, source = fetch(path, {'Authorization': 'Bearer owner'})
    assert response.status == 404
    assert not source.requests


@pytest.mark.parametrize('method', ['POST', 'DELETE', 'PUT', 'PATCH', 'OPTIONS'])
def test_cli_alias_is_read_only_even_with_an_owner_bearer(method):
    response, source = fetch('/private/v1/financial-history/batch',
                             {'Authorization': 'Bearer owner'}, method=method)
    assert response.status == 405
    assert not source.requests


@pytest.mark.parametrize('prefix', ['/api/data', '/private/v1'])
@pytest.mark.parametrize('length', [5000, 16384])
def test_native_row_cursor_uses_source_budget_without_truncation(prefix, length):
    # Parser boundaries only: Cloudflare's public URL limit remains16KB.
    cursor = 'x' * length
    query = '?path=data.parquet&cursor=' + cursor + '&columns=amount&limit=5'
    response, source = fetch(prefix + '/datasets/research/rows' + query,
                             {'Authorization': 'Bearer owner'})
    assert response.status == 206
    assert source.requests[0].url.endswith(query)


def test_native_row_wide_projection_survives_continuation_query():
    columns = ','.join('native_field_' + str(i).zfill(4) for i in range(256))
    assert len(columns) > 4096
    query = '?path=data.parquet&cursor=' + 'x' * 5000 + '&columns=' + columns
    response, source = fetch('/api/data/datasets/research/rows' + query,
                             {'Authorization': 'Bearer owner'})
    assert response.status == 206
    assert source.requests[0].url.endswith(query)


def test_object_listing_cursor_uses_existing_8192_source_budget():
    query = '?prefix=raw/wrds/&cursor=' + 'x' * 8192
    response, source = fetch('/api/data/datasets/research/objects' + query,
                             {'Authorization': 'Bearer owner'})
    assert response.status == 206
    assert source.requests[0].url.endswith(query)


@pytest.mark.parametrize('route,query', [
    ('datasets/research/rows', '?cursor=' + 'x' * 16385),
    ('datasets/research/rows', '?cursor=' + 'x' * 16384 + '&columns=' + 'x' * 16384),
    ('datasets/research/objects', '?cursor=' + 'x' * 8193),
    ('research-prices', '?cursor=' + 'x' * 4097),
    ('historical-series', '?search=' + 'x' * 4097),
])
def test_route_specific_cursor_and_query_budgets_still_fail_closed(route, query):
    response, source = fetch('/api/data/' + route + query, {'Authorization': 'Bearer owner'})
    assert response.status == 400
    assert not source.requests
