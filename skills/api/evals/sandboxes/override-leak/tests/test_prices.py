from fastapi.testclient import TestClient

from catalogue.main import app


def test_real_prices():
    with TestClient(app) as client:
        r = client.get("/prices/pear")
    assert r.json() == {"item": "pear", "price": 0.75}
