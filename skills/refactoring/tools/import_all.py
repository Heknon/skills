"""Import every module of a package, and resolve every dotted path to it.

Usage, from the project's root folder:

    uv run python <skill>/tools/import_all.py [--path DIR] [--config FILE]
        [--scripts DIR] PACKAGE [PACKAGE ...]

1. Imports each module of each PACKAGE (pkgutil.walk_packages), except
   __main__ modules, which run a program when imported.
2. For each --config file (pyproject.toml, YAML, INI, JSON, read as text),
   finds every dotted path that starts with one of the PACKAGE names, in
   the forms "pkg.mod:attr" and "pkg.mod.attr", and resolves it: the
   module imports and the attribute exists.
3. For each .py file in each --scripts folder, imports it under a private
   name when it has an `if __name__ == "__main__":` guard, so its imports
   run and its program does not. A script without the guard is SKIP.

The current folder is put first on sys.path; --path adds more (such as
src for a src layout that is not installed). One line per item: OK, FAIL
with the error, or SKIP with the reason. Exit 0 when nothing failed, 1
when something did, 2 on a usage error. Standard library only, Python
3.9 or later. Lab: Python 3.12.14, flat and src layouts.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import os
import pkgutil
import re
import sys
import traceback

GUARD = re.compile(r"""^if\s+__name__\s*==\s*["']__main__["']\s*:""", re.MULTILINE)


def error_text(exc: BaseException, where: bool = True) -> str:
    last = (
        traceback.extract_tb(exc.__traceback__)[-1:]
        if exc.__traceback__ and where
        else []
    )
    place = f" ({last[0].filename}:{last[0].lineno})" if last else ""
    return f"{type(exc).__name__}: {exc}{place}"


def import_package(name: str) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    try:
        package = importlib.import_module(name)
    except BaseException as exc:  # noqa: BLE001  # a script that exits on import is a finding too
        return [("FAIL", name, error_text(exc))]
    rows.append(("OK", name, ""))
    paths = getattr(package, "__path__", None)
    if paths is None:
        return rows
    for info in pkgutil.walk_packages(
        paths, prefix=name + ".", onerror=lambda _name: None
    ):
        if info.name.rsplit(".", 1)[-1] == "__main__":
            rows.append(("SKIP", info.name, "__main__ runs the program when imported"))
            continue
        try:
            importlib.import_module(info.name)
        except BaseException as exc:  # noqa: BLE001
            rows.append(("FAIL", info.name, error_text(exc)))
        else:
            rows.append(("OK", info.name, ""))
    return rows


def resolve(dotted: str) -> None:
    """Import the module part of a dotted path and read the attribute part."""
    if ":" in dotted:
        module_name, _, attrs = dotted.partition(":")
        target: object = importlib.import_module(module_name)
        for attr in attrs.split(".") if attrs else []:
            target = getattr(target, attr)
        return
    parts = dotted.split(".")
    for cut in range(len(parts), 0, -1):
        module_name = ".".join(parts[:cut])
        try:
            target = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name is not None and module_name.startswith(exc.name) and cut > 1:
                continue  # this prefix is not a module; try a shorter one
            raise
        for attr in parts[cut:]:
            target = getattr(target, attr)
        return


def dotted_paths(text: str, packages: list[str]) -> list[str]:
    heads = "|".join(re.escape(p) for p in packages)
    pattern = re.compile(rf"(?<![\w.])((?:{heads})(?:\.\w+)+(?::\w+(?:\.\w+)*)?)")
    seen: list[str] = []
    for match in pattern.finditer(text):
        if text[: match.start()].endswith(('entry-points."', "entry-points.'")):
            continue  # an entry point group's name, not a path to code
        if match.group(1) not in seen:
            seen.append(match.group(1))
    return seen


def check_config(path: str, packages: list[str]) -> list[tuple[str, str, str]]:
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        return [("FAIL", path, error_text(exc))]
    rows: list[tuple[str, str, str]] = []
    for dotted in dotted_paths(text, packages):
        label = f"{path}: {dotted}"
        try:
            resolve(dotted)
        except BaseException as exc:  # noqa: BLE001
            rows.append(("FAIL", label, error_text(exc, where=False)))
        else:
            rows.append(("OK", label, ""))
    if not rows:
        rows.append(("SKIP", path, "no dotted path to these packages"))
    return rows


def check_scripts(folder: str) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d not in ("__pycache__", ".venv", "venv"))
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as handle:
                if not GUARD.search(handle.read()):
                    rows.append(
                        (
                            "SKIP",
                            path,
                            "no __main__ guard: importing it would run it; run it with --help instead",
                        )
                    )
                    continue
            spec = importlib.util.spec_from_file_location(
                f"_import_all_{len(rows)}", path
            )
            if spec is None or spec.loader is None:
                rows.append(("FAIL", path, "cannot load"))
                continue
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
            except BaseException as exc:  # noqa: BLE001
                rows.append(("FAIL", path, error_text(exc)))
            else:
                rows.append(("OK", path, ""))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Import every module of a package and resolve dotted paths to it."
    )
    parser.add_argument(
        "packages",
        nargs="+",
        metavar="PACKAGE",
        help="top-level import names, such as app",
    )
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="a folder to put on sys.path, such as src",
    )
    parser.add_argument(
        "--config",
        action="append",
        default=[],
        help="a file that names code by dotted path",
    )
    parser.add_argument(
        "--scripts", action="append", default=[], help="a folder of scripts"
    )
    args = parser.parse_args(argv)
    for folder in reversed([os.getcwd(), *args.path]):
        sys.path.insert(0, os.path.abspath(folder))
    rows: list[tuple[str, str, str]] = []
    for package in args.packages:
        rows.extend(import_package(package))
    for path in args.config:
        rows.extend(check_config(path, args.packages))
    for folder in args.scripts:
        rows.extend(check_scripts(folder))
    for status, item, detail in rows:
        print(f"{status:<4} {item}" + (f"  {detail}" if detail else ""))
    failed = sum(1 for row in rows if row[0] == "FAIL")
    print(
        f"import_all: {sum(1 for r in rows if r[0] == 'OK')} ok, {failed} failed, {sum(1 for r in rows if r[0] == 'SKIP')} skipped"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
