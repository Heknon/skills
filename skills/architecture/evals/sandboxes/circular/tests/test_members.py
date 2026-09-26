from fastapi.testclient import TestClient

from app.main import app


def test_create_and_read():
    client = TestClient(app)
    created = client.post("/members", json={"email": "a@x", "name": "Ada", "password": "pw"})
    assert created.status_code == 201
    assert client.get(f"/members/{created.json()['id']}").json() == {"id": created.json()["id"], "name": "Ada"}
