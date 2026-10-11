from types import SimpleNamespace
import pytest
import dataset_catalog
from app import app


def document():
    return {"schema_version": "zion-dataset-catalog-v1", "checked_at": "2026-10-10T12:00:00Z",
            "sources": [{"id": key, "connectivity": "READABLE", "secret": "NEVER_RETURN"} for key in dataset_catalog.SOURCES], "path": "private/key"}


def test_catalog_sanitization_drops_all_unapproved_fields():
    result = dataset_catalog.sanitize_catalog(document())
    assert "NEVER_RETURN" not in str(result)
    assert "private/key" not in str(result)
    assert len(result["sources"]) == 4


@pytest.mark.parametrize("problem", ["missing", "duplicate", "unknown", "status", "date"])
def test_invalid_catalog_rejected(problem):
    doc = document()
    if problem == "missing": doc["sources"].pop()
    elif problem == "duplicate": doc["sources"][1] = doc["sources"][0]
    elif problem == "unknown": doc["sources"][0]["id"] = "untrusted"
    elif problem == "status": doc["sources"][0]["connectivity"] = "ALL_DATA_ACCURATE"
    else: doc["checked_at"] = "not a date"
    with pytest.raises(ValueError): dataset_catalog.sanitize_catalog(doc)


def test_routes_report_not_configured_without_cloud_binding():
    with app.test_client() as client:
        r = client.get('/api/providers/datasets')
        assert r.status_code == 200
        assert not r.json['configured']
        assert all(s['connectivity'] == 'NOT_CONFIGURED' for s in r.json['sources'])
        page = client.get('/providers').text
        assert '<title>Data providers · DCF Valuation Engine</title>' in page
        assert page.count('<h2>Zion dataset connections</h2>') == 1


def test_status_connection_and_failure_are_explicit(monkeypatch):
    env = SimpleNamespace(ZION_DATASET_CATALOG=object())
    monkeypatch.setattr(dataset_catalog, '_fetch', lambda service: dataset_catalog.sanitize_catalog(document()))
    with app.test_client() as client:
        r = client.get('/api/providers/datasets', environ_overrides={'workers.env': env})
        assert r.json['configured']
        assert all(s['connectivity'] == 'READABLE' for s in r.json['sources'])
        assert 'NEVER_RETURN' not in r.text
        assert client.get('/api/providers/datasets/research/object?path=private', environ_overrides={'workers.env': env}).status_code == 404
        def broken(service): raise RuntimeError('SECRET')
        monkeypatch.setattr(dataset_catalog, '_fetch', broken)
        r = client.get('/api/providers/datasets', environ_overrides={'workers.env': env})
        assert all(s['connectivity'] == 'UNAVAILABLE' for s in r.json['sources'])
        assert 'SECRET' not in r.text
