"""Look things up in the installed environment, with no web.

Run it with the project's interpreter, from the project folder:

    uv run --no-sync python <skill>/recipes/lookup.py <command> ...

Commands (only `def` imports the module it is asked about):

    pin DIST              interpreter, version, location, installer, editable
                          or copy, and where each import name loads from
    where IMPORT          the file `import IMPORT` would load
    grep IMPORT REGEX     search one installed package's .py and .pyi files
                          and its METADATA (add -i to ignore case); prints
                          path:line: text
    lines PATH START [END]
                          print lines START to END of a file, numbered
    def DOTTED            IMPORTS the module, then prints the signature, the
                          file and line of the definition, and whether it is
                          wrapped or compiled
    wheel FILE [MEMBER]   list a .whl, .zip or .tar.gz without installing it,
                          or print one member (a path, or a name such as
                          METADATA, RECORD or CHANGELOG.md)
    diff OLD NEW          unified diff of two files, folders or archives

Standard library only. Verified on CPython 3.12.14.
"""

import difflib
import importlib.metadata as md
import importlib.util
import inspect
import json
import os
import platform
import re
import sys
import tarfile
import zipfile
from pathlib import Path

TEXT = {".py", ".pyi", ".txt", ".md", ".rst", ".toml", ".cfg", ".ini", ".json", ""}
COMPILED = (".so", ".pyd")


def _print(*parts):
    print(*parts, flush=True)


def _spec(name):
    try:
        return importlib.util.find_spec(name)
    except (ImportError, ValueError) as exc:
        _print(f"find_spec({name!r}) failed: {type(exc).__name__}: {exc}")
        return None


def _import_names(dist):
    names = [n for n, ds in md.packages_distributions().items() if dist.metadata["Name"] in ds]
    if not names:
        top = dist.read_text("top_level.txt")
        names = top.split() if top else []
    if not names:
        names = [dist.metadata["Name"].replace("-", "_").lower()]
    return sorted(n for n in names if not n.startswith("_") and "." not in n and "-" not in n)


def cmd_pin(args):
    name = args[0]
    _print(f"python:    {platform.python_version()} at {sys.executable}")
    try:
        dist = md.distribution(name)
    except md.PackageNotFoundError:
        _print(f"not installed: no distribution named {name!r} for this interpreter")
        names = sorted({d.metadata["Name"] for d in md.distributions() if d.metadata["Name"]})
        want = re.sub(r"[-_.]+", "", name).lower()
        near = [n for n in names if want in re.sub(r"[-_.]+", "", n).lower()]
        near += [n for n in difflib.get_close_matches(name, names, n=3) if n not in near]
        _print("similar:  ", ", ".join(near) if near else "none")
        return 1
    _print(f"dist:      {dist.metadata['Name']} {dist.version}")
    _print(f"location:  {dist.locate_file('')}")
    installer = (dist.read_text("INSTALLER") or "not recorded").strip()
    _print(f"installer: {installer}")
    direct = dist.read_text("direct_url.json")
    if direct:
        info = json.loads(direct)
        if info.get("dir_info", {}).get("editable"):
            _print(f"install:   editable, from {info['url']}")
        else:
            _print(f"install:   from {info['url']} (a copy)")
    else:
        _print("install:   a copy from an index (no direct_url.json)")
    for imp in _import_names(dist):
        spec = _spec(imp)
        if spec is None or spec.origin is None:
            _print(f"import:    {imp} -> not importable by that name")
            continue
        origin = Path(spec.origin)
        kind = "compiled" if origin.suffix in COMPILED else "source"
        if kind == "compiled" and (origin.parent / (origin.name.split(".")[0] + ".py")).exists():
            kind = "compiled; its .py source is beside it"
        _print(f"import:    {imp} -> {origin} ({kind})")
        folder = origin.parent
        if spec.submodule_search_locations:
            binaries = [p for p in folder.rglob("*") if p.suffix in COMPILED]
            if binaries:
                _print(f"compiled:  {len(binaries)} file(s) in the package, such as {binaries[0].name}")
        if (folder / "py.typed").exists():
            _print(f"typed:     {imp} ships py.typed")
        for entry in sys.path:
            ext = Path(entry or ".") / f"{imp}-stubs"
            if ext.is_dir():
                _print(f"stubs:     separate stub package at {ext}")
    pyi = [str(f) for f in dist.files or [] if f.suffix == ".pyi"]
    if pyi:
        _print(f"pyi:       {len(pyi)} stub file(s) in this distribution, such as {pyi[0]}")
    return 0


