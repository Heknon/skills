from decimal import Decimal


def total(amounts: list[str]) -> Decimal:
    return sum((Decimal(a) for a in amounts), Decimal("0"))
