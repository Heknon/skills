"""HTTP API."""

from acme_core import total


def order_total(lines: list[str]) -> str:
    return str(total(lines))
