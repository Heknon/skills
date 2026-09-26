from fastapi.testclient import TestClient

from shop.api import app

client = TestClient(app)


def test_read_order() -> None:
    response = client.get("/orders/o-1")
    assert response.status_code == 200
    assert [line["sku"] for line in response.json()["lines"]] == ["SKU-1", "SKU-2"]


def test_read_unknown_order_is_404() -> None:
    assert client.get("/orders/nope").status_code == 404
