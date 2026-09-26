# /// script
# requires-python = ">=3.10"
# ///
"""Sandbox undo-pushed. main is pushed and holds a merge of
feature/fast-tax that broke the totals, and a later commit by a
colleague. Run once in an empty folder: uv run setup.py. Builds repo/,
origin.git/ and colleague/.
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
    write("totals.py", "from decimal import Decimal\n\n\ndef with_tax(net, rate):\n"
          "    return (Decimal(net) * (1 + Decimal(rate))).quantize(Decimal('0.01'))\n")
    write("tests/__init__.py", "")
    write("tests/test_totals.py", INIT + "import unittest\nfrom totals import with_tax\n\n\n"
          "class Totals(unittest.TestCase):\n    def test_tax(self):\n"
          "        self.assertEqual(str(with_tax('10', '0.2')), '12.00')\n")
    commit("Add totals with tax")
    new_origin()
    clone_colleague()
    git("switch", "-q", "-c", "feature/fast-tax", cwd="colleague")
    write("totals.py", "def with_tax(net, rate):\n    return round(float(net) * (1 + float(rate)), 2)\n", cwd="colleague")
    commit("Compute tax with floats for speed", cwd="colleague", who=OMER)
    write("bench.py", "import timeit\nfrom totals import with_tax\nprint(timeit.timeit(lambda: with_tax('10', '0.2')))\n", cwd="colleague")
    commit("Add a tax benchmark", cwd="colleague", who=OMER)
    git("switch", "-q", "main", cwd="colleague")
    git("merge", "-q", "--no-ff", "--no-edit", "feature/fast-tax", cwd="colleague", who=OMER)
    write("receipt.py", "def line(amount):\n    return f'EUR {amount}'\n", cwd="colleague")
    commit("Add currency to receipt lines", cwd="colleague", who=OMER)
    git("push", "-q", "origin", "main", "feature/fast-tax", cwd="colleague")
    git("pull", "-q", "--ff-only")
    finish()


if __name__ == "__main__":
    main()
