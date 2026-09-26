"""Writes the 38 job modules of this sandbox (called by make_repo.py).

python generate.py base <work>       jobs log through `log`
python generate.py change-1 <work>   the same jobs, renamed to `logger`
                                     (used only to write change-1.patch)
"""

import sys
from pathlib import Path

TEMPLATE = '''"""Nightly job {n:02d}."""

import logging

{name} = logging.getLogger(__name__)


def run_{n:02d}(items: list[int]) -> int:
    {name}.info("job {n:02d}: %d items", len(items))
    return len(items)
'''


def main() -> None:
    step, work = sys.argv[1], Path(sys.argv[2])
    name = "log" if step == "base" else "logger"
    jobs = work / "src" / "shop" / "jobs"
    jobs.mkdir(parents=True, exist_ok=True)
    (jobs / "__init__.py").write_text("", encoding="utf-8")
    for n in range(1, 39):
        text = TEMPLATE.format(n=n, name=name)
        (jobs / f"job_{n:02d}.py").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
