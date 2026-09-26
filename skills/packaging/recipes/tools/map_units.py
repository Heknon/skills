"""Map a repository's units and the ties between them. Changes nothing.

Standard library only (Python 3.11 or later; tested on 3.12). Run it
from the repository root:

    uv run --no-project python map_units.py .

A unit is a folder that builds, runs or deploys on its own (its own
pyproject.toml, setup.py, requirements file, Dockerfile, __main__.py, a
main guard, a CI line naming it), or a folder of Python code that other
units import. The report lists each unit with its signs, then every tie
it found (imports across units, sys.path lines, PYTHONPATH settings,
path and workspace sources, requirement files and who reads them, copied
modules), the Dockerfiles' install and run lines, then the folders the
evidence cannot place. Each line carries file:line so it can be checked
by hand. Virtual environments (any folder with pyvenv.cfg), .git and
caches are skipped. Exit code: 0, or 2 when the argument is not a
folder.
"""

from __future__ import annotations

import ast
import hashlib
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import tomllib

SKIP = {".git", ".venv", "venv", "node_modules", "__pycache__",
        "dist", "build", ".tox", ".nox", ".mypy_cache", ".pytest_cache",
        ".ruff_cache", "site-packages", ".idea", ".vscode"}
CI_NAMES = {".gitlab-ci.yml", "Jenkinsfile", "Makefile", "justfile",
            "tox.ini", "noxfile.py", "azure-pipelines.yml"}
TEXT_SUFFIXES = {".yml", ".yaml", ".toml", ".ini", ".cfg", ".sh", ".ps1",
                 ".bat", ".cmd", ".env", ".txt", ".md", ".json"}
BUILD_SIGNS = ("pyproject.toml", "setup.py", "setup.cfg")
GENERIC_NAMES = {"__init__.py", "__main__.py", "conftest.py", "main.py",
                 "setup.py", "app.py", "config.py", "settings.py"}
MAIN_GUARD = re.compile(r"""^if\s+__name__\s*==\s*['"]__main__['"]""", re.MULTILINE)
SYSPATH = re.compile(r"sys\.path\.(insert|append|extend)\s*\(|site\.addsitedir\s*\(")
PYTHONPATH = re.compile(r"PYTHONPATH")
REQ_PATH = re.compile(r"^\s*(-e\s+)?(\.{1,2}[/\\]|file:)")


def files(root: Path) -> list[Path]:
    """Every file under root, leaving out virtual environments and caches."""
    out = []
    for folder, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.endswith(".egg-info")
                   and not (Path(folder) / d / "pyvenv.cfg").exists()]
        out.extend(Path(folder, n).relative_to(root) for n in names)
    return sorted(out)


def read(root: Path, rel: Path) -> str:
    try:
        return (root / rel).read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


def is_ci(rel: Path) -> bool:
    return (rel.name in CI_NAMES or rel.name.endswith(".gitlab-ci.yml")
            or rel.parts[:2] == (".github", "workflows"))


def is_docker(rel: Path) -> bool:
    name = rel.name.lower()
    return "dockerfile" in name or "containerfile" in name


