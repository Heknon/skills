import os


def currency() -> str:
    return os.environ.get("ACME_CURRENCY", "EUR")
