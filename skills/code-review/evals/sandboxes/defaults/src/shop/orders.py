"""Orders and what they are worth."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Order:
    id: str
    customer_id: str
    total_cents: int
    status: str  # "paid", "shipped" or "cancelled"


ORDERS = [
    Order("o-1", "c-1", 2_000, "paid"),
    Order("o-2", "c-1", 3_500, "shipped"),
    Order("o-3", "c-2", 1_200, "paid"),
    Order("o-4", "c-2", 9_900, "cancelled"),
]


def list_orders(customer_id: str, include_cancelled: bool = False) -> list[Order]:
    """The customer's orders; cancelled ones only when asked for."""
    return [
        order
        for order in ORDERS
        if order.customer_id == customer_id
        and (include_cancelled or order.status != "cancelled")
    ]


def revenue_cents(customer_id: str) -> int:
    """What the customer has spent: every order that was not cancelled."""
    return sum(order.total_cents for order in list_orders(customer_id))
