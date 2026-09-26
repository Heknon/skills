"""Run the jobs listed in config/jobs.yaml. Each job names a callable by dotted path."""

import importlib
from pathlib import Path
from typing import Any

import yaml

CONFIG = Path(__file__).resolve().parent.parent / "config" / "jobs.yaml"


def load_callable(dotted: str) -> Any:
    module_name, _, attr = dotted.rpartition(".")
    return getattr(importlib.import_module(module_name), attr)


def run(job: str, *args: Any) -> Any:
    jobs = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))["jobs"]
    return load_callable(jobs[job]["call"])(*args)
