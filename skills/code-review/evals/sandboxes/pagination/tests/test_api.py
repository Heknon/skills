from fastapi.testclient import TestClient

from shop.api import app

client = TestClient(app)


def test_list_products_returns_every_product() -> None:
    response = client.get("/products")
    assert response.status_code == 200
    assert len(response.json()) == 25