def cmd_where(args):
    spec = _spec(args[0])
    if spec is None:
        _print(f"not found: {args[0]}")
        return 1
    _print(f"origin:    {spec.origin}")
    if spec.submodule_search_locations:
        _print(f"package:   {', '.join(spec.submodule_search_locations)}")
    if "." in args[0]:
        _print("note:      the parent packages were imported to find this")
    return 0


def _package_files(name):
    spec = _spec(name)
    if spec is None:
        return None, []
    if spec.submodule_search_locations:
        roots = [Path(p) for p in spec.submodule_search_locations]
    else:
        roots = [Path(spec.origin)]
    files = []
    for root in roots:
        if root.is_file():
            files.append(root)
            continue
        for path in sorted(root.rglob("*")):
            if path.suffix in (".py", ".pyi") and "__pycache__" not in path.parts:
                files.append(path)
    top = name.split(".")[0]
    for dist_name in md.packages_distributions().get(top, []):
        dist = md.distribution(dist_name)
        for f in dist.files or []:
            if f.name == "METADATA" and f.parent.name.endswith(".dist-info"):
                files.append(Path(dist.locate_file(f)))
    return roots, files


def cmd_grep(args):
    flags = re.IGNORECASE if "-i" in args else 0
    args = [a for a in args if a != "-i"]
    name, pattern = args[0], re.compile(args[1], flags)
    roots, files = _package_files(name)
    if roots is None:
        _print(f"not found: {name}")
        return 1
    hits = 0
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                hits += 1
                _print(f"{path}:{number}: {line.strip()}")
    where = ", ".join(str(r) for r in roots)
    if any(p.name == "METADATA" for p in files):
        where += " and its METADATA"
    if hits:
        _print(f"{hits} match(es) for /{pattern.pattern}/ in {len(files)} file(s) under {where}")
    else:
        _print(f"no match for /{pattern.pattern}/ in {len(files)} file(s) under {where}")
    return 0


def cmd_lines(args):
    path, start = Path(args[0]), int(args[1])
    end = int(args[2]) if len(args) > 2 else start + 30
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for number in range(start, min(end, len(lines)) + 1):
        _print(f"{number:5}  {lines[number - 1]}")
    return 0


def _resolve(dotted):
    parts = dotted.split(".")
    for cut in range(len(parts), 0, -1):
        modname = ".".join(parts[:cut])
        try:
            obj = __import__(modname, fromlist=["_"])
        except ImportError:
            continue
        for attr in parts[cut:]:
            obj = getattr(obj, attr)
        return modname, obj
    raise ImportError(f"no importable module in {dotted!r}")


def cmd_def(args):
    modname, obj = _resolve(args[0])
    _print(f"imported:  {modname} (its top-level code ran)")
    _print(f"object:    {type(obj).__module__}.{type(obj).__qualname__}")
    try:
        _print(f"signature: {inspect.signature(obj)}")
    except (ValueError, TypeError) as exc:
        _print(f"signature: none ({type(exc).__name__}: {exc})")
    if hasattr(obj, "__wrapped__"):
        _print(f"wrapper:   {inspect.signature(obj, follow_wrapped=False)} "
               "(decorated; the line above is the wrapped function's)")
    try:
        path = inspect.getsourcefile(obj)
        first = inspect.getsourcelines(obj)[1]
        _print(f"source:    {path}:{first}")
    except (TypeError, OSError) as exc:
        code = getattr(obj, "__code__", None)
        if code is not None:
            where = code.co_filename
            for entry in sys.path:
                candidate = Path(entry or ".") / where
                if candidate.is_file():
                    where = str(candidate)
                    break
            _print(f"source:    none from inspect ({type(exc).__name__}); "
                   f"compiled from {where}:{code.co_firstlineno}")
        else:
            _print(f"source:    none ({type(exc).__name__}: {exc}); read a stub or the docstring")
    module = sys.modules.get(getattr(obj, "__module__", "") or "")
    if module is not None and getattr(module, "__file__", None):
        _print(f"module:    {module.__name__} at {module.__file__}")
    doc = inspect.getdoc(obj)
    _print(f"doc:       {doc.splitlines()[0] if doc else 'none'}")
    return 0


