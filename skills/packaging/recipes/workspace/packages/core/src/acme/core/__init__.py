"""Shared money helpers."""

from decimal import Decimal


def total(amounts: list[str]) -> Decimal:
    """Sum amounts given as strings, such as ["1.10", "2.20"]."""
    return sum((Decimal(a) for a in amounts), Decimal("0"))
