"""Turn this folder into a git repository with one commit.

Run once, before the eval: uv run --no-project python make_sandbox.py
"""

import subprocess

for cmd in (
    ["git", "init", "-q", "-b", "main"],
    ["git", "config", "user.email", "dev@example.com"],
    ["git", "config", "user.name", "Dev"],
    ["git", "add", "-A"],
    ["git", "commit", "-q", "-m", "Start inventory"],
):
    subprocess.run(cmd, check=True)
