from fastapi.testclient import TestClient

from payments.main import app


def test_create_payment():
    with TestClient(app) as client:
        r = client.post("/payments", json={"account": "acc-1", "amount_cents": 1250})
    assert r.status_code == 201
    assert r.json()["amount_cents"] == 1250
