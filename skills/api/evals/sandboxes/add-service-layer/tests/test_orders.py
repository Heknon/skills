from fastapi.testclient import TestClient

from warehouse.main import app


def test_place_order():
    with TestClient(app) as client:
        r = client.post("/orders", json={"sku": "bolt", "quantity": 2})
    assert r.status_code == 201


def test_out_of_stock():
    with TestClient(app) as client:
        r = client.post("/orders", json={"sku": "nut", "quantity": 1})
    assert r.status_code == 409
