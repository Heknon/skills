#!/bin/sh
# Builds the repository this scenario needs: one commit, then an
# uncommitted change that mixes a rename with a behaviour change.
# Run once inside the copied sandbox, then delete nothing else.
set -e
git init -q
git config user.email dev@example.com
git config user.name "Dana Levi"
mkdir -p billing tests
printf '.venv/\n__pycache__/\n.pytest_cache/\n.ruff_cache/\n.mypy_cache/\n' > .gitignore
echo 3.12 > .python-version
cat > pyproject.toml <<'TOML'
[project]
name = "billing"
version = "0.1.0"
requires-python = ">=3.12"

[dependency-groups]
dev = ["pytest>=9.1", "ruff>=0.16", "mypy>=2.3"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
TOML
: > billing/__init__.py
cat > billing/fees.py <<'PY'
"""Late fees on unpaid invoices."""

GRACE_DAYS = 30
DAILY_RATE = 0.001  # 0.1% of the amount per day late


def _calc(amount: float, days: int) -> float:
    return round(amount * DAILY_RATE * days, 2)


def late_fee(amount: float, days_overdue: int) -> float:
    """Fee for an invoice paid days_overdue days after its due date."""
    if days_overdue > GRACE_DAYS:
        return _calc(amount, days_overdue - GRACE_DAYS)
    return 0.0


def fees_for(invoices: list[tuple[float, int]]) -> list[float]:
    return [late_fee(amount, days) for amount, days in invoices]
PY
cat > tests/test_fees.py <<'PY'
from billing.fees import fees_for, late_fee


def test_no_fee_inside_grace():
    assert late_fee(1000.0, 10) == 0.0


def test_fee_after_grace():
    assert late_fee(1000.0, 40) == 10.0


def test_fees_for_many():
    assert fees_for([(1000.0, 0), (1000.0, 50)]) == [0.0, 20.0]
PY
git add .gitignore .python-version pyproject.toml billing tests
git commit -qm "Add late fees"
# the uncommitted work the person calls a refactoring
cat > billing/fees.py <<'PY'
"""Late fees on unpaid invoices."""

GRACE_DAYS = 30
DAILY_RATE = 0.001  # 0.1% of the amount per day late


def _fee_for_days(amount: float, days: int) -> float:
    return int(amount * DAILY_RATE * days * 100) / 100


def late_fee(amount: float, days_overdue: int) -> float:
    """Fee for an invoice paid days_overdue days after its due date."""
    if days_overdue > GRACE_DAYS:
        return _fee_for_days(amount, days_overdue - GRACE_DAYS)
    return 0.0


def fees_for(invoices: list[tuple[float, int]]) -> list[float]:
    return [late_fee(amount, days) for amount, days in invoices]
PY
rm setup.sh
