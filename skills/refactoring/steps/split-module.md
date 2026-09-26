# Split a module

Turn a long module into a package of smaller modules, keeping every old
import working. Worked in the lab on a 129-line `app/reports.py` with
five sections, imported by the web layer, a CLI, a script, tests and
(per its README) other teams.

## Preconditions

- The baseline and the public names of the module are recorded
  (`core/before-you-start.md`, `tools/public_names.py app.reports`).
  In the lab the names showed `CENT`, public but not in `__all__`.
- The importers and patch targets are listed (`core/every-reference.md`).
  In the lab: two `mock.patch("app.reports.now")` in the tests.
- The sections are known: which functions go together, and which
  private helpers each uses.

## Mechanics

1. **Module to package**, one step, nothing else:

   ```powershell
   mkdir app/reports
   git mv app/reports.py app/reports/__init__.py
   ```

   `git status --short`: `R  app/reports.py -> app/reports/__init__.py`.
   Checks (5 passed), commit: "Turn app.reports into a package".
2. **One section per step.** Move its definitions to a new submodule
   (`app/reports/money.py`), and import them back into `__init__.py` in
   the import block at the top:

   ```python
   from app.reports.money import CENT as CENT, CURRENCY_SYMBOLS, format_money
   ```

   Names in `__all__` need no `as`; public names outside it do, or ruff
   reports `F401` for them in `__init__.py`. Remove the imports
   `__init__.py` no longer uses (ruff `F401` lists them). Checks, public
   names compared, commit: "Move money formatting to app.reports.money".
3. **Submodules import from their siblings**, never from the package:
   `from app.reports.money import format_money` in `text.py`, not
   `from app.reports import format_money`.
4. **Patch targets move with the name** they patch, in the same step:
   `mock.patch("app.reports.now")` becomes
   `mock.patch("app.reports.clock.now")` when `now` and its caller move
   to `clock.py`.
5. Repeat until `__init__.py` holds only the docstring, the imports and
   `__all__`.

## Traps seen in the lab

| Trap | What happened |
| --- | --- |
| a public name outside `__all__` | after the money step, `from app.reports import CENT` failed with `ImportError: cannot import name 'CENT'`; tests, ruff and mypy were green; the public-names comparison showed the line `app.reports.CENT  value  Decimal('0.01')` gone |
| the clock moved, patch targets not | 2 tests failed with the real time in the header: `mock.patch("app.reports.now")` replaced the package's name, and `stamp_header` in `clock.py` used its own. The step was undone and redone with the patch targets (`examples/red-step-undone.md`) |
| `text.py` imported from `app.reports` while `__init__.py` imported `text` first | `ImportError: cannot import name 'Order' from partially initialized module 'app.reports' (most likely due to a circular import)` in every importer; with the import last it worked, so it hangs on import order. ruff, mypy and pyright said nothing; `import_all.py` failed |
| names only imported into the old module (`Decimal`, `Path`, `csv`, `dataclass`) | they vanished from `app.reports`; `public_names.py` lists them as `imported` or `module`. Explain them; nobody should import `Decimal` from `app.reports` |

At the end of the six steps: 5 passed at every commit (checked with
`git rebase --exec`, `core/step-loop.md`), import-all `10 ok, 0 failed`,
and seniority's change check `OK` on the whole split.

## Probe inputs

Every public name imported through `app.reports` (write them in the
probe as `from app.reports import ...`), and each function's edge
inputs.

**Done when:** every old import works, the public-names comparison
lost only imported names, and the checks were green at every commit.
