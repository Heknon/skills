# /// script
# requires-python = ">=3.10"
# ///
"""Sandbox bisect. 40 commits after tag v1.0; one changed the rounding
mode, and a run of commits in the middle cannot be imported. Run once in
an empty folder: uv run setup.py. Builds repo/.
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


GOOD = "ROUND_HALF_UP"
BAD = "ROUND_HALF_EVEN"


def money(mode, broken=False):
    head = "from shop.fmt import pad\n" if broken else ""
    return (head + "from decimal import Decimal, " + mode + "\n\n\n"
            "def to_cents(amount):\n"
            "    return Decimal(amount).quantize(Decimal('0.01'), rounding=" + mode + ")\n")


def main():
    new_repo()
    write(".gitignore", "__pycache__/\n")
    write("shop/__init__.py", "")
    write("shop/money.py", money(GOOD))
    write("CHANGELOG.md", "# Changes\n")
    commit("Add money helpers")
    git("tag", "-a", "v1.0", "-m", "Release 1.0")
    log = "# Changes\n"
    for n in range(1, 41):
        mode = BAD if n >= 29 else GOOD
        broken = 17 <= n <= 23
        write("shop/money.py", money(mode, broken))
        log += f"- change {n}\n"
        write("CHANGELOG.md", log)
        subject = {
            17: "Pad amounts in money helpers",
            24: "Add the fmt module",
            29: "Use the context rounding in to_cents",
        }.get(n, f"Update changelog ({n})")
        if n == 24:
            write("shop/fmt.py", "def pad(s, n):\n    return str(s).rjust(n)\n")
        commit(subject)
    finish()


if __name__ == "__main__":
    main()
