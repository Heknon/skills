import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_place_order(client):
    r = client.post("/orders", json={"customer_id": 1, "amount_cents": 2_500})
    assert r.status_code == 201
    assert r.json()["amount_cents"] == 2_500


def test_unknown_customer_is_404(client):
    r = client.post("/orders", json={"customer_id": 9, "amount_cents": 100})
    assert r.status_code == 404
    assert r.json() == {"detail": "customer 9 not found"}
