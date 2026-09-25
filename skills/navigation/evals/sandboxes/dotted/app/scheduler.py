import importlib

from app.settings import JOBS


def load(spec):
    module_name, _, attribute = spec.partition(":")
    return getattr(importlib.import_module(module_name), attribute)


def run_all():
    return [load(spec)() for spec in JOBS.values()]
