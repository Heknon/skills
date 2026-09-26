"""Make a repository whose hooks live in .githooks (core.hooksPath).

Run once, before the eval, with the package index or mirror reachable:
    uv run --no-project python make_sandbox.py
"""

import pathlib
import subprocess


def run(*cmd: str) -> None:
    subprocess.run(cmd, check=True)


run("git", "init", "-q", "-b", "main")
run("git", "config", "user.email", "dev@example.com")
run("git", "config", "user.name", "Dev")
run("git", "config", "core.hooksPath", ".githooks")
run("uv", "lock", "-q")
run("uv", "sync", "-q")
run("git", "add", "-A", ":!make_sandbox.py")
run("git", "commit", "-q", "-m", "Start notify")
pathlib.Path("make_sandbox.py").unlink()