def _members(path):
    path = Path(path)
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            return {i.filename: i for i in z.infolist() if not i.is_dir()}, "zip"
    with tarfile.open(path) as t:
        return {m.name: m for m in t.getmembers() if m.isfile()}, "tar"


def _read_member(path, name, kind):
    if kind == "zip":
        with zipfile.ZipFile(path) as z:
            return z.read(name).decode("utf-8", errors="replace")
    with tarfile.open(path) as t:
        return t.extractfile(name).read().decode("utf-8", errors="replace")


def cmd_wheel(args):
    members, kind = _members(args[0])
    if len(args) == 1:
        for name, info in members.items():
            size = info.file_size if kind == "zip" else info.size
            _print(f"{size:9}  {name}")
        return 0
    want = args[1]
    matches = [n for n in members if n == want or n.endswith("/" + want)]
    if not matches:
        _print(f"no member {want!r} in {args[0]}")
        return 1
    for name in matches:
        _print(f"--- {name}")
        _print(_read_member(args[0], name, kind))
    return 0


def _snapshot(path):
    path = Path(path)
    if path.is_file() and (zipfile.is_zipfile(path) or tarfile.is_tarfile(path)):
        members, kind = _members(path)
        out = {}
        for name in members:
            key = name.split("/", 1)[1] if kind == "tar" and "/" in name else name
            key = re.sub(r"-[^/-]+\.dist-info/", ".dist-info/", key)
            if key.endswith(".dist-info/RECORD"):
                continue
            if Path(key).suffix in TEXT:
                out[key] = _read_member(path, name, kind)
        return out
    if path.is_file():
        return {path.name: path.read_text(encoding="utf-8", errors="replace")}
    return {
        str(p.relative_to(path)).replace(os.sep, "/"): p.read_text(encoding="utf-8", errors="replace")
        for p in sorted(path.rglob("*"))
        if p.is_file() and p.suffix in TEXT and "__pycache__" not in p.parts
    }


def cmd_diff(args):
    old, new = _snapshot(args[0]), _snapshot(args[1])
    if len(old) == 1 and len(new) == 1:
        pairs = [(next(iter(old)), next(iter(new)))]
    else:
        pairs = [(k, k) for k in sorted(set(old) | set(new))]
    changed = 0
    for a, b in pairs:
        if a not in old:
            _print(f"only in {args[1]}: {b}")
            changed += 1
            continue
        if b not in new:
            _print(f"only in {args[0]}: {a}")
            changed += 1
            continue
        diff = list(difflib.unified_diff(old[a].splitlines(), new[b].splitlines(),
                                         f"old/{a}", f"new/{b}", lineterm=""))
        if diff:
            changed += 1
            for line in diff:
                _print(line)
    _print(f"{changed} file(s) differ" if changed else "no difference in text files")
    return 0


COMMANDS = {"pin": (cmd_pin, 1), "where": (cmd_where, 1), "grep": (cmd_grep, 2),
            "lines": (cmd_lines, 2), "def": (cmd_def, 1), "wheel": (cmd_wheel, 1),
            "diff": (cmd_diff, 2)}


def main(argv):
    # A script's own folder is first on sys.path; put the current folder
    # there instead, as `python -c` does, so project packages resolve.
    sys.path[0] = os.getcwd()
    if not argv or argv[0] not in COMMANDS:
        _print(__doc__)
        return 2
    func, needed = COMMANDS[argv[0]]
    if len([a for a in argv[1:] if a != "-i"]) < needed:
        _print(__doc__)
        return 2
    return func(argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
