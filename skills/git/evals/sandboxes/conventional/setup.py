# /// script
# requires-python = ">=3.10"
# ///
"""Sandbox conventional. The repository uses Conventional Commits,
enforced by commitlint; the person's rounding fix is uncommitted. Run
once in an empty folder: uv run setup.py. Builds repo/ and origin.git/.
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


HISTORY = [
    ("feat(cart): add cart totals", "cart/totals.py"),
    ("fix(cart): keep empty carts at zero", "cart/totals.py"),
    ("feat(pricing): add percentage discounts", "pricing/discount.py"),
    ("docs: describe discount tiers", "README.md"),
    ("chore(deps): pin requests to 2.32", "requirements.txt"),
    ("fix(pricing): reject negative discount rates", "pricing/discount.py"),
    ("refactor(cart): split totals into helpers", "cart/totals.py"),
    ("test(pricing): cover the zero rate", "pricing/discount.py"),
]


def main():
    new_repo()
    write("commitlint.config.js", "module.exports = { extends: ['@commitlint/config-conventional'] };\n")
    write(".gitignore", "__pycache__/\n")
    commit("chore: add commitlint")
    for n, (subject, path) in enumerate(HISTORY):
        (ROOT / "repo" / path).parent.mkdir(parents=True, exist_ok=True)
        with open(ROOT / "repo" / path, "a", newline="\n") as f:
            f.write(f"# {n}\n")
        commit(subject)
    write("pricing/discount.py", "from decimal import Decimal, ROUND_HALF_UP\n\n\n"
          "def apply(amount, rate):\n    value = Decimal(amount) * (1 - Decimal(rate))\n"
          "    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)\n")
    commit("feat(pricing): return discounted amounts as Decimal")
    new_origin()
    write("pricing/discount.py", "from decimal import Decimal, ROUND_HALF_UP\n\n\n"
          "def apply(amount, rate):\n    value = Decimal(str(amount)) * (1 - Decimal(str(rate)))\n"
          "    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)\n")
    finish()


if __name__ == "__main__":
    main()
