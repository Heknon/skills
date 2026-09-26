"""Shared money and order helpers."""

from decimal import Decimal


def total(amounts: list[str]) -> Decimal:
    """Sum amounts given as strings, such as ["1.10", "2.20"]."""
    return sum((Decimal(a) for a in amounts), Decimal("0"))


def legacy_total(amounts: list[float]) -> float:
    """Old float version, kept for the reports service."""
    return round(sum(amounts), 2)
