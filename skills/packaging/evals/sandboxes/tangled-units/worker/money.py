from decimal import ROUND_HALF_UP, Decimal


def to_cents(amount: str) -> int:
    return int((Decimal(amount) * 100).quantize(Decimal("1"), ROUND_HALF_UP))


def fmt(cents: int, currency: str) -> str:
    return f"{cents // 100}.{cents % 100:02d} {currency}"
