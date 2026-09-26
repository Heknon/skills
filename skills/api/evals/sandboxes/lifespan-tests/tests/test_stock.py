from fastapi.testclient import TestClient

from inventory.main import app

client = TestClient(app)


def test_bolts_in_stock():
    r = client.get("/stock/bolt")
    assert r.json() == {"sku": "bolt", "count": 120}


def test_nuts_out_of_stock():
    r = client.get("/stock/nut")
    assert r.json()["count"] == 0
