"""Parsers registered by installed packages under the entry point group app.parsers."""

from collections.abc import Callable
from importlib.metadata import entry_points


def load_parsers() -> dict[str, Callable[[str], object]]:
    return {ep.name: ep.load() for ep in entry_points(group="app.parsers")}
