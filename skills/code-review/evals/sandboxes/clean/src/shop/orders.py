"""Orders, kept in memory for this service."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Line:
    sku: str
    qty: int
    unit_cents: int


@dataclass(frozen=True)
class Order:
    id: str
    lines: list[Line] = field(default_factory=list)


ORDERS = {
    "o-1": Order("o-1", [Line("SKU-1", 2, 1_250), Line("SKU-2", 1, 999)]),
    "o-2": Order("o-2", []),
}


def get_order(order_id: str) -> Order | None:
    """The order with this id, or None."""
    return ORDERS.get(order_id)
