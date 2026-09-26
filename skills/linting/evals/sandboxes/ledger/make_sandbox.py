"""Write the 29 other ledger modules, all left unformatted on purpose.

Run once, before the eval: uv run --no-project python make_sandbox.py
"""

import pathlib

NAMES = (
    "accounts audit balances batches budget calendar cashflow categories "
    "clients currency discounts exports fees imports journal ledgers limits "
    "notes payments periods refunds reminders reports rounding schedules "
    "suppliers taxes transfers vendors"
).split()

for name in NAMES:
    pathlib.Path(f"src/ledger/{name}.py").write_text(
        f"def {name}_count( items ):\n"
        f"    return len( items )\n"
        f"def {name}_label(name,prefix = '{name}'):\n"
        f"    return prefix+':'+name\n"
    )
pathlib.Path("make_sandbox.py").unlink()
