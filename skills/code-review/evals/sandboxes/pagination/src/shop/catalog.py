"""The product catalogue."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    price_cents: int


PRODUCTS = [
    Product(sku=f"SKU-{n:03d}", name=f"Product {n}", price_cents=250 * n)
    for n in range(1, 26)
]


def all_products() -> list[Product]:
    """Every product, in catalogue order."""
    return list(PRODUCTS)
