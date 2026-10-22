from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_demo_recommendations() -> None:
    response = client.post(
        "/recommendations",
        json={"location": "Paris", "exposure": "FULL_SUN", "soilType": "LOAMY"},
    )
    assert response.status_code == 200
    assert response.json()["mode"] == "demo-rules-not-ai"
    assert len(response.json()["plants"]) == 3


def test_invalid_recommendation_request() -> None:
    response = client.post("/recommendations", json={"location": ""})
    assert response.status_code == 422
