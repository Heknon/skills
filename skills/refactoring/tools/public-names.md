# public_names.py

**What it decides:** whether every name a module offered before a step,
with the same signature, is still importable from it after the step.

```powershell
uv run --no-sync python <skill>/tools/public_names.py app.reports | Out-File -Encoding utf8 .ledger/names-before.txt
# after each step:
uv run --no-sync python <skill>/tools/public_names.py app.reports | Out-File -Encoding utf8 .ledger/names-after.txt
git diff --no-index .ledger/names-before.txt .ledger/names-after.txt
```

One line per public name of the module (no leading underscore), sorted,
whether or not it is in `__all__`:

```
app.reports.CENT  value  Decimal('0.01')
app.reports.Decimal  imported  from decimal
app.reports.Order  class  (number: str, customer: str, lines: list[Line] = <factory>, currency: str = 'EUR', tax_rate: Decimal = Decimal('0.20')) -> None
app.reports.csv  module
app.reports.format_money  function  (amount: Decimal, currency: str = 'EUR') -> str
```

Public methods of the module's own classes get a line each. Classes and
functions from outside the module's top-level package are one
`imported` line each, without a signature. Module prefixes are dropped
from signatures (`Decimal`, not `decimal.Decimal`), so moving a class
does not change the lines that mention it. `--path src` adds a folder
to `sys.path`. Exit 1 when a module cannot be imported. Standard library
only; lab: Python 3.12.14.

## Reading the difference

| Line | Means | Do |
| --- | --- | --- |
| `+` only | a new name, such as a new submodule (`+app.reports.money  module`) | nothing |
| `-` for your own function, class or value | callers lose it | red: re-export it (`core/public-surface.md`) |
| `-` then `+` with another signature | a parameter, default or annotation changed | red, unless the step is a signature change asked for |
| `-` for an `imported` or `module` line | a name the module only imported (`Decimal`, `csv`) is gone | explain it under *References*; re-export it only if someone imports it from here (search first) |

In the lab, after moving the money section out of `app/reports.py`,
this showed `-app.reports.CENT  value  Decimal('0.01')`: a public
constant outside `__all__` that the move dropped while the tests, ruff
and mypy were green.
