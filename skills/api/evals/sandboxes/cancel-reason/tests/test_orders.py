from fastapi.testclient import TestClient

from orders.main import app


def test_get_order():
    with TestClient(app) as client:
        r = client.get("/orders/1")
    assert r.json()["status"] == "open"
