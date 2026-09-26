# /// script
# requires-python = ">=3.10"
# ///
"""Sandbox rebase-sides. feature/late-fee is being rebased onto main and
stopped on a conflict in fees.py: the branch raised the fee, main added a
comment on the same line. Run once in an empty folder: uv run setup.py.
Builds repo/.
"""

import os
import pathlib
import subprocess

ROOT = pathlib.Path.cwd()
LAB = ROOT / ".lab"
DANA = ("Dana Levi", "dana@example.com")
OMER = ("Omer Katz", "omer@example.com")
_clock = [1772355600]  # fixed dates, so every run gives the same hashes


def git(*args, cwd="repo", who=DANA, check=True):
    """Run git in ROOT/cwd as `who`, never opening an editor."""
    _clock[0] += 60
    stamp = f"{_clock[0]} +0000"
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        GIT_AUTHOR_NAME=who[0], GIT_AUTHOR_EMAIL=who[1], GIT_AUTHOR_DATE=stamp,
        GIT_COMMITTER_NAME=who[0], GIT_COMMITTER_EMAIL=who[1],
        GIT_COMMITTER_DATE=stamp, GIT_EDITOR=":", GIT_TERMINAL_PROMPT="0",
    )
    base = ["git", "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false",
            "-c", "init.defaultBranch=main", "-c", "core.autocrlf=false"]
    done = subprocess.run(base + list(args), cwd=ROOT / cwd, env=env,
                          capture_output=True, text=True)
    if check and done.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{done.stderr}")
    return done.stdout.strip()


def write(path, text, cwd="repo", newline="\n"):
    p = ROOT / cwd / path
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline=newline) as f:
        f.write(text)


def commit(message, *paths, cwd="repo", who=DANA):
    git("add", "--", *(paths or ["."]), cwd=cwd)
    git("commit", "-q", "-m", message, cwd=cwd, who=who)


def new_repo(name="repo"):
    (ROOT / name).mkdir()
    git("init", "-q", cwd=name)


def new_origin():
    """A bare origin.git from repo, and repo tracking it."""
    git("init", "-q", "--bare", "origin.git", cwd=".")
    git("remote", "add", "origin", str(ROOT / "origin.git"))
    git("push", "-q", "-u", "origin", "--all")


def clone_colleague():
    git("clone", "-q", str(ROOT / "origin.git"), "colleague", cwd=".")


def finish(*clones):
    """Point each clone's editor at a recorder that logs the call and fails,
    so an editor opened during the task shows in .lab/editor-calls.log."""
    LAB.mkdir(exist_ok=True)
    rec = LAB / "record-editor.sh"
    rec.write_text(
        "#!/bin/sh\n"
        f"echo \"$*\" >> '{LAB.as_posix()}/editor-calls.log'\n"
        "echo 'record-editor: git opened an editor; failing so nothing waits' >&2\n"
        "exit 1\n", newline="\n")
    rec.chmod(0o755)
    for name in clones or ("repo",):
        git("config", "user.name", DANA[0], cwd=name)
        git("config", "user.email", DANA[1], cwd=name)
        git("config", "core.editor", f"sh '{rec.as_posix()}'", cwd=name)
        git("config", "sequence.editor", f"sh '{rec.as_posix()}'", cwd=name)
    script = ROOT / "setup.py"
    if script.exists():
        script.unlink()


INIT = "import sys, pathlib\nsys.path.insert(0, str(pathlib.Path(__file__).parents[1]))\n"


def main():
    new_repo()
    write(".gitignore", "__pycache__/\n")
    write("fees.py", "LATE_FEE = 5\nGRACE_DAYS = 3\n")
    commit("Add fee settings")
    git("switch", "-q", "-c", "feature/late-fee")
    write("fees.py", "LATE_FEE = 7\nGRACE_DAYS = 3\n")
    commit("Raise the late fee to 7 (FIN-88)")
    write("tests/__init__.py", "")
    write("tests/test_fees.py", INIT + "import unittest\nimport fees\n\n\n"
          "class Fees(unittest.TestCase):\n    def test_late_fee(self):\n"
          "        self.assertEqual(fees.LATE_FEE, 7)\n")
    commit("Test the late fee")
    git("switch", "-q", "main")
    write("fees.py", "LATE_FEE = 5  # EUR, charged once per invoice\nGRACE_DAYS = 3\n")
    commit("Document the fee unit", who=OMER)
    git("switch", "-q", "feature/late-fee")
    git("rebase", "main", check=False)
    finish()


if __name__ == "__main__":
    main()
