from collections.abc import Iterator

import pytest

from app.dependencies import get_repo
from app.main import app
from app.repository import Customer


class FakeRepository:
    def __init__(self) -> None:
        self.customers: dict[str, Customer] = {
            "c1": {"id": "c1", "tier": "gold", "credit_limit_cents": 50_000},
            "c2": {"id": "c2", "tier": "basic", "credit_limit_cents": 1_000},
        }
        self.saved: list[tuple[str, int]] = []

    def customer(self, customer_id: str) -> Customer | None:
        return self.customers.get(customer_id)

    def open_total(self, customer_id: str) -> int:
        return sum(total for owner, total in self.saved if owner == customer_id)

    def add(self, customer_id: str, total_cents: int) -> int:
        self.saved.append((customer_id, total_cents))
        return len(self.saved)


@pytest.fixture
def repo() -> Iterator[FakeRepository]:
    fake = FakeRepository()
    app.dependency_overrides[get_repo] = lambda: fake
    yield fake
    app.dependency_overrides.clear()
