from decimal import ROUND_HALF_UP, Decimal


def line_total(quantity, unit_price):
    """Price of one invoice line, rounded half up to the cent."""
    amount = Decimal(quantity * unit_price)
    return float(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
