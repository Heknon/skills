from fastapi.testclient import TestClient

from ledger.main import app


def test_first_page_is_newest():
    with TestClient(app) as client:
        r = client.get("/orders", params={"limit": 5})
    items = r.json()["items"]
    assert len(items) == 5
    assert items[0]["created_at"] >= items[-1]["created_at"]
