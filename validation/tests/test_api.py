from io import BytesIO
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app

def image_bytes():
    buf = BytesIO()
    Image.new("RGB", (32, 32)).save(buf, format="PNG")
    return buf.getvalue()

def test_openapi():
    with TestClient(app) as client:
        assert client.get("/openapi.json").status_code == 200
        assert client.get("/docs").status_code == 200

def test_missing_model_returns_503():
    with TestClient(app) as client:
        response = client.post("/api/v1/validation/photo",
                               files={"photo": ("garden.png", image_bytes(), "image/png")})
        assert response.status_code == 503

def test_bad_mime_returns_415():
    with TestClient(app) as client:
        response = client.post("/api/v1/validation/photo",
                               files={"photo": ("x.txt", b"hello", "text/plain")})
        assert response.status_code == 415

def test_invalid_image_returns_422():
    with TestClient(app) as client:
        response = client.post("/api/v1/validation/photo",
                               files={"photo": ("x.png", b"not an image", "image/png")})
        assert response.status_code == 422
