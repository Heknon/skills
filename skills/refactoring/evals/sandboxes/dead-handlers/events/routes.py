"""Routes from config/routes.yaml: event kind -> dotted path of a handler."""

import importlib
from pathlib import Path
from typing import Any

import yaml

ROUTES = Path(__file__).resolve().parent.parent / "config" / "routes.yaml"


def routed_handler(kind: str) -> Any:
    routes = yaml.safe_load(ROUTES.read_text(encoding="utf-8"))
    module_name, _, name = routes[kind].rpartition(".")
    return getattr(importlib.import_module(module_name), name)
