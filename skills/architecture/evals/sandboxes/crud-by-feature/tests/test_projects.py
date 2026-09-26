import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def owner(client):
    return client.post("/users", json={"email": "ada@example.com", "name": "Ada"}).json()


def test_create_and_get(client, owner):
    created = client.post("/projects", json={"name": "Atlas", "owner_id": owner["id"]})
    assert created.status_code == 201
    got = client.get(f"/projects/{created.json()['id']}").json()
    assert (got["name"], got["owner_id"]) == ("Atlas", owner["id"])


def test_unknown_owner_is_422(client):
    assert client.post("/projects", json={"name": "Atlas", "owner_id": 99}).status_code == 422


def test_missing_project_is_404(client):
    assert client.get("/projects/99").status_code == 404


def test_list(client, owner):
    for name in ("A", "B"):
        client.post("/projects", json={"name": name, "owner_id": owner["id"]})
    assert [p["name"] for p in client.get("/projects").json()] == ["A", "B"]
