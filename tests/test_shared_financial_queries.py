from types import SimpleNamespace
from unittest.mock import patch
from app import app


def test_private_prices_are_not_available_to_anonymous_or_other_accounts():
    client = app.test_client()
    env = SimpleNamespace(FINANCIAL_DATA_TOKEN='private-test', FINANCIAL_OWNER_USER_ID='owner-id')
    with patch('accounts.current_user', return_value={'email': 'scswitzer@chapman.edu', 'id': 'other-id'}):
        response = client.get('/api/data/query?query=AAPL+price+on+2020-01-02', environ_overrides={'workers.env': env})
    assert response.status_code == 403
    assert 'price' not in response.get_json()


def test_data_page_uses_existing_site_and_no_embedded_private_credentials():
    response = app.test_client().get('/data')
    assert response.status_code == 200
    assert b'financial-query' in response.data
    assert b'FINANCIAL_DATA_TOKEN' not in response.data


def test_structured_queries_preserve_private_price_and_catalog_access():
    import json
    client = app.test_client()
    env = SimpleNamespace(FINANCIAL_DATA_TOKEN='private-test')
    for action in ['price', 'dataset_catalog']:
        response = client.get('/api/data/query', query_string={'request': json.dumps({'action': action, 'symbol': 'AAPL'})},
                              environ_overrides={'workers.env': env})
        assert response.status_code == 403
    response = client.get('/api/data/query', query_string={'request': json.dumps({'action': 'dataset_detail', 'dataset_id': '1' * 32})},
                          environ_overrides={'workers.env': env})
    assert response.status_code == 403
    # Public SEC requests get past access checks, but this fixture has no service.
    response = client.get('/api/data/query', query_string={'request': '{"action":"financials","symbol":"AAPL"}'},
                          environ_overrides={'workers.env': env})
    assert response.status_code == 503


def test_ambiguous_and_malformed_inputs_are_rejected_before_dispatch():
    client = app.test_client()
    for query in ['query=AAPL&request={}', 'request=null', 'request={', 'query=x&query=y', 'query=']:
        assert client.get('/api/data/query?' + query).status_code == 400


def test_website_forwards_bundle_pin_and_source_mismatch(monkeypatch):
    import json
    import sys
    import ppe_provider
    calls = []
    bundle = 'a' * 64
    response = SimpleNamespace(status=409, text=lambda: json.dumps({'error': 'RELEASE_MISMATCH'}))
    source = SimpleNamespace(fetch=lambda value: (calls.append(value), response)[1])
    monkeypatch.setitem(sys.modules, 'js', SimpleNamespace(
        Request=SimpleNamespace(new=lambda url, options: SimpleNamespace(url=url, options=options)),
        Object=SimpleNamespace(fromEntries=lambda x: x)))
    monkeypatch.setitem(sys.modules, 'pyodide.ffi', SimpleNamespace(to_js=lambda value, **kwargs: value))
    monkeypatch.setattr(ppe_provider, '_wait', lambda value, deadline: value)
    env = SimpleNamespace(FINANCIAL_DATA_TOKEN='private-test', FINANCIAL_DATA=source)
    result = app.test_client().get('/api/data/query',
        query_string={'request': '{"action":"dataset_catalog","offset":50}'},
        headers={'Authorization': 'Bearer private-test', 'x-zion-bundle-id': bundle},
        environ_overrides={'workers.env': env})
    assert result.status_code == 409
    assert result.get_json()['error'] == 'RELEASE_MISMATCH'
    assert len(calls) == 1
    assert calls[0].options['headers']['x-zion-bundle-id'] == bundle
    assert 'request=' in calls[0].url
