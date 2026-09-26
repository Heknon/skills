from fastapi.testclient import TestClient

from quotes.main import app


def test_quote():
    with TestClient(app) as client:
        r = client.get("/quotes/USD", params={"amount": 10})
    assert r.json() == {"currency": "USD", "amount": 10.8}
