"""Make a git repository with pre-commit installed.

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
run("uv", "lock", "-q")
run("uv", "sync", "-q")
run("git", "add", "-A", ":!make_sandbox.py")
run("git", "commit", "-q", "-m", "SHOP-1 Start the shop API")
run("uv", "run", "--frozen", "pre-commit", "install")
pathlib.Path("make_sandbox.py").unlink()
