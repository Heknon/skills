import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_get_invoice(client):
    assert client.get("/invoices/1").json()["amount_cents"] == 5_000


def test_pay_twice_is_409(client):
    assert client.post("/invoices/1/pay").status_code == 200
    r = client.post("/invoices/1/pay")
    assert r.status_code == 409
    assert r.json() == {"code": "invoice_already_paid", "detail": "invoice 1 is already paid"}
