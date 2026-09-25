import events.handlers  # noqa: F401  registers the handlers
from events.registry import HANDLERS


def dispatch(event):
    return HANDLERS[event["kind"]](event)
