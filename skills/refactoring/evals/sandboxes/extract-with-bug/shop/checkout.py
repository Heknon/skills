"""Checkout: the price a customer pays for a basket."""

from decimal import ROUND_HALF_UP, Decimal

BULK_THRESHOLD = 10  # items; the price list says "10 items or more: 5% off"
BULK_RATE = Decimal("0.05")
LOYALTY_CREDIT = Decimal("2.00")


def order_total(lines: list[dict[str, object]], customer: dict[str, object]) -> Decimal:
    """Total to pay for the basket, in euros, rounded to cents."""
    subtotal = Decimal("0")
    items = 0
    for line in lines:
        price = Decimal(str(line["price"]))
        quantity = int(str(line["qty"]))
        subtotal += price * quantity
        items += quantity

    # discounts: bulk first, then the loyalty credit, never below zero
    if items > BULK_THRESHOLD:
        subtotal -= subtotal * BULK_RATE
    if customer.get("loyal"):
        subtotal -= LOYALTY_CREDIT
    if subtotal < 0:
        subtotal = Decimal("0")

    shipping = Decimal("0") if subtotal >= 50 else Decimal("4.90")
    return (subtotal + shipping).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
