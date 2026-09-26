"""Print the public names of modules, with signatures, to compare before and after a step.

Usage, from the project's root folder:

    uv run python <skill>/tools/public_names.py [--path DIR] MODULE [MODULE ...]

For each MODULE, one line per public name (no leading underscore) that
`from MODULE import name` can reach, sorted:

    app.reports.format_money  function  (amount: Decimal, currency: str = 'EUR') -> str
    app.reports.Order  class  (number: str, customer: str, ...) -> None
    app.reports.Order.total  method  (self) -> Decimal
    app.reports.CENT  value  Decimal('0.01')
    app.reports.Decimal  imported  from decimal
    app.reports.csv  module

Run it before the first step and after each one, into two files, and
compare them: a line that disappeared or changed is a name or signature
that callers can no longer use as before; an added line is harmless.
Names are listed wherever they are defined, so a move that keeps the old
import working shows no difference. Classes and functions from outside
the module's top-level package are one `imported` line each. The current folder is put first on sys.path; --path adds
more (such as src). Exit 1 when a module cannot be imported. Standard
library only. Lab: Python 3.12.14.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import os
import re
import sys
import types
from collections.abc import Callable

ADDRESS = re.compile(r" at 0x[0-9a-fA-F]+")
MODULE_PREFIX = re.compile(r"\b(?:[a-z_]\w*\.)+([A-Za-z_]\w*)")


def signature_text(value: Callable[..., object]) -> str:
    """The signature, with module prefixes dropped so a move does not show as a change."""
    try:
        text = str(inspect.signature(value))
    except (TypeError, ValueError):
        return "(signature not available)"
    return MODULE_PREFIX.sub(r"\1", ADDRESS.sub("", text))


def describe(value: object, root: str) -> tuple[str, str]:
    if isinstance(value, types.ModuleType):
        return "module", ""
    home = getattr(value, "__module__", None)
    callable_here = inspect.isclass(value) or inspect.isroutine(value)
    if (
        callable_here
        and isinstance(home, str)
        and home != root
        and not home.startswith(root + ".")
    ):
        return "imported", f"from {home}"
    if inspect.isclass(value):
        kind = "class"
    elif inspect.isroutine(value):
        kind = "function"
    else:
        text = ADDRESS.sub("", repr(value))
        return "value", text if len(text) <= 80 else text[:77] + "..."
    return kind, signature_text(value)


def public_lines(module_name: str) -> list[str]:
    module = importlib.import_module(module_name)
    root = module_name.split(".")[0]
    lines = []
    for name in sorted(vars(module)):
        if name.startswith("_"):
            continue
        value = vars(module)[name]
        kind, detail = describe(value, root)
        lines.append(f"{module_name}.{name}  {kind}  {detail}".rstrip())
        if kind == "class" and isinstance(value, type):
            for attr in sorted(vars(value)):
                if attr.startswith("_"):
                    continue
                member = inspect.getattr_static(value, attr)
                if isinstance(member, (staticmethod, classmethod)):
                    member = member.__func__
                if inspect.isfunction(member):
                    lines.append(
                        f"{module_name}.{name}.{attr}  method  {signature_text(member)}"
                    )
                elif isinstance(member, property):
                    lines.append(f"{module_name}.{name}.{attr}  property")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print public names and signatures of modules."
    )
    parser.add_argument(
        "modules",
        nargs="+",
        metavar="MODULE",
        help="dotted module names, such as app.reports",
    )
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="a folder to put on sys.path, such as src",
    )
    args = parser.parse_args(argv)
    for folder in reversed([os.getcwd(), *args.path]):
        sys.path.insert(0, os.path.abspath(folder))
    status = 0
    for module_name in args.modules:
        try:
            lines = public_lines(module_name)
        except Exception as exc:  # noqa: BLE001  # report and go on to the next module
            print(f"{module_name}  IMPORT FAILED  {type(exc).__name__}: {exc}")
            status = 1
            continue
        print("\n".join(lines))
    return status


if __name__ == "__main__":
    sys.exit(main())
