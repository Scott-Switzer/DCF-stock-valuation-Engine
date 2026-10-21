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
