import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_create_and_get(client):
    created = client.post("/notes", json={"title": "Plan", "body": "x"})
    assert created.status_code == 201
    assert client.get(f"/notes/{created.json()['id']}").json()["title"] == "Plan"


def test_missing_is_404(client):
    assert client.get("/notes/9").status_code == 404
