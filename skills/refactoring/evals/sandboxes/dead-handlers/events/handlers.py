"""Event handlers. Each returns a one-line summary for the audit log."""

from typing import Any

from events.registry import handler


@handler("refund")
def on_refund(event: dict[str, Any]) -> str:
    return f"refund {event['id']}: {event['amount']}"


def on_invoice(event: dict[str, Any]) -> str:
    return f"invoice {event['id']} issued"


def on_ping(event: dict[str, Any]) -> str:
    # replaced by the health endpoint in 2024; nothing sends ping any more
    return "pong"


def _format_legacy(event: dict[str, Any]) -> str:
    return " ".join(f"{key}={value}" for key, value in sorted(event.items()))


def _on_shipment(event: dict[str, Any]) -> str:
    return f"shipment {event['id']} sent"
