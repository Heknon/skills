import asyncio
import os

import pytest
from pymongo import monitoring

URI = os.environ.get("MONGODB_URI")
DB = "beanie_app_test"


class Commands(monitoring.CommandListener):
    """Records every command the driver sends (PyMongo command monitoring)."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, dict]] = []

    def started(self, event) -> None:
        if event.command_name not in ("hello", "isMaster", "endSessions"):
            self.sent.append((event.command_name, dict(event.command)))

    def succeeded(self, event) -> None:
        pass

    def failed(self, event) -> None:
        pass

    def names(self) -> list[str]:
        return [name for name, _ in self.sent]


LISTENER = Commands()
monitoring.register(LISTENER)  # applies to every client created afterwards


@pytest.fixture
def commands() -> Commands:
    LISTENER.sent.clear()
    return LISTENER


@pytest.fixture
def run():
    """Run a coroutine: the recipe needs no pytest plugin."""
    return asyncio.run


def pytest_collection_modifyitems(items):
    if not URI:
        skip = pytest.mark.skip(reason="needs MONGODB_URI (a development server)")
        for item in items:
            item.add_marker(skip)
