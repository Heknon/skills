"""Entry point of the queue worker: every message from the queue comes through dispatch()."""

from typing import Any

import events.handlers  # noqa: F401  # registers the @handler functions
from events.registry import HANDLERS
from events.routes import routed_handler


def dispatch(event: dict[str, Any]) -> str:
    kind = event["kind"]
    if kind in HANDLERS:
        return HANDLERS[kind](event)
    return str(routed_handler(kind)(event))
