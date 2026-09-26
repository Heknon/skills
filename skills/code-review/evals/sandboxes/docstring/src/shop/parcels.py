"""Parcels and what goes in them."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    sku: str
    weight_g: int
    qty: int


def item_count(items: list[Item]) -> int:
    """How many units the parcel holds."""
    return sum(item.qty for item in items)
