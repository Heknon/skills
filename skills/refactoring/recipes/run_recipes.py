"""Replay each recipe from the architecture shape's before to its after.

Usage, from this folder (its pyproject.toml pins what the shapes need):

    uv run python run_recipes.py                  # every recipe
    uv run python run_recipes.py L2 L5            # some
    uv run python run_recipes.py --harness <repo>/harness/seniority-checks/check_change.py
    uv run python run_recipes.py --keep <folder> L3   # keep the git repository

For each recipe file L<n>-*.md here:

1. Reads the architecture skill's shapes/L<n>-*.md (--shapes, default
   ../../architecture/shapes) and writes its before, with the shared test,
   into a new git repository, committed as the start.
2. Runs the baseline: pytest, ruff, mypy, import_all.py, public_names.py,
   and the OpenAPI document when app.main has an app.
3. Applies each step's ```diff block with git apply, runs the same checks,
   and commits with the step's `Commit:` subject. A step whose heading says
   "behaviour change" first applies only its test files and must see the
   tests fail, then applies the rest.
4. Compares the last tree with the shape's after, file by file.

A step is red when the tests fail or ruff or mypy report a code more often
than at the start, unless the step's text declares it on a line
"New finding: mypy `<code>`" (the recipe then says why it is a finding and
not a break). Lost public names, a changed OpenAPI document and the
change check's result are printed for the recipe's text to explain. Exit 0
when every step was green and every recipe ended at its after, else 1.
Standard library only; needs git on PATH. Lab: Python 3.12.14.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent / "tools"
SHAPE_BLOCK = re.compile(r"^```python file=(\S+)\n(.*?)^```", re.DOTALL | re.MULTILINE)
STEP = re.compile(
    r"^### (?P<title>.+?)\n(?P<text>.*?)^```diff\n(?P<diff>.*?)^```\n(?P<rest>.*?)(?=^##|\Z)",
    re.DOTALL | re.MULTILINE,
)
COMMIT = re.compile(r"^Commit: `(?P<subject>[^`]+)`", re.MULTILINE)
DECLARED = re.compile(
    r"^New finding: (?P<tool>ruff|mypy) `(?P<code>[\w-]+)`", re.MULTILINE
)
RUFF_SELECT = "E4,E7,E9,F,B,PLC0415,TRY002"
TESTS = ["--include=test_*", "--include=*/test_*"]
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "GIT_CONFIG_NOSYSTEM": "1"}


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, env=ENV, check=False
    )


def git(
    cwd: Path, *args: str, stdin: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.name=recipe", "-c", "user.email=recipe@example.com", *args],
        cwd=cwd,
        input=stdin,
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )


def shape_sides(md: Path) -> dict[str, dict[str, str]]:
    sides: dict[str, dict[str, str]] = {"before": {}, "after": {}}
    for path, code in SHAPE_BLOCK.findall(md.read_text(encoding="utf-8")):
        side, _, rest = path.partition("/")
        if side in sides:
            sides[side][rest] = code
        else:  # the shared test goes to both sides
            for files in sides.values():
                files[path] = code
    return sides


def last_line(text: str) -> str:
    lines = text.strip().splitlines()
    return lines[-1] if lines else ""


def tests(root: Path) -> tuple[bool, str]:
    proc = run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], root)
    return proc.returncode == 0, last_line(proc.stdout) or last_line(proc.stderr)


def ruff_codes(root: Path) -> Counter[str]:
    proc = run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--isolated",
            "--select",
            RUFF_SELECT,
            "--output-format",
            "json",
            "--no-cache",
            ".",
        ],
        root,
    )
    return Counter(item["code"] or "syntax" for item in json.loads(proc.stdout or "[]"))


def mypy_codes(root: Path, cache: Path) -> Counter[str]:
    proc = run(
        [
            sys.executable,
            "-m",
            "mypy",
            "app",
            "--cache-dir",
            str(cache),
            "--no-error-summary",
            "--show-error-codes",
            # a multi-file shape otherwise stops at "Source file found twice",
            # an error with no code, and is never type-checked
            "--explicit-package-bases",
        ],
        root,
    )
    codes = Counter(
        m.group(1)
        for m in re.finditer(r"error: .*\[([\w-]+)\]$", proc.stdout, re.MULTILINE)
    )
    # an error without a code, or a crash, means mypy did not check the tree:
    # count it, so a blocked run can never read as clean
    codes["uncoded"] += sum(
        1
        for line in proc.stdout.splitlines()
        if ": error:" in line and not re.search(r"\[[\w-]+\]$", line)
    )
    if proc.returncode not in (0, 1):
        codes["mypy-crash"] += 1
    return +codes


def modules(root: Path) -> list[str]:
    return sorted(
        ".".join(p.relative_to(root).with_suffix("").parts)
        for p in (root / "app").rglob("*.py")
        if p.name != "__init__.py"
    )


def public_names(root: Path) -> set[str]:
    proc = run([sys.executable, str(TOOLS / "public_names.py"), *modules(root)], root)
    return set(proc.stdout.splitlines())


def import_all(root: Path) -> str:
    return last_line(
        run([sys.executable, str(TOOLS / "import_all.py"), "app"], root).stdout
    ).removeprefix("import_all: ")


def openapi(root: Path) -> str | None:
    code = (
        "import json\nfrom app.main import app\n"
        "print(json.dumps(app.openapi(), sort_keys=True) if hasattr(app, 'openapi') else '')"
    )
    proc = run([sys.executable, "-c", code], root)
    return proc.stdout if proc.returncode == 0 and proc.stdout.strip() else None


def change_check(harness: Path | None, start: Path, root: Path) -> str:
    if harness is None:
        return ""
    proc = run(
        [sys.executable, str(harness.resolve()), "--before", str(start), "--after", str(root)],
        root,
    )
    if proc.returncode not in (0, 1):  # an argument error or a crash, not a finding
        tail = (proc.stderr or proc.stdout).strip().splitlines()[-1:] or ["no output"]
        return f"ERROR exit {proc.returncode}: {tail[0]}"
    fails = re.findall(r"^FAIL (\S+)", proc.stdout, re.MULTILINE)
    examples = [
        line.strip()[2:]
        for line in proc.stdout.splitlines()
        if line.strip().startswith("- ") and "files-changed" not in line
    ]
    head = "OK" if proc.returncode == 0 else "FAIL " + ", ".join(fails)
    detail = [
        e for e in examples if not e.endswith(".py") and " became the package " not in e
    ]
    return head + ("; " + "; ".join(detail) if detail and proc.returncode else "")


def diff_codes(now: Counter[str], base: Counter[str]) -> str:
    grown = [f"+{code}" for code in sorted(now) if now[code] > base.get(code, 0)]
    gone = [f"-{code}" for code in sorted(base) if now.get(code, 0) < base[code]]
    return " ".join(grown + gone) or "same"


def replay(recipe: Path, shape: Path, harness: Path | None, keep: Path | None) -> bool:
    sides = shape_sides(shape)
    steps = list(STEP.finditer(recipe.read_text(encoding="utf-8")))
    label = recipe.name.split("-")[0]
    with tempfile.TemporaryDirectory() as tmp:
        root = keep / label if keep else Path(tmp) / "repo"
        start, cache = Path(tmp) / "start", Path(tmp) / "mypy"
        if root.exists():
            shutil.rmtree(root)
        for rel, code in sides["before"].items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(code, encoding="utf-8")
        shutil.copytree(root, start)
        git(root, "init", "-q")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", f"Start from the architecture shape {label}")
        ok, summary = tests(root)
        base_ruff, base_mypy = ruff_codes(root), mypy_codes(root, cache)
        base_names, base_api = public_names(root), openapi(root)
        print(
            f"{label:4} start  tests {summary} | ruff {dict(base_ruff) or 'clean'} | "
            f"mypy {dict(base_mypy) or 'clean'} | import-all {import_all(root)}"
        )
        green = ok
        for number, step in enumerate(steps, 1):
            title, patch = step["title"], step["diff"]
            found = COMMIT.search(step["rest"])
            subject = found["subject"] if found else title
            if "behaviour change" in title:
                git(root, "apply", *TESTS, stdin=patch)
                failed, first = tests(root)
                print(
                    f"{label:4} {number}.     test first: {first}"
                    + ("" if not failed else "  (EXPECTED A FAILURE)")
                )
                green = green and not failed
                applied = git(
                    root,
                    "apply",
                    *[a.replace("include", "exclude") for a in TESTS],
                    stdin=patch,
                )
            else:
                applied = git(root, "apply", stdin=patch)
            if applied.returncode:
                print(
                    f"{label:4} {number}. {subject}\n      DOES NOT APPLY: {applied.stderr.strip()}"
                )
                return False
            ok, summary = tests(root)
            now_ruff, now_mypy = ruff_codes(root), mypy_codes(root, cache)
            declared = []
            for found in DECLARED.finditer(
                step["text"] + step["rest"]
            ):  # a finding the recipe explains
                now, base = (
                    (now_ruff, base_ruff)
                    if found["tool"] == "ruff"
                    else (now_mypy, base_mypy)
                )
                base[found["code"]] = now[found["code"]]
                declared.append(f"{found['tool']} {found['code']}")
            ruff, mypy = (
                diff_codes(now_ruff, base_ruff),
                diff_codes(now_mypy, base_mypy),
            )
            names = public_names(root)
            lost = sorted(line.split("  ")[0] for line in base_names - names)
            api = openapi(root)
            print(f"{label:4} {number}. {subject}")
            print(
                f"      tests {summary} | ruff {ruff} | mypy {mypy} | import-all {import_all(root)}"
                + (
                    f" | new finding, declared: {', '.join(declared)}"
                    if declared
                    else ""
                )
            )
            print(
                f"      names {'lost or changed ' + ', '.join(lost) if lost else 'none lost'}"
                + (
                    ""
                    if base_api is None
                    else f" | openapi {'same' if api == base_api else 'CHANGED'}"
                )
                + (
                    f" | change check {change_check(harness, start, root)}"
                    if harness
                    else ""
                )
            )
            green = green and ok and "+" not in ruff and "+" not in mypy
            git(root, "add", "-A")
            git(root, "commit", "-q", "-m", subject)
        wrong = [
            rel
            for rel, code in sides["after"].items()
            if not (root / rel).is_file()
            or (root / rel).read_text(encoding="utf-8") != code
        ]
        extra = [
            str(p.relative_to(root))
            for p in root.rglob("*.py")
            if str(p.relative_to(root)) not in sides["after"]
        ]
        same = not wrong and not extra
        print(
            f"{label:4} end    "
            + (
                f"identical to the shape's after ({len(sides['after'])} files)"
                if same
                else f"DIFFERS from the shape's after: {wrong + extra}"
            )
        )
        return green and same


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Replay recipes from a shape's before to its after."
    )
    parser.add_argument(
        "ids", nargs="*", metavar="ID", help="recipe IDs such as L2; all when none"
    )
    parser.add_argument(
        "--shapes",
        type=Path,
        default=HERE.parent.parent / "architecture" / "shapes",
        help="the architecture skill's shapes folder",
    )
    parser.add_argument(
        "--harness", type=Path, help="seniority's check_change.py, run after each step"
    )
    parser.add_argument(
        "--keep", type=Path, help="keep each recipe's git repository under this folder"
    )
    args = parser.parse_args(argv)
    if not args.shapes.is_dir():
        print(
            f"run_recipes: no shapes folder at {args.shapes}; pass --shapes",
            file=sys.stderr,
        )
        return 2
    recipes = sorted(HERE.glob("L*-*.md"), key=lambda p: int(p.name[1:].split("-")[0]))
    failed = 0
    for recipe in recipes:
        label = recipe.name.split("-")[0]
        if args.ids and label not in args.ids:
            continue
        shapes = list(args.shapes.glob(f"{label}-*.md"))
        if len(shapes) != 1:
            print(f"{label:4} no shape {label}-*.md in {args.shapes}")
            failed += 1
            continue
        failed += not replay(
            recipe, shapes[0], args.harness, args.keep.resolve() if args.keep else None
        )
    print(
        "run_recipes: "
        + ("all green" if not failed else f"{failed} recipe(s) not green")
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
