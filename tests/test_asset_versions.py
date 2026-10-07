import re
import sys
from types import SimpleNamespace
from unittest.mock import patch
from app import app, asset_version


def test_template_versions_static_assets():
    with app.test_client() as client:
        html=client.get('/').get_data(as_text=True)
    urls=re.findall(r'(/static/[^" ]+)',html)
    assert urls and all('?v=' in url for url in urls)
    assert asset_version('css/workspace.css') in html


def test_edge_asset_cache_only_matches_content():
    from app import edge_static
    previous=app.config.get('CLOUDFLARE')
    app.config['CLOUDFLARE']=True
    asset_version.cache_clear()
    try:
        mocked_assets=SimpleNamespace(ASSETS={'static/css/workspace.css':'body {color: black}'})
        with patch.dict(sys.modules, {'embedded_assets':mocked_assets}):
            _check_edge_cache(edge_static)
    finally:
        app.config['CLOUDFLARE']=previous
        asset_version.cache_clear()


def _check_edge_cache(edge_static):
    version=asset_version('css/workspace.css')
    for query, expected in [('', 'no-cache'), ('?v=old', 'no-cache'), ('?v='+version, 'public, max-age=31536000, immutable')]:
        with app.test_request_context('/static/css/workspace.css'+query):
            assert edge_static('css/workspace.css').headers['Cache-Control']==expected
