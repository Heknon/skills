#!/usr/bin/env python3
"""Judge a code change against the snapshot taken before it.

Usage: check_change.py --before DIR --after DIR [--json]

--before is the snapshot folder (.ledger/before), holding a copy of every
file as it was before its first edit, at the same relative path. --after
is the working directory. Only files present in the snapshot are compared.

Every rule prints PASS, FAIL, WARN, SKIP or INFO, a count, up to five
offenders and a note. Exit 0 when no rule is FAIL, 1 when any is, 2 on an
argument error. Standard library only, Python 3.8 or later. Python files
are read with the ast module; other files are compared as text.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

PASS, FAIL, WARN, SKIP, INFO = "PASS", "FAIL", "WARN", "SKIP", "INFO"
MAX_EXAMPLES = 5
TEST_PATH_RE = re.compile(r"(^|/)(tests?/|test_[^/]*$|[^/]*_test\.[^/]+$|[^/]*\.(test|spec)\.[^/]+$)")
ASSERT_LINE_RE = re.compile(r"\b(assert\w*|expect\w*|should\w*|verify\w*)\b", re.I)


@dataclass
class Result:
    name: str
    status: str
    count: int = 0
    examples: List[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict:
        return {"rule": self.name, "status": self.status, "count": self.count,
                "examples": self.examples[:MAX_EXAMPLES], "note": self.note}


def verdict(name: str, offenders: List[str], failing: str = FAIL, note: str = "", passing_note: str = "") -> Result:
    if offenders:
        return Result(name, failing, len(offenders), offenders, note)
    return Result(name, PASS, 0, [], passing_note)


def snapshot_files(before: str) -> List[str]:
    paths = []
    for root, dirs, files in os.walk(before):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            full = os.path.join(root, name)
            paths.append(os.path.relpath(full, before).replace(os.sep, "/"))
    return sorted(paths)


def read(path: str) -> Optional[str]:
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError):
        return None


@dataclass
class Signature:
    params: List[Tuple[str, str]]  # (kind, name)
    defaults: Dict[str, str]
    handlers_without_raise: int


def default_text(node: ast.AST) -> str:
    return ast.dump(node, annotate_fields=False)


def has_raise(handler: ast.ExceptHandler) -> bool:
    return any(isinstance(node, ast.Raise) for node in ast.walk(handler))


def signature_of(function) -> Signature:
    args = function.args
    params: List[Tuple[str, str]] = []
    defaults: Dict[str, str] = {}
    positional = list(getattr(args, "posonlyargs", [])) + list(args.args)
    for arg in positional:
        params.append(("positional", arg.arg))
    for arg, value in zip(positional[len(positional) - len(args.defaults):], args.defaults):
        defaults[arg.arg] = default_text(value)
    if args.vararg:
        params.append(("*args", args.vararg.arg))
    for arg, value in zip(args.kwonlyargs, args.kw_defaults):
        params.append(("keyword", arg.arg))
        if value is not None:
            defaults[arg.arg] = default_text(value)
    if args.kwarg:
        params.append(("**kwargs", args.kwarg.arg))
    handlers = sum(1 for node in ast.walk(function) if isinstance(node, ast.ExceptHandler) and not has_raise(node))
    return Signature(params, defaults, handlers)


def public_api(source: str) -> Optional[Dict[str, Signature]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    api: Dict[str, Signature] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            api[node.name] = signature_of(node)
        elif isinstance(node, ast.ClassDef):
            api[node.name] = Signature([], {}, 0)
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    api[f"{node.name}.{item.name}"] = signature_of(item)
    return api


def module_constants(source: str) -> Dict[str, str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name.isupper():
                constants[name] = default_text(node.value)
    return constants


def is_public(name: str) -> bool:
    return not any(part.startswith("_") and not (part.startswith("__") and part.endswith("__")) for part in name.split("."))


def compare_python(path: str, old: str, new: str, api: List[str], errors: List[str], constants: List[str]) -> None:
    old_api, new_api = public_api(old), public_api(new)
    if old_api is None or new_api is None:
        return
    for name, before in old_api.items():
        if not is_public(name):
            continue
        after = new_api.get(name)
        if after is None:
            api.append(f"{path}: {name} was removed or renamed")
            continue
        old_names = [param for param in before.params]
        new_names = [param for param in after.params]
        common = min(len(old_names), len(new_names))
        for index in range(common):
            if old_names[index] != new_names[index]:
                api.append(f"{path}: {name} parameter {old_names[index][1]!r} became {new_names[index][1]!r}; a caller passing it by name breaks")
                break
        else:
            if len(new_names) < len(old_names):
                api.append(f"{path}: {name} lost parameter(s) {[p[1] for p in old_names[common:]]}")
            for kind, added in new_names[common:]:
                if kind in ("positional", "keyword") and added not in after.defaults:
                    api.append(f"{path}: {name} gained required parameter {added!r}; existing callers break")
        for param, value in before.defaults.items():
            if param in after.defaults and after.defaults[param] != value:
                api.append(f"{path}: {name} default of {param!r} changed")
            elif param not in after.defaults and any(p[1] == param for p in after.params):
                api.append(f"{path}: {name} parameter {param!r} lost its default; callers that omit it break")
    for name, after in new_api.items():
        before = old_api.get(name)
        added = after.handlers_without_raise - (before.handlers_without_raise if before else 0)
        if added > 0:
            errors.append(f"{path}: {name} has {added} new except block(s) that do not re-raise; an error that used to stop the program is now hidden")
    old_constants, new_constants = module_constants(old), module_constants(new)
    for name, value in old_constants.items():
        if name in new_constants and new_constants[name] != value:
            constants.append(f"{path}: module constant {name} changed")


def compare_tests(path: str, old: str, new: str, offenders: List[str], added: List[str]) -> None:
    diff = list(difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0))
    removed_asserts = [line[1:].strip() for line in diff if line.startswith("-") and not line.startswith("---") and ASSERT_LINE_RE.search(line)]
    new_asserts = [line[1:].strip() for line in diff if line.startswith("+") and not line.startswith("+++") and ASSERT_LINE_RE.search(line)]
    for line in removed_asserts:
        offenders.append(f"{path}: expectation removed or changed: {line[:90]!r}")
    if new_asserts and not removed_asserts:
        added.append(f"{path}: {len(new_asserts)} expectation line(s) added")


def evaluate(before: str, after: str):
    """Compare the snapshot with the working directory. Returns (results, summary)."""
    results: List[Result] = []
    files = snapshot_files(before) if os.path.isdir(before) else []
    if not files:
        results.append(Result("snapshot-present", FAIL, 1, [f"no files under {before}"],
                              "copy each file to .ledger/before/<same path> before its first edit (SKILL.md gate 1); without it nothing can be compared"))
    else:
        results.append(Result("snapshot-present", PASS, 0, [], f"{len(files)} file(s) in the snapshot"))

    changed, missing, api, errors, constants, tests, tests_added = [], [], [], [], [], [], []
    for path in files:
        old = read(os.path.join(before, path))
        new = read(os.path.join(after, path))
        if new is None:
            missing.append(f"{path} is in the snapshot but gone from the working directory")
            continue
        if old is None or old == new:
            continue
        changed.append(path)
        if TEST_PATH_RE.search(path):
            compare_tests(path, old, new, tests, tests_added)
        elif path.endswith(".py"):
            compare_python(path, old, new, api, errors, constants)

    results.append(Result("files-changed", INFO, len(changed), changed, "files that differ from the snapshot") if files else Result("files-changed", SKIP, 0, [], "no snapshot"))
    results.append(verdict("files-deleted", missing, note="deleting a file is a behaviour change; it needs the ask"))
    results.append(verdict("public-signature", api, note="SKILL.md invariant 7: renaming, removing or changing a public function, parameter or default is a behaviour change; revert it, or show that the goal asks for it"))
    results.append(verdict("swallowed-errors", errors, note="SKILL.md invariant 10: catching an error and carrying on is not a fix unless the goal asks for it"))
    results.append(verdict("test-expectations", tests, note="SKILL.md invariant 10: a test's expectation changed or removed; revert it, or name the goal's reason in the answer"))
    results.append(verdict("module-constants", constants, failing=WARN, note="a changed constant is a changed default for every caller; name it in the answer"))
    if tests_added:
        results.append(Result("tests-added", INFO, len(tests_added), tests_added, "new expectations only"))
    return results, {"snapshot_files": len(files), "changed": len(changed)}


def summary_line(results: List[Result]) -> str:
    exit_code = 1 if any(result.status == FAIL for result in results) else 0
    counts = {status: sum(1 for result in results if result.status == status) for status in (PASS, FAIL, WARN, SKIP, INFO)}
    return f"{'OK' if exit_code == 0 else 'NOT OK'}: " + " ".join(f"{s}={c}" for s, c in counts.items() if c) + f"; exit {exit_code}"


def print_results(results: List[Result]) -> None:
    for result in results:
        print(f"{result.status:<4} {result.name:<26} {result.count}")
        for example in result.examples[:MAX_EXAMPLES]:
            print(f"       - {example}")
        if result.note:
            print(f"       note: {result.note}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--before", required=True, help="the snapshot folder, such as .ledger/before")
    parser.add_argument("--after", required=True, help="the working directory")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not os.path.isdir(args.after):
        print(f"check_change: {args.after} is not a directory", file=sys.stderr)
        return 2
    results, summary = evaluate(args.before, args.after)
    exit_code = 1 if any(result.status == FAIL for result in results) else 0
    if args.json:
        print(json.dumps({"tool": "check_change", "before": args.before, "after": args.after, "summary": summary,
                          "results": [result.to_dict() for result in results], "exit_code": exit_code}, indent=2))
        return exit_code
    print(f"check_change: {args.before} -> {args.after}")
    print("  " + ", ".join(f"{key}={value}" for key, value in summary.items()))
    print_results(results)
    print(summary_line(results))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
