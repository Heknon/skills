"""Make a repository with pre-commit installed and a staged fix.

Run once, before the eval, with the package index or mirror reachable:
    uv run --no-project python make_sandbox.py
"""

import pathlib
import shutil
import subprocess


def run(*cmd: str) -> None:
    subprocess.run(cmd, check=True)


run("git", "init", "-q", "-b", "main")
run("git", "config", "user.email", "dev@example.com")
run("git", "config", "user.name", "Dev")
run("uv", "lock", "-q")
run("uv", "sync", "-q")
fixed = pathlib.Path("fixed_totals.py.txt")
run("git", "add", "-A", ":!fixed_totals.py.txt", ":!make_sandbox.py")
run("git", "commit", "-q", "-m", "Add cart totals")
run("uv", "run", "--frozen", "pre-commit", "install")
shutil.move(fixed, "src/cart/totals.py")
run("git", "add", "src/cart/totals.py")
pathlib.Path("make_sandbox.py").unlink()
