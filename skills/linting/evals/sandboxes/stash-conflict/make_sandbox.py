"""Make a repository where a staged file also has unstaged edits.

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
run("git", "commit", "-q", "-m", "Add cart totals")
run("uv", "run", "--frozen", "pre-commit", "install")
path = pathlib.Path("src/cart/totals.py")
# The staged version: a new function, not formatted as ruff would.
path.write_text(
    path.read_text()
    + "\n\ndef average_line(lines: list[tuple[int,int]])->float:\n"
    "    return cart_total(lines)/len(lines)\n"
)
run("git", "add", str(path))
# A further edit in the same file, not staged.
path.write_text(path.read_text() + "\n\n# TODO: handle an empty cart in average_line\n")
pathlib.Path("make_sandbox.py").unlink()
