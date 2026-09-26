from fastapi.testclient import TestClient

from app.main import app


def test_first_page():
    body = TestClient(app).get("/products").json()
    assert body[0] == "product-001"
    assert len(body) == 20
