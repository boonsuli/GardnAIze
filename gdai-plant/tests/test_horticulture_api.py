"""Unit tests do not require PostgreSQL or alter existing data."""
from fastapi.testclient import TestClient
from api import horticulture_api as module


def test_attributes_contract(monkeypatch):
    monkeypatch.setattr(module, 'fetch_all', lambda sql, params=(): [
        {'attribute_name': 'sun_exposure', 'plants_covered': 12, 'evidence_count': 12}
    ])
    response = TestClient(module.app).get('/v1/attributes')
    assert response.status_code == 200
    attributes = response.json()['attributes']
    assert len(attributes) == 7
    assert attributes[0]['name'] == 'sun_exposure'
    assert attributes[0]['plants_covered'] == 12
    assert attributes[1]['plants_covered'] == 0


def test_recommendations_are_gated(monkeypatch):
    monkeypatch.setattr(module, 'fetch_all', lambda sql, params=(): [{'n': 0}])
    response = TestClient(module.app).post('/v1/recommendations', json={'preferences': {}})
    assert response.status_code == 409


def test_no_dsn_returns_503(monkeypatch):
    monkeypatch.delenv('GARDNAIZE_ML_DATABASE_URL', raising=False)
    response = TestClient(module.app).get('/v1/health')
    assert response.status_code == 503


def test_evidence_404(monkeypatch):
    monkeypatch.setattr(module, 'fetch_all', lambda sql, params=(): [])
    response = TestClient(module.app).get('/v1/plants/999/evidence')
    assert response.status_code == 404
