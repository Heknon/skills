"""Prices, discounts and stock checks for the shop."""
from decimal import ROUND_HALF_UP, Decimal

from shop import store

VAT_RATE = Decimal("0.17")


def add_vat(net: Decimal) -> Decimal:
    """Add VAT to a net price."""
    return (net * (1 + VAT_RATE)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def apply_discount(price: Decimal, percent: int) -> Decimal:
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return _round(price * (100 - percent) / 100)


def price_list(category: str) -> dict:
    items = store.load(category)
    return {item["sku"]: add_vat(Decimal(item["net"])) for item in items}


def reprice(items: list[dict], percent: int) -> None:
    for item in items:
        item["price"] = apply_discount(item["price"], percent)


def wait_for_stock(sku: str, timeout: float = 5) -> bool:
    return store.poll(sku, timeout)


def sku_label(sku: str) -> str:
    """Return the sku label."""
    return sku.upper()


def _round(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
