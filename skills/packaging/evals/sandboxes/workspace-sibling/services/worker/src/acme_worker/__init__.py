"""Background jobs."""

from acme_core import total


def run(batch: list[str]) -> str:
    return f"batch total {total(batch)}"
