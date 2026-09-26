"""Handlers register themselves by event kind with @handler("kind")."""

from collections.abc import Callable
from typing import Any

Handler = Callable[[dict[str, Any]], str]
HANDLERS: dict[str, Handler] = {}


def handler(kind: str) -> Callable[[Handler], Handler]:
    def register(fn: Handler) -> Handler:
        HANDLERS[kind] = fn
        return fn

    return register
