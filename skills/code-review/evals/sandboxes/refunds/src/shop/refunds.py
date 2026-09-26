"""Refund rules."""

from dataclasses import dataclass
from datetime import date

REFUND_WINDOW_DAYS = 30


@dataclass(frozen=True)
class Order:
    id: str
    total_cents: int
    delivered_on: date | None


def refundable(order: Order, today: date) -> bool:
    """An order can be refunded until 30 days after delivery."""
    if order.delivered_on is None:
        return False
    return (today - order.delivered_on).days <= REFUND_WINDOW_DAYS
