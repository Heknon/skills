from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def order(customer_id: str, qty: int, unit_cents: int) -> dict[str, object]:
    return {"customer_id": customer_id, "lines": [{"sku": "A1", "qty": qty, "unit_cents": unit_cents}]}


def test_gold_discount_and_saved(repo):
    r = client.post("/orders", json=order("c1", 4, 2_500))
    assert (r.status_code, r.json()) == (201, {"id": 1, "customer_id": "c1", "total_cents": 9_000})
    assert repo.saved == [("c1", 9_000)]


def test_no_discount_under_threshold(repo):
    r = client.post("/orders", json=order("c1", 1, 9_999))
    assert r.json()["total_cents"] == 9_999


def test_credit_limit(repo):
    r = client.post("/orders", json=order("c2", 3, 500))
    assert (r.status_code, r.json()) == (409, {"detail": "credit limit exceeded: 1500 > 1000"})
    assert repo.saved == []


def test_unknown_customer(repo):
    r = client.post("/orders", json=order("c9", 1, 100))
    assert (r.status_code, r.json()) == (404, {"detail": "unknown customer"})
