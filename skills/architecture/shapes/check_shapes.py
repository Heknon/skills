"""Run every shape's test against its before and its after code.

    uv run python check_shapes.py            # all shapes
    uv run python check_shapes.py L5 L8      # some

A shape file (L1-*.md ...) holds fenced blocks whose info string is
`python file=<path>`. Paths starting with before/ or after/ go to that
side; test_*.py at the top goes to both; after-only tests are written as
after/test_*.py. Exit status 1 if any side fails.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
BLOCK = re.compile(r"^```python file=(\S+)\n(.*?)^```", re.S | re.M)


def split(md: Path) -> dict[str, dict[str, str]]:
    sides: dict[str, dict[str, str]] = {"before": {}, "after": {}}
    for path, code in BLOCK.findall(md.read_text(encoding="utf-8")):
        side, _, rest = path.partition("/")
        if side in sides:
            sides[side][rest] = code
        else:  # a shared test
            for files in sides.values():
                files[path] = code
    return sides


def run_side(files: dict[str, str], root: Path) -> tuple[int, str]:
    for rel, code in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(code, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    lines = proc.stdout.strip().splitlines()
    return proc.returncode, lines[-1] if lines else proc.stderr.strip()[-200:]


def main(ids: list[str]) -> int:
    failed = runs = 0
    for md in sorted(HERE.glob("L*-*.md"), key=lambda p: int(p.name[1:].split("-")[0])):
        shape_id = md.name.split("-")[0]
        if ids and shape_id not in ids:
            continue
        with tempfile.TemporaryDirectory() as tmp:
            for side, files in split(md).items():
                code, summary = run_side(files, Path(tmp) / side)
                failed += code != 0
                runs += 1
                print(f"{shape_id:4} {side:6} {summary}")
    print(f"check_shapes: {runs - failed} of {runs} sides passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
