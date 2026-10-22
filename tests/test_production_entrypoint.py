"""The production build must ship an entrypoint that awaits the edge limiter.

The limiter was inert in production because the WSGI hook cannot await the binding
*and* because ``wrangler.production.jsonc`` copied a second entrypoint that never
called the awaited check. These tests pin the build identity, the module bundle and
the dispatch order so neither can regress silently.
"""
import ast
import asyncio
import importlib.util
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


class _HTTPMethod:
    """Mirrors workers' HTTPMethod enum: str() is not the method name."""

    def __init__(self, name):
        self.value = name

    def __str__(self):
        return '<HTTPMethod.' + str(self.value) + '>'


class _Response:
    def __init__(self, body=None, status=200, headers=None):
        self.body, self.status, self.headers = body, status, headers or {}


class _Entrypoint:
    env = None


def production_config():
    text = (ROOT / 'wrangler.production.jsonc').read_text()
    body = '\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('//'))
    return json.loads(body)


def module_names():
    tree = ast.parse((ROOT / 'scripts/embed_assets.py').read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                getattr(target, 'id', None) == 'module_names' for target in node.targets):
            return [item.value for item in node.value.elts]
    raise AssertionError('scripts/embed_assets.py no longer declares module_names')


def entrypoint_awaits_limiter_before_dispatch(path):
    """Return the line of the awaited limiter call, proving it precedes dispatch."""
    tree = ast.parse(Path(path).read_text())
    fetch = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == 'Default'
        for node in node.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == 'fetch'
    )
    limiter = [
        node.lineno
        for node in ast.walk(fetch)
        if isinstance(node, ast.Await)
        and isinstance(node.value, ast.Call)
        and getattr(node.value.func, 'id', None) == 'enforce'
    ]
    assert limiter, f'{path} does not await enforce() in Default.fetch'
    dispatch = [
        node.lineno
        for node in ast.walk(fetch)
        if isinstance(node, ast.Call)
        and getattr(node.func, 'attr', None) in {'fetch', 'handle'}
    ]
    assert dispatch, f'{path} never dispatches a request'
    assert min(limiter) < min(dispatch), 'the limiter must run before any dispatch'
    return True


def test_production_build_compiles_the_limited_entrypoint():
    config = production_config()
    assert config['main'] == 'worker_runtime/worker.py'
    command = config['build']['command']
    assert 'scripts/embed_assets.py' in command
    assert 'production_worker.py' not in command
    assert not (ROOT / 'production_worker.py').exists(), (
        'a second entrypoint can omit the awaited limiter; keep one build path'
    )
    assert entrypoint_awaits_limiter_before_dispatch(ROOT / 'worker.py')


def test_embed_assets_bundles_the_entrypoint_and_the_limiter():
    names = module_names()
    assert 'worker.py' in names
    assert 'edge_limits.py' in names
    assert 'owner_data_proxy.py' in names


def test_production_wrangler_ships_the_limiter_bindings():
    names = {limit['name'] for limit in production_config()['ratelimits']}
    assert {'PREVIEW_LIMIT', 'REFERENCE_LIMIT', 'WRITE_LIMIT', 'MCP_LIMIT'} <= names


def test_production_build_emits_a_bundled_limited_entrypoint(tmp_path):
    """Run the real build command in a scratch tree and inspect its output."""
    command = production_config()['build']['command'].replace(
        'python3', shlex.quote(sys.executable), 1)
    for source in ROOT.glob('*.py'):
        shutil.copy2(source, tmp_path / source.name)
    for directory in ('scripts', 'templates', 'static', 'data'):
        shutil.copytree(ROOT / directory, tmp_path / directory)
    subprocess.run(command, shell=True, cwd=tmp_path, check=True, capture_output=True)
    built = tmp_path / 'worker_runtime/worker.py'
    assert built.is_file()
    assert 'await enforce' in built.read_text()
    assert (tmp_path / 'worker_runtime/edge_limits.py').is_file()
    assert (tmp_path / 'worker_runtime/owner_data_proxy.py').is_file()
    entrypoint_awaits_limiter_before_dispatch(built)


def load_entrypoint(monkeypatch, calls):
    async def wsgi_fetch(app, request, env):
        calls.append('wsgi')
        return 'normal-wsgi'

    async def handle(request, env):
        calls.append('owner-proxy')
        return 'owner-proxy'

    monkeypatch.setitem(sys.modules, 'workers', SimpleNamespace(
        WorkerEntrypoint=_Entrypoint, wsgi=SimpleNamespace(fetch=wsgi_fetch),
        Response=_Response))
    monkeypatch.setitem(sys.modules, 'jinja2', SimpleNamespace(DictLoader=dict))
    monkeypatch.setitem(sys.modules, 'embedded_assets', SimpleNamespace(ASSETS={}))
    monkeypatch.setitem(sys.modules, 'app', SimpleNamespace(
        app=SimpleNamespace(config={}, jinja_loader=None)))
    monkeypatch.setitem(sys.modules, 'owner_data_proxy', SimpleNamespace(handle=handle))
    sys.modules.pop('edge_limits', None)
    spec = importlib.util.spec_from_file_location('worker_under_test', ROOT / 'worker.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Default


def limited_request(path, method):
    return SimpleNamespace(
        url='https://dcf.example' + path,
        method=method,
        headers=SimpleNamespace(get=lambda key: '203.0.113.7' if key == 'CF-Connecting-IP' else None),
    )


def test_enum_valued_method_is_metered_before_wsgi_or_proxy_dispatch(monkeypatch):
    calls, counted = [], []

    async def limit(payload):
        counted.append(payload['key'])
        return SimpleNamespace(success=False)

    entrypoint = load_entrypoint(monkeypatch, calls)
    worker = entrypoint()
    worker.env = SimpleNamespace(
        RECORD_SALT='test-only-salt', DEPLOY_ENVIRONMENT='production',
        REFERENCE_LIMIT=SimpleNamespace(limit=limit))
    response = asyncio.run(worker.fetch(limited_request('/api/data/query?q=AAPL', _HTTPMethod('GET'))))
    assert response.status == 429
    assert calls == [], 'a limited request must not reach WSGI or the owner proxy'
    assert len(counted) == 1 and counted[0].startswith('dcf:edge:')


def test_allowed_request_still_reaches_the_route_it_asks_for(monkeypatch):
    calls, counted = [], []

    async def limit(payload):
        counted.append(payload['key'])
        return SimpleNamespace(success=True)

    entrypoint = load_entrypoint(monkeypatch, calls)
    worker = entrypoint()
    worker.env = SimpleNamespace(
        RECORD_SALT='test-only-salt', DEPLOY_ENVIRONMENT='production',
        REFERENCE_LIMIT=SimpleNamespace(limit=limit))
    assert asyncio.run(worker.fetch(
        limited_request('/api/data/query?q=AAPL', _HTTPMethod('GET')))) == 'normal-wsgi'
    assert asyncio.run(worker.fetch(
        limited_request('/api/data/catalog', _HTTPMethod('GET')))) == 'owner-proxy'
    assert calls == ['wsgi', 'owner-proxy']
    assert len(counted) == 2
