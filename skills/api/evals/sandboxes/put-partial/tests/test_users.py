from fastapi.testclient import TestClient

from accounts.main import app


def test_create_user():
    with TestClient(app) as client:
        r = client.post("/users", json={"name": "Bea", "email": "bea@example.com"})
    assert r.status_code == 201
    assert r.json()["locale"] == "en"
