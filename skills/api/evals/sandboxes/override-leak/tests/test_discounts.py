from fastapi.testclient import TestClient

from catalogue.main import app, get_price_list


def test_price_with_fake_list():
    app.dependency_overrides[get_price_list] = lambda: {"apple": 9.99}
    with TestClient(app) as client:
        r = client.get("/prices/apple")
    assert r.json()["price"] == 9.99
