from pathlib import Path

from flask import Flask

from data_workspace import register_data_workspace


def test_data_page_is_same_app_template_and_never_embeds_server_credentials(monkeypatch):
    monkeypatch.setenv('ZION_PRIVATE_API_TOKEN', 'PRIVATE_SECRET_SENTINEL')
    root = Path(__file__).resolve().parents[1]
    app = Flask('workspace-test', template_folder=str(root / 'templates'),
                static_folder=str(root / 'static'))
    app.config['ZION_PRIVATE_API_TOKEN'] = 'CONFIG_SECRET_SENTINEL'
    register_data_workspace(app)
    client = app.test_client()
    response = client.get('/data')
    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'private, no-store'
    assert 'PRIVATE_SECRET_SENTINEL' not in response.text
    assert 'CONFIG_SECRET_SENTINEL' not in response.text
    assert 'Valuation Engine' in response.text
    assert 'id="data-owner-key"' in response.text
    assert 'type="password"' in response.text
    assert 'js/data-workspace.js' in response.text
    assert client.post('/data').status_code == 405
    assert 'Set-Cookie' not in response.headers
