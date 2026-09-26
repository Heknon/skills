"""List what a wheel or sdist holds: its metadata, entry points and files.

Standard library only (tested on Python 3.12 and 3.11). Changes nothing.

    uv run --no-project python inspect_dist.py dist/acme_report-1.2.0-py3-none-any.whl
    uv run --no-project python inspect_dist.py dist/acme_report-1.2.0.tar.gz
    uv run --no-project python inspect_dist.py "dist/*.whl" --against src/acme_report

--against DIR compares the files of one package folder in the source tree
with the distribution and lists each source file the distribution lacks
(compiled files and __pycache__ are ignored). Run it from the project
root. Exit code: 0 when nothing is missing, 1 when a file is missing or
the wheel holds no Python module, 2 on a usage error.
"""

from __future__ import annotations

import argparse
import glob
import sys
import tarfile
import zipfile
from email.parser import HeaderParser
from pathlib import Path, PurePosixPath

SHOWN = ("Metadata-Version", "Name", "Version", "Requires-Python",
         "Requires-Dist", "Provides-Extra", "License-Expression",
         "Dynamic")
IGNORED_SUFFIXES = (".pyc", ".pyo")


def read_dist(path: Path) -> tuple[str, list[str], str, str, str]:
    """Return (kind, member names, METADATA or PKG-INFO, entry points, WHEEL)."""
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]

            def text(suffix: str) -> str:
                found = next((n for n in names if n.endswith(".dist-info/" + suffix)), None)
                return zf.read(found).decode() if found else ""

            return "wheel", names, text("METADATA"), text("entry_points.txt"), text("WHEEL")
    if path.name.endswith(".tar.gz"):
        with tarfile.open(path) as tf:
            members = [m for m in tf.getmembers() if m.isfile()]
            names = [m.name for m in members]
            pkg_info = next((m for m in members
                             if PurePosixPath(m.name).parts[1:] == ("PKG-INFO",)), None)
            meta_text = tf.extractfile(pkg_info).read().decode() if pkg_info else ""
        return "sdist", names, meta_text, "", ""
    raise SystemExit(f"error: not a wheel (.whl) or sdist (.tar.gz): {path}")


def source_prefix(folder: Path, kind: str) -> str:
    """Where the files of a source package folder sit inside the distribution."""
    rel = Path(folder)
    if kind == "sdist":
        return rel.as_posix().strip("/") + "/"
    parts = rel.parts
    # In a wheel, paths start at the import root: below src/ when there is one.
    if "src" in parts:
        parts = parts[parts.index("src") + 1:]
    return PurePosixPath(*parts).as_posix() + "/" if parts else ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dist", nargs="+", type=Path, help="wheel or sdist files")
    parser.add_argument("--against", type=Path, metavar="DIR",
                        help="a package folder in the source tree to compare with")
    args = parser.parse_args()
    status = 0
    paths: list[Path] = []
    for given in args.dist:
        # PowerShell passes dist\*.whl to programs unexpanded: expand it here.
        matches = sorted(glob.glob(str(given))) if any(c in str(given) for c in "*?[") else []
        if matches:
            paths.extend(Path(m) for m in matches)
        else:
            paths.append(given)
    for path in paths:
        if not path.is_file():
            print(f"error: no such file: {path}", file=sys.stderr)
            return 2
        kind, names, meta_text, eps_text, wheel_text = read_dist(path)
        print(f"== {path.name} ({kind}, {len(names)} files)")
        headers = HeaderParser().parsestr(meta_text)
        print("metadata:")
        for key in SHOWN:
            for value in headers.get_all(key) or []:
                print(f"  {key}: {value}")
        if kind == "wheel":
            generator = HeaderParser().parsestr(wheel_text).get("Generator", "unknown")
            print(f"built by: {generator}")
            print("entry points:")
            print("  " + ("\n  ".join(eps_text.strip().splitlines()) if eps_text.strip() else "none"))
        print("files:")
        for name in names:
            print(f"  {name}")
        if kind == "sdist":
            inner = ["/".join(PurePosixPath(n).parts[1:]) for n in names]
        else:
            inner = names
        if kind == "wheel" and not any(n.endswith(".py") for n in names):
            if any(n.endswith(".pth") for n in names):
                print("note: no .py files, only a .pth file: an editable wheel")
            else:
                print("PROBLEM: the wheel holds no Python module")
                status = 1
        if args.against:
            folder = args.against
            if not folder.is_dir():
                print(f"error: no such folder: {folder}", file=sys.stderr)
                return 2
            prefix = source_prefix(folder, kind)
            wanted = sorted(
                prefix + p.relative_to(folder).as_posix()
                for p in folder.rglob("*")
                if p.is_file() and "__pycache__" not in p.parts
                and not p.name.endswith(IGNORED_SUFFIXES)
            )
            missing = [w for w in wanted if w not in set(inner)]
            print(f"against {folder.as_posix()} ({len(wanted)} files, as {prefix or '/'}):")
            if missing:
                status = 1
                for m in missing:
                    print(f"  MISSING {m}")
            else:
                print("  every source file is in the distribution")
    return status


if __name__ == "__main__":
    sys.exit(main())
