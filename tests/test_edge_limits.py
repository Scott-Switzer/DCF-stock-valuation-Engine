"""Native edge throttling must never serialize previews through D1."""
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch
import pytest
from app import app


@pytest.mark.parametrize('path,binding', [('/api/preview/dcf','PREVIEW_LIMIT'),('/api/calculate','WRITE_LIMIT'),('/api/references/AAPL','REFERENCE_LIMIT')])
@pytest.mark.parametrize('allowed', [True, False])
def test_native_limits_do_not_query_database(path, binding, allowed):
    limit = Mock(return_value=SimpleNamespace(success=allowed))
    env = SimpleNamespace(RECORD_SALT='test-only-salt', DB=Mock(), **{binding: SimpleNamespace(limit=limit)})
    modules = {'pyodide':SimpleNamespace(), 'pyodide.ffi':SimpleNamespace(run_sync=lambda result:result, to_js=lambda value, **kwargs:value), 'js':SimpleNamespace(Object=SimpleNamespace(fromEntries=None))}
    previous = app.config.get('CLOUDFLARE')
    app.config['CLOUDFLARE'] = True
    try:
        with patch.dict(sys.modules, modules), app.test_request_context(path, method='GET' if binding=='REFERENCE_LIMIT' else 'POST', environ_overrides={'workers.env':env}):
            from app import limit_expensive_work
            response=limit_expensive_work()
            assert response is None if allowed else response.status_code == 429
            env.DB.prepare.assert_not_called()
            assert limit.call_args.args[0]['key'].startswith('dcf:')
            assert 'test-only-salt' not in limit.call_args.args[0]['key']
    finally:
        app.config['CLOUDFLARE'] = previous
