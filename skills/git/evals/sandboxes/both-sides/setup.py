# /// script
# requires-python = ">=3.10"
# ///
"""Sandbox both-sides. A merge of main into feature/tax is in progress
and pricing.py conflicts: main rounds to cents, the branch adds a tax
rate. Each side has a test. Run once in an empty folder: uv run setup.py.
Builds repo/ and origin.git/.
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


BASE = '''def total(items, discount=0):
    """Sum price * quantity and take off the discount rate."""
    subtotal = sum(price * qty for price, qty in items)
    return subtotal - subtotal * discount
'''
MAIN = BASE.replace("    return subtotal - subtotal * discount",
                    "    return round(subtotal - subtotal * discount, 2)")
BRANCH = BASE.replace("def total(items, discount=0):", "def total(items, discount=0, tax=0):").replace(
    "    return subtotal - subtotal * discount",
    "    return (subtotal - subtotal * discount) * (1 + tax)")
INIT = "import sys, pathlib\nsys.path.insert(0, str(pathlib.Path(__file__).parents[1]))\n"


def main():
    new_repo()
    write(".gitignore", "__pycache__/\n")
    write("pricing.py", BASE)
    write("tests/__init__.py", "")
    write("tests/test_basic.py", INIT + "import unittest\nfrom pricing import total\n\n\n"
          "class Basic(unittest.TestCase):\n    def test_sum(self):\n"
          "        self.assertEqual(total([(2, 3)]), 6)\n")
    commit("Add order total")
    new_origin()
    git("switch", "-q", "-c", "feature/tax")
    write("pricing.py", BRANCH)
    write("tests/test_tax.py", INIT + "import unittest\nfrom pricing import total\n\n\n"
          "class Tax(unittest.TestCase):\n    def test_tax_added(self):\n"
          "        self.assertEqual(total([(19.99, 3)], discount=0.1, tax=0.17), 63.15)\n")
    commit("Add a tax rate to the order total")
    git("switch", "-q", "main")
    write("pricing.py", MAIN)
    write("tests/test_rounding.py", INIT + "import unittest\nfrom pricing import total\n\n\n"
          "class Rounding(unittest.TestCase):\n    def test_cents(self):\n"
          "        self.assertEqual(total([(19.99, 3)], discount=0.1), 53.97)\n")
    commit("Round order totals to cents", who=OMER)
    git("push", "-q", "origin", "main", "feature/tax")
    git("switch", "-q", "feature/tax")
    git("merge", "main", check=False)
    finish()


if __name__ == "__main__":
    main()
