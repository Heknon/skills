"""Route tests with a fake service: no database needed."""

from collections.abc import Iterator

import pytest
from beanie import PydanticObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient

from shop.api import get_user_service, router
from shop.schemas import UserOut

ANN_ID = PydanticObjectId("64b7f0c2a1b2c3d4e5f60718")


class FakeService:
    async def profile(self, user_id: PydanticObjectId) -> UserOut | None:
        if user_id == ANN_ID:
            return UserOut(id=str(ANN_ID), email="ann@example.com", name="Ann")
        return None


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_user_service] = FakeService
    yield TestClient(app)


def test_read_user(client: TestClient) -> None:
    response = client.get(f"/users/{ANN_ID}")
    assert response.json() == {
        "id": str(ANN_ID),
        "email": "ann@example.com",
        "name": "Ann",
    }


def test_unknown_user_is_404(client: TestClient) -> None:
    assert client.get("/users/64b7f0c2a1b2c3d4e5f60719").status_code == 404
