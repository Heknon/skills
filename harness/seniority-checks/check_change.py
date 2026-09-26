#!/usr/bin/env python3
"""Judge a code change against the snapshot taken before it.

Usage: check_change.py --before DIR --after DIR [--json]

--before is the snapshot folder (.ledger/before), holding a copy of every
file as it was before its first edit, at the same relative path. --after
is the working directory. Only files present in the snapshot are compared.
A public name that moved and stays importable from its old module (a
`from x import name` at module level) is compared where it now lives, and
a module that became a package (`util.py` to `util/__init__.py`) is
compared as the same module, so a correct move or split is not a removal.

Every rule prints PASS, FAIL, WARN, SKIP or INFO, a count, up to five
offenders and a note. Exit 0 when no rule is FAIL, 1 when any is, 2 on an
argument error. Standard library only, Python 3.8 or later. Python files
are read with the ast module; other files are compared as text.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import glob
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
    variable: bool = False  # a module-level value, not a callable: only its presence is compared


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
        targets = []
        if isinstance(node, ast.Assign) and not isinstance(node.value, (ast.Name, ast.Attribute)):
            targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None \
                and not isinstance(node.value, (ast.Name, ast.Attribute)):
            targets = [node.target.id]
        for target in targets:  # aliases (`old = new`) are resolved by find_signature instead
            if target != "__all__":
                api[target] = Signature([], {}, 0, variable=True)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            api[node.name] = signature_of(node)
        elif isinstance(node, ast.ClassDef):
            api[node.name] = Signature([], {}, 0)
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    api[f"{node.name}.{item.name}"] = signature_of(item)
    return api


def module_tree(source: str) -> Optional[ast.Module]:
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def reexports(source: str) -> Dict[str, Tuple[str, int, str]]:
    """Names a module imports at top level with `from X import name`: {local name: (module, level, original name)}."""
    tree = module_tree(source)
    names: Dict[str, Tuple[str, int, str]] = {}
    for node in tree.body if tree else []:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    names[alias.asname or alias.name] = (node.module or "", node.level, alias.name)
    return names


def module_imports(source: str) -> Dict[str, Tuple[str, int]]:
    """Modules bound to a name at top level (`import a.b as m`, `import a`, `from pkg import mod`): {name: (module, level)}.
    A `from pkg import name` is listed too, since `name` may be a module; resolution decides."""
    tree = module_tree(source)
    bound: Dict[str, Tuple[str, int]] = {}
    for node in tree.body if tree else []:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    bound[alias.asname] = (alias.name, 0)
                else:
                    bound[alias.name.split(".")[0]] = (alias.name.split(".")[0], 0)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    module = ".".join(part for part in (node.module or "", alias.name) if part)
                    bound[alias.asname or alias.name] = (module, node.level)
    return bound


def star_imports(source: str) -> List[Tuple[str, int]]:
    tree = module_tree(source)
    return [(node.module or "", node.level) for node in (tree.body if tree else [])
            if isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names)]


def aliases(source: str) -> Dict[str, str]:
    """Names bound to another name: module level `old = new` or `old = mod.new`, and class level
    `old_method = new_method`. {alias: target}, targets dotted as written."""
    tree = module_tree(source)
    found: Dict[str, str] = {}

    def dotted(node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            base = dotted(node.value)
            return f"{base}.{node.attr}" if base else None
        return None

    for node in tree.body if tree else []:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target = dotted(node.value)
            if target:
                found[node.targets[0].id] = target
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.Assign) and len(item.targets) == 1 and isinstance(item.targets[0], ast.Name) \
                        and isinstance(item.value, ast.Name):
                    found[f"{node.name}.{item.targets[0].id}"] = f"{node.name}.{item.value.id}"
    return found


def dunder_all(source: str) -> Optional[List[str]]:
    """A module's literal `__all__`, or None when it has none (or builds it dynamically)."""
    tree = module_tree(source)
    for node in tree.body if tree else []:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets) \
                and isinstance(node.value, (ast.List, ast.Tuple)):
            return [element.value for element in node.value.elts
                    if isinstance(element, ast.Constant) and isinstance(element.value, str)]
    return None


def has_module_getattr(source: str) -> bool:
    tree = module_tree(source)
    return any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "__getattr__"
               for node in (tree.body if tree else []))


_ROOTS: Dict[str, List[str]] = {}


def import_roots(after: str) -> List[str]:
    """Folders an absolute import may be rooted at: the working directory, and every `src` folder
    up to three levels down (`src`, `packages/core/src`)."""
    if after not in _ROOTS:
        roots = [""]
        for depth in ("src", "*/src", "*/*/src", "*/*/*/src"):
            for found in sorted(glob.glob(os.path.join(after, depth))):
                if os.path.isdir(found):
                    roots.append(os.path.relpath(found, after))
        _ROOTS[after] = roots
    return _ROOTS[after]


def resolve_module(after: str, path: str, module: str, level: int) -> Tuple[Optional[str], bool]:
    """The file inside the working directory that an import from `path` names.
    Returns (file, local): local is True when the module belongs to this project (a relative import,
    or a top-level package that exists here), so a missing file is a real break, not a third-party module."""
    parts: List[str] = []
    if level:
        base = os.path.dirname(path)
        for _ in range(level - 1):
            base = os.path.dirname(base)
        if base:
            parts.append(base)
    parts.extend(part for part in module.split(".") if part)
    stem = os.path.join(*parts) if parts else ""
    candidates = [stem + ".py", os.path.join(stem, "__init__.py")] if stem else ["__init__.py"]
    roots = [""] if level else import_roots(after)
    for root in roots:
        for candidate in candidates:
            full = os.path.join(after, root, candidate)
            if os.path.isfile(full):
                return full, True
    if level:
        return None, True
    top = module.split(".")[0]
    local = any(os.path.isdir(os.path.join(after, root, top)) or os.path.isfile(os.path.join(after, root, top + ".py"))
                for root in roots)
    return None, local


