"""Entry point: the worker calls on_message for every message on the events queue."""
import json

from events.dispatch import dispatch


def on_message(body):
    return dispatch(json.loads(body))
