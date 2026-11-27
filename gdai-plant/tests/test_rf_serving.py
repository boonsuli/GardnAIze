from fastapi.testclient import TestClient
from api.main import app
from api.model_registry import Registry
from api.rf_features import features
import numpy as np

def test_scope_no_fallback():
    registry = Registry(None)
    registry.models = [({"scope":{"country":"FR","region":"FR-IDF"}}, {}, None, [])]
    assert registry.select({"country":"FR","region":"FR-IDF"}) is not None
    assert registry.select({"country":"SN","region":"FR-IDF"}) is None
    assert registry.select({"country":"FR"}) is None

def test_prediction_never_pads():
    class Model:
        classes_ = np.array([0,1,2,3])
        def predict(self, rows):
            return np.array([2,0])
        def predict_proba(self, rows):
            return np.array([[.1,.1,.7,.1],[.8,.1,.1,0]])
    catalogue = [{"plant_id":i,"scientific_name":str(i),"features":{}} for i in (1,2)]
    results = Registry(None).predict(({}, {}, Model(), catalogue), {}, 10)
    assert len(results) == 1
    assert results[0]["method"] == "RANDOM_FOREST"

def test_unconfigured_api(monkeypatch):
    monkeypatch.delenv("GDAI_PLANT_MODEL_REGISTRY", raising=False)
    with TestClient(app) as client:
        assert client.get("/health").json()["loaded_models"] == 0
        assert client.get("/docs").status_code == 200
        assert client.get("/redoc").status_code == 200
        assert client.get("/openapi.json").status_code == 200
        result = client.post("/v1/recommendations", json={"request_id":"test","garden":{},"limit":10})
        assert result.status_code == 200
        assert result.json()["status"] == "INSUFFICIENT_DATA"

def test_features_exclude_labels_and_ids():
    assert features({"garden_id":"A","relevance_grade":3}) == features({})
