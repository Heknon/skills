"""Orders and customers. In memory here; the real service keeps them in a database."""

from typing import TypedDict


class Customer(TypedDict):
    id: str
    tier: str
    credit_limit_cents: int


_CUSTOMERS: dict[str, Customer] = {
    "c1": {"id": "c1", "tier": "basic", "credit_limit_cents": 5_000},
}
_ORDERS: list[tuple[str, int]] = [("c1", 2_000)]


class OrderRepository:
    def customer(self, customer_id: str) -> Customer | None:
        return _CUSTOMERS.get(customer_id)

    def open_total(self, customer_id: str) -> int:
        return sum(total for owner, total in _ORDERS if owner == customer_id)

    def add(self, customer_id: str, total_cents: int) -> int:
        _ORDERS.append((customer_id, total_cents))
        return len(_ORDERS)
