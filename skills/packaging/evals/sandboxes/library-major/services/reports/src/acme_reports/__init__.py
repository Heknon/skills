"""Monthly reports."""

from acme_core import legacy_total


def month_total(amounts: list[float]) -> float:
    return legacy_total(amounts)
