# /// script
# requires-python = ">=3.10"
# ///
"""Sandbox shared-rebase. feature/export is pushed; a colleague (Omer)
pushed a commit to it and to main; the person has one local commit and
has fetched. Run once in an empty folder: uv run setup.py. Builds repo/,
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


def main():
    new_repo()
    write("app/export.py", "def rows(data):\n    return [list(r) for r in data]\n")
    commit("Add export module")
    new_origin()
    git("switch", "-q", "-c", "feature/export")
    write("app/export.py", "def rows(data):\n    return [list(r) for r in data]\n\n\n"
          "def to_csv(data):\n    return \"\\n\".join(\",\".join(map(str, r)) for r in rows(data))\n")
    commit("Add CSV export")
    git("push", "-q", "-u", "origin", "feature/export")
    clone_colleague()
    git("switch", "-q", "feature/export", cwd="colleague")
    write("app/export.py", "def rows(data):\n    return [list(r) for r in data]\n\n\n"
          "def quote(v):\n    v = str(v)\n    return f'\"{v}\"' if \",\" in v else v\n\n\n"
          "def to_csv(data):\n    return \"\\n\".join(\",\".join(map(quote, r)) for r in rows(data))\n",
          cwd="colleague")
    commit("Quote CSV fields that contain commas", cwd="colleague", who=OMER)
    git("push", "-q", "origin", "feature/export", cwd="colleague")
    git("switch", "-q", "main", cwd="colleague")
    write("app/log.py", "import logging\n\nlog = logging.getLogger(\"app\")\n", cwd="colleague")
    commit("Add a module logger", cwd="colleague", who=OMER)
    git("push", "-q", "origin", "main", cwd="colleague")
    write("app/header.py", "def header(names):\n    return \",\".join(names)\n")
    commit("wip header")
    git("fetch", "-q", "origin")
    finish()


if __name__ == "__main__":
    main()
