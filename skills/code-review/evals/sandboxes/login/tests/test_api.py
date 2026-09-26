from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from shop.api import app, get_clients


class FakeClients:
    """Enough of a pymongo Collection for find_one with equality filters."""

    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self.docs = docs

    def find_one(
        self, query: dict[str, Any], projection: dict[str, int]
    ) -> dict[str, Any] | None:
        for doc in self.docs:
            if all(doc.get(key) == value for key, value in query.items()):
                return {k: doc[k] for k, on in projection.items() if on and k in doc}
        return None


@pytest.fixture
def client() -> Iterator[TestClient]:
    fake = FakeClients(
        [{"client_id": "acme", "api_key": "s3cret", "scopes": ["orders:read"]}]
    )
    app.dependency_overrides[get_clients] = lambda: fake
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_known_client_gets_its_scopes(client: TestClient) -> None:
    body = {"client_id": "acme", "api_key": "s3cret"}
    response = client.post("/auth/scopes", json=body)
    assert response.status_code == 200
    assert response.json() == {"client_id": "acme", "scopes": ["orders:read"]}


def test_wrong_key_is_401(client: TestClient) -> None:
    body = {"client_id": "acme", "api_key": "nope"}
    response = client.post("/auth/scopes", json=body)
    assert response.status_code == 401