def find_signature(after: str, path: str, source: str, name: str, depth: int = 0) -> Tuple[Optional[Signature], bool]:
    """Look a public name up in a module, following aliases, re-exports, module attributes and star
    imports. Returns (signature, resolved); resolved is False when the name comes from somewhere that
    cannot be read (a module outside the project, a module-level __getattr__)."""
    if depth > 5:
        return None, False
    api = public_api(source) or {}
    if name in api:
        return api[name], True
    head, _, rest = name.partition(".")
    suffix = "." + rest if rest else ""

    def follow(module: str, level: int, inner: str) -> Tuple[Optional[Signature], bool]:
        target, local = resolve_module(after, path, module, level)
        text = read(target) if target else None
        if text is None:
            return None, local  # a missing module of this project is a break; a third-party one cannot be read
        target_path = os.path.relpath(target, after).replace(os.sep, "/")
        return find_signature(after, target_path, text, inner, depth + 1)

    known = aliases(source)
    if name in known:  # a class-level method alias, Class.old = Class.new
        return find_signature(after, path, source, known[name], depth + 1)
    if head in known:
        return find_signature(after, path, source, known[head] + suffix, depth + 1)
    imports = reexports(source)
    if head in imports:
        module, level, original = imports[head]
        signature, resolved = follow(module, level, original + suffix)
        if signature is not None or not rest:
            return signature, resolved
    bound = module_imports(source)
    if head in bound and rest:  # `import money` then `total = money.total`, reached through an alias
        module, level = bound[head]
        return follow(module, level, rest)
    for module, level in star_imports(source):
        target, _ = resolve_module(after, path, module, level)
        text = read(target) if target else None
        exported = dunder_all(text) if text is not None else None
        if exported is not None and head not in exported:
            continue  # `import *` only brings names listed in the target's __all__
        signature, resolved = follow(module, level, name)
        if signature is not None:
            return signature, True
    if has_module_getattr(source):
        return None, False
    return None, True


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


def cli_options(source: str) -> Dict[str, str]:
    """Every add_argument(...) call: its flag or name, mapped to its action, default, type and nargs."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    options: Dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument":
            names = [arg.value for arg in node.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str)]
            if not names:
                continue
            settings = {keyword.arg: default_text(keyword.value) for keyword in node.keywords
                        if keyword.arg in ("action", "default", "type", "nargs", "required", "choices", "dest")}
            options[" ".join(sorted(names))] = json.dumps(settings, sort_keys=True)
    return options


def is_public(name: str) -> bool:
    return not any(part.startswith("_") and not (part.startswith("__") and part.endswith("__")) for part in name.split("."))


def compare_python(path: str, old: str, new: str, api: List[str], errors: List[str], constants: List[str],
                   after_root: Optional[str] = None, moved_from: Optional[Dict[str, int]] = None) -> None:
    old_api, new_api = public_api(old), public_api(new)
    if old_api is None or new_api is None:
        return
    for name, before in old_api.items():
        if not is_public(name):
            continue
        after = new_api.get(name)
        if after is None and after_root is not None:
            after, resolved = find_signature(after_root, path, new, name)
            if after is None and not resolved:
                continue  # re-exported from outside the working directory; its signature cannot be read
        if after is None:
            api.append(f"{path}: {name} was removed or renamed")
            continue
        if before.variable or after.variable:
            continue  # a value that still exists; module-constants reports a changed constant
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
        if before is not None:
            baseline = before.handlers_without_raise
        else:  # new here: a function moved from another snapshot file keeps its old count
            baseline = (moved_from or {}).get(name, 0)
        added = after.handlers_without_raise - baseline
        if added > 0:
            errors.append(f"{path}: {name} has {added} new except block(s) that do not re-raise; an error that used to stop the program is now hidden")
    old_options, new_options = cli_options(old), cli_options(new)
    for flag, settings in old_options.items():
        if flag not in new_options:
            api.append(f"{path}: command-line option {flag} was removed or renamed; scripts and people that pass it break")
        elif new_options[flag] != settings:
            api.append(f"{path}: command-line option {flag} changed its action, default or type; running the program the same way now does something else")
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
    moved_from: Dict[str, int] = {}
    for path in files:
        if path.endswith(".py") and not TEST_PATH_RE.search(path):
            for name, signature in (public_api(read(os.path.join(before, path)) or "") or {}).items():
                moved_from[name] = max(moved_from.get(name, 0), signature.handlers_without_raise)
    for path in files:
        old = read(os.path.join(before, path))
        new = read(os.path.join(after, path))
        compared_as = path
        if new is None and path.endswith(".py"):
            package_init = path[:-3] + "/__init__.py"
            new = read(os.path.join(after, package_init))
            if new is not None:
                compared_as = package_init
        if new is None:
            missing.append(f"{path} is in the snapshot but gone from the working directory")
            continue
        if old is None or old == new:
            continue
        changed.append(path if compared_as == path else f"{path} became the package {compared_as}")
        if TEST_PATH_RE.search(path):
            compare_tests(path, old, new, tests, tests_added)
        elif path.endswith(".py"):
            compare_python(compared_as, old, new, api, errors, constants, after_root=after, moved_from=moved_from)

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
