"""Read a unified diff and print what a reviewer needs next. Standard library only.

Run from the repository under review, with its own interpreter:

    uv run --no-sync python <skill>/recipes/review_diff.py scope review.diff
    uv run --no-sync python <skill>/recipes/review_diff.py defs review.diff
    uv run --no-sync python <skill>/recipes/review_diff.py signs review.diff
    uv run --no-sync python <skill>/recipes/review_diff.py newerrors base.txt head.txt

scope      every file with its lines added and removed, largest first, and
           groups of files that received the same edit (digits ignored)
defs       functions, methods and module names whose contract changed:
           parameters, defaults, return annotation, exceptions raised,
           `return None`, moves between files. Each one needs its callers read.
signs      lines that match a checklist sign (the `## Signs` blocks of
           <skill>/checklists/*.md): leads to open and judge, never findings.
           TST signs read test files only; every other sign reads the rest
newerrors  tool lines (ruff concise, mypy) in head.txt that base.txt does not
           have, compared without line and column numbers

The diff is a file written by `git diff --output=review.diff <base>...HEAD`
or a patch file. UTF-8 and UTF-16 (what PowerShell 5.1 `>` writes) are read.
`defs` reads the old files with `git cat-file` from the blob ids on the
diff's `index` lines, so run it inside the repository; the new files are
rebuilt from the old ones and the hunks, so the head need not be checked out.
Exit code: 0, or 2 on a usage or reading error.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
INDEX = re.compile(r"^index ([0-9a-f]+)\.\.([0-9a-f]+)")


@dataclass
class Hunk:
    old_start: int
    new_start: int
    lines: list[str] = field(default_factory=list)  # with their ' ', '+', '-'


@dataclass
class FileDiff:
    old_path: str | None
    new_path: str | None
    old_blob: str | None = None
    hunks: list[Hunk] = field(default_factory=list)
    binary: bool = False

    @property
    def path(self) -> str:
        return self.new_path or self.old_path or "?"

    def added(self) -> list[tuple[int, str]]:
        out = []
        for hunk in self.hunks:
            line_no = hunk.new_start
            for line in hunk.lines:
                if line.startswith("+"):
                    out.append((line_no, line[1:]))
                    line_no += 1
                elif line.startswith(" "):
                    line_no += 1
        return out

    def removed(self) -> list[tuple[int, str]]:
        out = []
        for hunk in self.hunks:
            line_no = hunk.old_start
            for line in hunk.lines:
                if line.startswith("-"):
                    out.append((line_no, line[1:]))
                    line_no += 1
                elif line.startswith(" "):
                    line_no += 1
        return out


def read_text(path: str) -> str:
    raw = Path(path).read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig", errors="replace")


def strip_prefix(name: str) -> str | None:
    name = name.strip().split("\t")[0]
    if name == "/dev/null":
        return None
    if name[:2] in ("a/", "b/"):
        return name[2:]
    return name


def parse_diff(text: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    current: FileDiff | None = None
    hunk: Hunk | None = None
    for line in text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split(" ")
            current = FileDiff(strip_prefix(parts[2]), strip_prefix(parts[3]))
            files.append(current)
            hunk = None
        elif current is None:
            continue  # mail headers or text before the first file
        elif line.startswith("--- ") and hunk is None:
            current.old_path = strip_prefix(line[4:])
        elif line.startswith("+++ ") and hunk is None:
            current.new_path = strip_prefix(line[4:])
        elif match := INDEX.match(line):
            current.old_blob = match.group(1)
        elif line.startswith("Binary files"):
            current.binary = True
        elif line.startswith("rename from "):
            current.old_path = line[len("rename from ") :]
        elif line.startswith("rename to "):
            current.new_path = line[len("rename to ") :]
        elif match := HUNK.match(line):
            hunk = Hunk(int(match.group(1)), int(match.group(3)))
            current.hunks.append(hunk)
        elif hunk is not None and line[:1] in (" ", "+", "-"):
            hunk.lines.append(line)
        elif hunk is not None and line == "":
            hunk.lines.append(" ")  # a blank context line whose space was lost
    return files


# ---------------------------------------------------------------- scope


def normalise(line: str) -> str:
    return re.sub(r"\d+", "N", line.strip())


def cmd_scope(files: list[FileDiff]) -> None:
    info = {}
    for f in files:
        if f.old_path is None:
            kind = "added"
        elif f.new_path is None:
            kind = "deleted"
        elif f.old_path != f.new_path:
            kind = f"renamed from {f.old_path}"
        else:
            kind = "modified"
        if f.binary:
            kind += ", binary"
        info[f.path] = (len(f.added()), len(f.removed()), kind)
    total_add = sum(a for a, _, _ in info.values())
    total_del = sum(r for _, r, _ in info.values())
    print(f"{len(files)} files, +{total_add} -{total_del}")
    groups: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for f in files:
        edit = tuple(
            ["-" + normalise(t) for _, t in f.removed()]
            + ["+" + normalise(t) for _, t in f.added()]
        )
        if edit:
            groups[edit].append(f.path)
    same = [(edit, paths) for edit, paths in groups.items() if len(paths) > 1]
    grouped = {path for _, paths in same for path in paths}
    lone = [path for path in info if path not in grouped]
    lone.sort(key=lambda p: (-(info[p][0] + info[p][1]), p))
    print(f"files with an edit of their own: {len(lone)}, largest first")
    for path in lone:
        add, rem, kind = info[path]
        print(f"  {path}  +{add} -{rem}  {kind}")
    if not same:
        print("no two files received the same edit")
    for edit, paths in sorted(same, key=lambda item: -len(item[1])):
        print(f"same edit in {len(paths)} files (digits read as N):")
        for line in edit:
            print(f"    {line}")
        print("  files: " + ", ".join(paths))


# ---------------------------------------------------------------- defs


def git_blob(blob: str | None) -> str | None:
    if not blob or set(blob) == {"0"}:
        return None
    done = subprocess.run(
        ["git", "cat-file", "-p", blob],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return done.stdout if done.returncode == 0 else None


def apply_hunks(old: str | None, f: FileDiff) -> str | None:
    if f.new_path is None:
        return None
    old_lines = (old or "").splitlines()
    out: list[str] = []
    pos = 0  # index into old_lines
    for hunk in f.hunks:
        start = max(hunk.old_start - 1, 0) if old_lines else 0
        out.extend(old_lines[pos:start])
        pos = start
        for line in hunk.lines:
            if line.startswith("+"):
                out.append(line[1:])
            elif line.startswith("-"):
                pos += 1
            else:
                out.append(old_lines[pos] if pos < len(old_lines) else line[1:])
                pos += 1
    out.extend(old_lines[pos:])
    return "\n".join(out) + "\n"


@dataclass
class Def:
    path: str
    line: int
    params: list[str]
    returns: str
    raises: set[str]
    returns_none: bool


def raised_name(node: ast.Raise) -> str | None:
    exc = node.exc
    if exc is None:
        return "(re-raise)"
    if isinstance(exc, ast.Call):
        exc = exc.func
    return ast.unparse(exc)


def own_nodes(func: ast.AST):
    """The nodes of a function, without those of functions nested in it."""
    stack = list(ast.iter_child_nodes(func))
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        yield node
        stack.extend(ast.iter_child_nodes(node))


def describe_params(args: ast.arguments) -> list[str]:
    out = []
    positional = args.posonlyargs + args.args
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    for arg, default in zip(positional, defaults, strict=True):
        text = arg.arg
        if arg.annotation is not None:
            text += ": " + ast.unparse(arg.annotation)
        if default is not None:
            text += " = " + ast.unparse(default)
        out.append(text)
    if args.vararg:
        out.append("*" + args.vararg.arg)
    elif args.kwonlyargs:
        out.append("*")
    for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=True):
        text = arg.arg
        if arg.annotation is not None:
            text += ": " + ast.unparse(arg.annotation)
        if default is not None:
            text += " = " + ast.unparse(default)
        out.append(text)
    if args.kwarg:
        out.append("**" + args.kwarg.arg)
    return out


def collect(path: str, source: str | None) -> tuple[dict[str, Def], dict[str, int]]:
    """Functions and methods (as Def), module-level names, and class fields.

    A class's annotated fields are kept as a Def named <Class>.<fields>
    whose params list the fields, so a changed model or dataclass shows.
    """
    defs: dict[str, Def] = {}
    names: dict[str, int] = {}
    if source is None or not path.endswith(".py"):
        return defs, names
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        print(f"  cannot parse {path}: {exc}")
        return defs, names

    def visit(body: list[ast.stmt], prefix: str) -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                nodes = list(own_nodes(node))
                raises = {
                    n
                    for r in nodes
                    if isinstance(r, ast.Raise)
                    if (n := raised_name(r))
                }
                none = any(
                    isinstance(r, ast.Return)
                    and (
                        r.value is None
                        or (isinstance(r.value, ast.Constant) and r.value.value is None)
                    )
                    for r in nodes
                )
                defs[prefix + node.name] = Def(
                    path,
                    node.lineno,
                    describe_params(node.args),
                    ast.unparse(node.returns) if node.returns else "(none)",
                    raises,
                    none,
                )
            elif isinstance(node, ast.ClassDef):
                if not prefix:
                    names[node.name] = node.lineno
                fields = [
                    ast.unparse(item.target)
                    + ": "
                    + ast.unparse(item.annotation)
                    + (
                        " = " + ast.unparse(item.value)
                        if item.value is not None
                        else ""
                    )
                    for item in node.body
                    if isinstance(item, ast.AnnAssign)
                ]
                if fields:
                    defs[prefix + node.name + ".<fields>"] = Def(
                        path, node.lineno, fields, "(none)", set(), False
                    )
                visit(node.body, prefix + node.name + ".")
            elif not prefix and isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
                for target in targets:
                    if isinstance(target, ast.Name):
                        names[target.id] = node.lineno

    visit(tree.body, "")
    return defs, names


def cmd_defs(files: list[FileDiff]) -> None:
    old_defs: dict[str, Def] = {}
    new_defs: dict[str, Def] = {}
    unread = []
    removed_names: dict[str, list[str]] = defaultdict(list)
    new_names: dict[str, str] = {}
    for f in files:
        if not f.path.endswith(".py"):
            continue
        old = git_blob(f.old_blob) if f.old_path else None
        if f.old_path and old is None:
            unread.append(f.path)
            continue
        new = apply_hunks(old, f)
        od, on = collect(f.old_path or "", old)
        nd, nn = collect(f.new_path or "", new)
        old_defs.update(od)
        new_defs.update(nd)
        for name in sorted(set(on) - set(nn)):
            removed_names[name].append(f"{f.old_path}:{on[name]}")
        for name, line in nn.items():
            new_names[name] = f"{f.new_path}:{line}"
    changed = 0
    tests_removed = []
    for name in sorted(set(old_defs) | set(new_defs)):
        a, b = old_defs.get(name), new_defs.get(name)
        notes = []
        if a and not b and name.split(".")[-1].startswith("test"):
            tests_removed.append(f"{a.path}:{a.line}  {name}")
            continue
        if a and not b:
            twin = next(
                (
                    n
                    for n, d in new_defs.items()
                    if n not in old_defs
                    and d.path == a.path
                    and abs(d.line - a.line) <= 2
                    and n.endswith(".<fields>") == name.endswith(".<fields>")
                ),
                None,
            )
            if twin is None:
                notes.append("removed (was " + f"{a.path}:{a.line})")
            else:
                b = new_defs[twin]
                notes.append(f"renamed to {twin}? (a new def at the same place)")
                if a.params != b.params:
                    before, after = ", ".join(a.params), ", ".join(b.params)
                    notes.append(f"parameters: ({before}) -> ({after})")
                if a.returns != b.returns:
                    notes.append(f"return annotation: {a.returns} -> {b.returns}")
        elif b and not a:
            continue  # new code: its callers are in the diff
        else:
            assert a and b
            if a.path != b.path:
                notes.append(f"moved from {a.path}:{a.line}")
            if a.params != b.params and name.endswith(".<fields>"):
                gone = [p for p in a.params if p not in b.params]
                added = [p for p in b.params if p not in a.params]
                notes.append(
                    "fields: "
                    + "; ".join([f"-{p}" for p in gone] + [f"+{p}" for p in added])
                )
            elif a.params != b.params:
                notes.append(
                    f"parameters: ({', '.join(a.params)}) -> ({', '.join(b.params)})"
                )
            if a.returns != b.returns:
                notes.append(f"return annotation: {a.returns} -> {b.returns}")
            if a.raises - b.raises:
                notes.append(
                    "no longer raises: " + ", ".join(sorted(a.raises - b.raises))
                )
            if b.raises - a.raises:
                notes.append("now raises: " + ", ".join(sorted(b.raises - a.raises)))
            if b.returns_none and not a.returns_none:
                notes.append("now returns None somewhere")
        if not notes:
            continue
        changed += 1
        where = f"{b.path}:{b.line}" if b else f"{a.path}:{a.line}"  # type: ignore[union-attr]
        print(f"{where}  {name}")
        for note in notes:
            print(f"    {note}")
        short = name.replace(".<fields>", "").split(".")[-1]
        print(f"    callers: search \\b{short}\\b outside the diff")
    for name, places in sorted(removed_names.items()):
        if name in new_defs:
            continue
        changed += 1
        more = " ..." if len(places) > 3 else ""
        print(f"{', '.join(places[:3])}{more}  module name {name}")
        if name in new_names:
            print(f"    moved to {new_names[name]}; importers of the old module break")
        else:
            print(f"    removed from {len(places)} module(s); importers of it break")
        print(f"    callers: search \\b{name}\\b outside the diff")
    print(f"{changed} changed contract(s)")
    for removed_test in tests_removed:
        print(f"test removed: {removed_test}")
    for path in unread:
        print(
            f"not read: {path} (its old blob is not in this repository; fetch the base)"
        )


# ---------------------------------------------------------------- signs


def load_signs(folder: Path) -> list[tuple[str, str, re.Pattern[str]]]:
    signs = []
    for md in sorted(folder.glob("*.md")):
        in_block = in_signs = False
        for line in md.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                in_signs = line.strip() == "## Signs"
            elif in_signs and line.startswith("```"):
                in_block = not in_block
            elif in_signs and in_block and line.strip():
                parts = line.split(None, 2)
                if len(parts) == 3 and parts[1] in ("+", "-"):
                    signs.append((parts[0], parts[1], re.compile(parts[2])))
    return signs


def is_test(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return "tests/" in path or name.startswith("test_") or name == "conftest.py"


def cmd_signs(files: list[FileDiff], folder: Path) -> None:
    signs = load_signs(folder)
    if not signs:
        print(f"no signs found under {folder}")
        return
    hits = 0
    for f in files:
        test_file = is_test(f.path)
        for side, lines in (("+", f.added()), ("-", f.removed())):
            for line_no, text in lines:
                for sign_id, sign_side, pattern in signs:
                    if test_file != sign_id.startswith("TST"):
                        continue  # TST signs read test files; the others read code
                    if sign_side == side and pattern.search(text):
                        hits += 1
                        mark = "" if side == "+" else " (removed line, old numbering)"
                        print(f"{f.path}:{line_no}  {sign_id}{mark}  {text.strip()}")
    print(f"{hits} lead(s) from {len(signs)} signs; open each line and decide")


# ---------------------------------------------------------------- newerrors

RUFF = re.compile(
    r"^(?P<path>[^:\s][^:]*):(?P<line>\d+):(?P<col>\d+): (?P<rest>[A-Z]+\d+ .*)$"
)
MYPY = re.compile(r"^(?P<path>[^:\s][^:]*):(?P<line>\d+): (?P<rest>(error|note): .*)$")


def tool_lines(path: str) -> list[tuple[str, str]]:
    out = []
    for line in read_text(path).splitlines():
        match = RUFF.match(line) or MYPY.match(line)
        if match and not match.group("rest").startswith("note:"):
            key = (
                match.group("path").replace("\\", "/")
                + ": "
                + match.group("rest").strip()
            )
            out.append((key, line))
    return out


def cmd_newerrors(before: str, after: str) -> None:
    base = Counter(key for key, _ in tool_lines(before))
    new = []
    for key, line in tool_lines(after):
        if base[key]:
            base[key] -= 1
        else:
            new.append(line)
    for line in new:
        print(line)
    print(f"{len(new)} new tool line(s) in {after} that {before} does not have")


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in {"scope", "defs", "signs", "newerrors"}:
        print(__doc__)
        return 2
    try:
        if argv[0] == "newerrors":
            cmd_newerrors(argv[1], argv[2])
            return 0
        files = parse_diff(read_text(argv[1]))
    except (OSError, IndexError) as exc:
        print(f"cannot read: {exc}")
        return 2
    if not files:
        print(
            "no file diffs found: is this a unified diff (git diff, git format-patch)?"
        )
        return 2
    if argv[0] == "scope":
        cmd_scope(files)
    elif argv[0] == "defs":
        cmd_defs(files)
    else:
        cmd_signs(files, Path(__file__).resolve().parent.parent / "checklists")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
