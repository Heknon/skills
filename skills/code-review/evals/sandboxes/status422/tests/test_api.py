from fastapi.testclient import TestClient

from shop.api import app

client = TestClient(app)


def test_reserve_takes_units() -> None:
    response = client.post("/stock/SKU-1/reserve", json={"qty": 2})
    assert response.status_code == 200
    assert response.json()["sku"] == "SKU-1"


def test_reserve_more_than_left_is_409() -> None:
    assert client.post("/stock/SKU-2/reserve", json={"qty": 1}).status_code == 409
