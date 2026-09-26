"""Eval setup: make this folder a git repository holding the project as it is.

Run once in the copied sandbox, then delete this file:
    uv run --no-project python setup.py
"""
import pathlib
import subprocess


def git(*args):
    subprocess.run(["git", *args], check=True, capture_output=True, cwd=here)


here = pathlib.Path(__file__).parent
git("init", "-q", "-b", "main")
git("config", "user.name", "Dev")
git("config", "user.email", "dev@example.com")
(here / ".gitignore").write_text(".venv/\n__pycache__/\n.pytest_cache/\nsetup.py\n", encoding="utf-8")
git("add", "-A")
git("commit", "-q", "-m", "Add the stock value report")