def main(argv: list[str]) -> int:
    if len(argv) > 1 and argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"map_units: not a folder: {root}", file=sys.stderr)
        return 2
    all_files = files(root)
    py = [f for f in all_files if f.suffix == ".py"]
    texts = {f: read(root, f) for f in all_files
             if f.suffix in TEXT_SUFFIXES or f.suffix == ".py" or is_docker(f)
             or is_ci(f) or f.name.startswith(".env") or f.name in CI_NAMES}

    # 1. Signs per folder.
    signs: dict[Path, list[str]] = defaultdict(list)
    for f in all_files:
        d = f.parent
        if f.name in BUILD_SIGNS or f.name.startswith("requirements") and f.suffix in {".txt", ".in"} or is_docker(f) and any(p.parent == d or d in p.parents for p in py):
            signs[d].append(f.name)
        elif f.name == "__main__.py" and not (root / d.parent / "__init__.py").exists():
            signs[d].append("__main__.py")
        elif f.suffix == ".py" and MAIN_GUARD.search(texts.get(f, "")) \
                and "tests" not in f.parts and not f.name.startswith("test_"):
            signs[d].append(f"main guard in {f.name}")
    # A main guard or __main__.py inside a project belongs to that project.
    def owns(p: Path) -> bool:
        if p == Path("."):
            try:
                return "project" in tomllib.loads(read(root, Path("pyproject.toml")))
            except tomllib.TOMLDecodeError:
                return False
        return any((root / p / b).exists() for b in BUILD_SIGNS)

    for d in sorted(signs, key=lambda x: -len(x.parts)):
        owner = next((p for p in [d, *d.parents] if owns(p)), None)
        if owner is not None and owner != d:
            where = d.relative_to(owner).as_posix()
            signs[owner].extend(f"{x} ({where})" for x in signs.pop(d))
    root_signs = signs.pop(Path("."), [])

    # A pyproject's scripts and workspace.
    projects: dict[Path, dict] = {}
    for f in all_files:
        if f.name == "pyproject.toml":
            try:
                projects[f.parent] = tomllib.loads(read(root, f))
            except tomllib.TOMLDecodeError as exc:
                print(f"note: {f.as_posix()} does not parse: {exc}")

    # 2. Code roots: top-level packages and loose modules, and where they sit.
    code: dict[str, Path] = {}          # dotted import name -> its folder or file

    def import_root(start: Path) -> Path:
        for d in [start, *start.parents]:
            if d.name == "src" or any((root / d / s).exists() for s in BUILD_SIGNS):
                return d
        return Path(".")

    for f in py:
        top = f.parent if (root / f.parent / "__init__.py").exists() else None
        while top is not None and top != Path(".") \
                and (root / top.parent / "__init__.py").exists():
            top = top.parent
        if top is not None and top != Path("."):
            base = import_root(top.parent)
            code.setdefault(".".join(top.relative_to(base).parts), top)
        elif f.name not in {"__init__.py", "__main__.py", "conftest.py"} \
                and "tests" not in f.parts and not f.name.startswith("test_"):
            code.setdefault(f.stem, f)

    def lookup(name: str) -> Path | None:
        parts = name.split(".")
        for i in range(len(parts), 0, -1):
            if ".".join(parts[:i]) in code:
                return code[".".join(parts[:i])]
        return None

    # 3. Units: sign folders, then code folders outside every sign folder.
    units: list[Path] = sorted(signs)
    root_project = Path(".") in projects and "project" in projects[Path(".")]

    def unit_of(rel: Path) -> Path:
        best = Path(".")
        for u in units:
            if (rel == u or u in rel.parents) and len(u.parts) > len(best.parts):
                best = u
        return best

    for where in sorted(code.values()):
        folder = where if (root / where).is_dir() else where.parent
        if folder == Path(".") or unit_of(folder) != Path("."):
            continue
        if root_project and (folder.parts[0] in {"src", "tests", "test", "docs"}
                             or (root / folder / "__init__.py").exists()):
            continue                    # the root project's own packages
        top = Path(folder.parts[0]) if folder.parts[0] not in {"src", "lib"} else folder
        if top not in units:
            units.append(top)
    units.sort()

    # CI lines that name a unit folder.
    ci_lines: dict[Path, list[str]] = defaultdict(list)
    for f, text in texts.items():
        if not (is_ci(f)):
            continue
        job = ""
        for n, line in enumerate(text.splitlines(), 1):
            m = re.match(r"^([A-Za-z0-9_.-]+):\s*$", line)
            if m and f.name.endswith(".gitlab-ci.yml"):
                job = m.group(1)
            for u in units:
                if re.search(rf"(^|[\s\"'=/]){re.escape(u.as_posix())}/", line):
                    where = f"{f.as_posix()}:{n}" + (f" job {job}" if job else "")
                    ci_lines[u].append(f"{where}: {line.strip()}")

    # 4. Imports across units (and across top-level packages of one project).
    imports: list[str] = []
    importers: dict[Path, set[Path]] = defaultdict(set)
    pkg_ties: list[str] = []
    pkg_importers: dict[Path, set[str]] = defaultdict(set)
    for f in py:
        try:
            tree = ast.parse(texts.get(f) or read(root, f))
        except SyntaxError:
            continue
        mine = unit_of(f)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                target = lookup(name)
                if target is None:
                    continue
                other = unit_of(target)
                text = ast.get_source_segment(texts.get(f, ""), node) or name
                if other != mine:
                    imports.append(f"{f.as_posix()}:{node.lineno}: {text}  -> {other.as_posix()}")
                    importers[other].add(mine)
                elif root_project and (root / target).is_dir():
                    here = next((c for c in code.values() if (root / c).is_dir()
                                 and (f == c or c in f.parents)), None)
                    if here is not None and here != target:
                        pkg_ties.append(f"{f.as_posix()}:{node.lineno}: {text}  -> {target.as_posix()}")
                        pkg_importers[target].add(here.name)

    # 5. Path hacks and PYTHONPATH.
    hacks, pythonpath = [], []
    for f, text in texts.items():
        for n, line in enumerate(text.splitlines(), 1):
            if f.suffix == ".py" and SYSPATH.search(line):
                hacks.append(f"{f.as_posix()}:{n}: {line.strip()}")
            if PYTHONPATH.search(line) and not line.lstrip().startswith("#"):
                pythonpath.append(f"{f.as_posix()}:{n}: {line.strip()}")

    # 6. Requirement files, path requirements, sources, workspaces.
    reqs = [f for f in all_files if f.name.startswith("requirements") and f.suffix in {".txt", ".in"}]
    req_users, req_paths = [], []
    for r in reqs:
        for n, line in enumerate(read(root, r).splitlines(), 1):
            if REQ_PATH.match(line):
                req_paths.append(f"{r.as_posix()}:{n}: {line.strip()}")
        for f, text in texts.items():
            if f == r or not (is_docker(f) or is_ci(f) or f.suffix in {".sh", ".ps1", ".toml"}):
                continue
            for n, line in enumerate(text.splitlines(), 1):
                if r.name in line:
                    req_users.append(f"{r.as_posix()} <- {f.as_posix()}:{n}: {line.strip()}")
    sources, workspaces, scripts = [], [], []
    for d, data in sorted(projects.items()):
        tool_uv = data.get("tool", {}).get("uv", {})
        ws = tool_uv.get("workspace")
        if ws is not None:
            workspaces.append(f"{(d / 'pyproject.toml').as_posix()}: members = {ws.get('members', [])}"
                              + (f", exclude = {ws['exclude']}" if ws.get("exclude") else ""))
        for name, src in (tool_uv.get("sources") or {}).items():
            if isinstance(src, dict) and ("path" in src or "workspace" in src):
                sources.append(f"{(d / 'pyproject.toml').as_posix()}: {name} = {src}")
        for name, target in (data.get("project", {}).get("scripts") or {}).items():
            scripts.append(f"{(d / 'pyproject.toml').as_posix()}: {name} = {target}")
    locks = [f.as_posix() for f in all_files if f.name in {"uv.lock", "poetry.lock", "pdm.lock",
                                                          "Pipfile.lock", "requirements.lock"}]
    others = [f.as_posix() for f in all_files if f.name in {"pants.toml", "BUILD", "BUILD.bazel",
                                                           "WORKSPACE", "MODULE.bazel", "nx.json"}]

    # 7. Copies: the same bytes in two units, and the same file name that differs.
    by_hash: dict[str, list[Path]] = defaultdict(list)
    by_name: dict[str, list[Path]] = defaultdict(list)
    for f in py:
        data = (root / f).read_bytes()
        if not data.strip():
            continue
        by_hash[hashlib.sha256(data).hexdigest()].append(f)
        if f.name not in GENERIC_NAMES and not f.name.startswith("test_"):
            by_name[f.name].append(f)
    copies, differs = [], []
    for digest, group in sorted(by_hash.items()):
        if len({unit_of(f) for f in group}) > 1:
            copies.append(" = ".join(f.as_posix() for f in group) + f"  (sha256 {digest[:12]})")
    for _name, group in sorted(by_name.items()):
        hashes = {hashlib.sha256((root / f).read_bytes()).hexdigest() for f in group}
        if len({unit_of(f) for f in group}) > 1 and len(hashes) > 1:
            differs.append(", ".join(f.as_posix() for f in group))

    # Report.
    print(f"repository: {root}")
    print(f"repository level: {', '.join(root_signs) or 'nothing'}"
          + ("; the root is a project" if root_project else ""))
    print("\nunits:")
    for u in units:
        s = signs.get(u, [])
        by = sorted(i.as_posix() for i in importers.get(u, ()))
        line = f"  {u.as_posix():<24} signs: {', '.join(s) or 'none'}"
        if by:
            line += f"; imported by {', '.join(by)}"
        print(line)
        for c in ci_lines.get(u, [])[:6]:
            print(f"  {'':<24} CI: {c}")
    if root_project:
        root_scripts = projects[Path(".")].get("project", {}).get("scripts") or {}
        deploy = {f: t for f, t in texts.items() if is_docker(f) or is_ci(f)}
        for name, where in sorted(code.items()):
            if not (root / where).is_dir() or unit_of(where) != Path("."):
                continue
            mine = [k for k, v in root_scripts.items() if v.split(":")[0].split(".")[0] == name.split(".")[0]]
            named = []
            for f, text in sorted(deploy.items()):
                for n, line in enumerate(text.splitlines(), 1):
                    if any(re.search(rf"(?<![\w-]){re.escape(w)}(?![\w-])", line) for w in [name, *mine]):
                        named.append(f"{f.as_posix()}:{n}")
            by = sorted(pkg_importers.get(where, ()))
            print(f"  root project package {name:<14} scripts: {', '.join(mine) or 'none'}; "
                  f"named in: {', '.join(named) or 'nothing'}"
                  + (f"; imported by {', '.join(by)}" if by else ""))
    orphans = [u for u in units if not signs.get(u) and not importers.get(u)]

    def section(title: str, rows: list[str]) -> None:
        print(f"\n{title}:" + ("" if rows else " none"))
        for r in rows:
            print(f"  {r}")

    section("imports across units", imports)
    if root_project:
        section("imports between top-level packages of the root project", pkg_ties)
    section("sys.path lines", hacks)
    section("PYTHONPATH settings", pythonpath)
    section("requirement files read by builds and CI", req_users)
    section("path requirements in requirement files", req_paths)
    section("path and workspace sources", sources)
    section("uv workspaces", workspaces)
    section("console scripts", scripts)
    section("lock files", locks)
    docker_rows = []
    for f, text in sorted(texts.items()):
        if is_docker(f):
            for n, line in enumerate(text.splitlines(), 1):
                if re.match(r"\s*(COPY|ADD|RUN|CMD|ENTRYPOINT|ENV|WORKDIR)\b", line):
                    docker_rows.append(f"{f.as_posix()}:{n}: {line.strip()}")
    section("Dockerfiles (what each copies, installs and runs)", docker_rows)
    section("other build tools", others)
    section("copies (same bytes in two units)", copies)
    section("same file name in two units, different content", differs)
    section("folders with code, no sign and no importer (ask: unit or dead code?)",
            [u.as_posix() for u in orphans])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
