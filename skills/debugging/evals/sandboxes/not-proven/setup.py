"""Eval setup: make this folder a git repository with the bug and its "fix".

Run once in the copied sandbox, then delete this file:
    uv run python setup.py
"""
import pathlib
import subprocess

OLD_TOTAL = '''def line_total(quantity, unit_price):
    """Price of one invoice line, rounded to the cent."""
    return round(quantity * unit_price, 2)
'''
OLD_TEST = '''from billing.total import line_total


def test_line_total():
    assert line_total(3, 1.25) == 3.75
'''


def git(*args):
    subprocess.run(["git", *args], check=True, capture_output=True)


here = pathlib.Path(__file__).parent
new_total = (here / "billing" / "total.py").read_text(encoding="utf-8")
new_test = (here / "tests" / "test_total.py").read_text(encoding="utf-8")
git("init", "-q", "-b", "main")
git("config", "user.name", "Dev")
git("config", "user.email", "dev@example.com")
(here / ".gitignore").write_text(".venv/\n__pycache__/\n.pytest_cache/\nsetup.py\n", encoding="utf-8")
(here / "billing" / "total.py").write_text(OLD_TOTAL, encoding="utf-8")
(here / "tests" / "test_total.py").write_text(OLD_TEST, encoding="utf-8")
git("add", "-A")
git("commit", "-q", "-m", "Add invoice line totals")
(here / "billing" / "total.py").write_text(new_total, encoding="utf-8")
(here / "tests" / "test_total.py").write_text(new_test, encoding="utf-8")
git("add", "-A")
git("commit", "-q", "-m", "Fix BUG-88: round half cents up")
