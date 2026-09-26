from fastapi.testclient import TestClient

from billing.main import app


def test_get_customer():
    with TestClient(app) as client:
        assert client.get("/customers/1").json() == {"ok": True, "data": {"id": 1, "name": "Acme"}}


def test_missing_customer():
    with TestClient(app) as client:
        r = client.get("/customers/9")
    assert r.status_code == 200
    assert r.json()["ok"] is False
