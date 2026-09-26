from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from orders_api.deps import get_clock
from orders_api.main import app

FIXED = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)


@pytest.fixture
def client() -> Iterator[TestClient]:
    # `with` runs the lifespan: a fresh Store per test, closed afterwards
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clear_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()  # an override left behind breaks later tests


@pytest.fixture
def frozen_clock() -> datetime:
    """Every order created in the test gets the same created_at: ties."""
    app.dependency_overrides[get_clock] = lambda: FIXED
    return FIXED
