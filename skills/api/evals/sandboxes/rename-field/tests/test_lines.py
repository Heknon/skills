from fastapi.testclient import TestClient

from shop.main import app


def test_add_line():
    with TestClient(app) as client:
        r = client.post("/lines", json={"sku": "nut", "qty": 2})
    assert r.status_code == 201
    assert r.json()["qty"] == 2
