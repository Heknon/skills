import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'orders.db'}")
    with TestClient(app) as c:
        yield c


def test_create_order(client):
    r = client.post("/orders", json={"customer": "ada", "lines": [{"sku": "A1", "quantity": 2}]})
    assert r.status_code == 201
    assert r.json()["lines"] == [{"sku": "A1", "quantity": 2}]
