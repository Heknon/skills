"""Turn one sandbox folder into a git repository with a change to review.

Usage (any OS, Python 3.10 or later, git on PATH):
    python make_repo.py <sandbox folder> <new work folder>

What it builds:
- branch main: every file of the sandbox except the change files, one commit;
- branch feature, checked out: one commit per change-<n>.patch, in order;
  the text above the patch's first `diff --git` line is the message.
A generate.py in the sandbox writes files for the first commit
(`generate.py base <work>`); the patches hold every change.
Files under notes/ and incoming/ are copied but never committed (the
earlier review, a patch to review): git status shows them as untracked.
"""

import shutil
import subprocess
import sys
from pathlib import Path

SKIP_NAMES = {".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


def git(work: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=work, check=True)


def is_change_file(path: Path) -> bool:
    return path.name.startswith("change-") and path.suffix == ".patch"


def message(patch: Path) -> str:
    text = patch.read_text(encoding="utf-8")
    head = text[: text.index("diff --git")]
    return head.rsplit("---", 1)[0].strip() + "\n"


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    sandbox, work = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    if work.exists() and any(work.iterdir()):
        print(f"{work} exists and is not empty")
        return 2
    work.mkdir(parents=True, exist_ok=True)
    for src in sandbox.rglob("*"):
        rel = src.relative_to(sandbox)
        if SKIP_NAMES & set(rel.parts) or is_change_file(src) or rel.name == "generate.py":
            continue
        dst = work / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    generator = sandbox / "generate.py"

    git(work, "init", "-q", "-b", "main")
    git(work, "config", "user.name", "Sandbox Author")
    git(work, "config", "user.email", "author@example.com")
    git(work, "config", "core.autocrlf", "false")
    exclude = work / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    exclude.write_text("notes/\nincoming/\nuv.lock\n.venv/\n__pycache__/\n*_cache/\n", encoding="utf-8")
    if generator.exists():
        subprocess.run([sys.executable, str(generator), "base", str(work)], check=True)
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "Initial service")
    patches = sorted(sandbox.glob("change-*.patch"))
    if patches:
        git(work, "switch", "-q", "-c", "feature")
    for patch in patches:
        git(work, "apply", "--index", str(patch))
        git(work, "add", "-A")
        git(work, "commit", "-q", "-m", message(patch))
    subprocess.run(["git", "log", "--oneline", "--all", "--graph"], cwd=work, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
