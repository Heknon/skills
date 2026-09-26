# Worked example: a move with a shim

Kind: Step (move function). Outputs from a lab run on Python 3.12.14,
pytest 9.1.1, ruff 0.16.9, mypy 2.3.1, uv 0.8.17, git 2.43.0, commands
run in PowerShell 7.5 on Linux.

## The ask

> Move parse_date from app/helpers.py into app/dates.py, where it belongs.

## Steps

1. **Before you start.** Baseline: `7 passed`, ruff `All checks
   passed!`, mypy on `src tests tools` `Success: no issues found in 8
   source files`, `import_all: 8 ok, 0 failed, 0 skipped`. The package
   is installed (`[build-system]`) and declares an entry point, so
   outside code can reach `app.helpers`: a shim is needed
   (`core/public-surface.md`). The probe calls `parse_date` on six
   inputs, three of which raise, and loads the entry point:

   ```
   parse_date '' ValueError unknown date format: ''
   parse_date '2026-02-30' ValueError unknown date format: '2026-02-30'
   entry point date 2026-03-01
   ```

2. **Every reference.** `git grep -n -w -I parse_date`, `git grep -n -w
   -I DATE_FORMATS`, and the module path
   (`git grep -n -I -e 'app\.helpers' -e 'app/helpers'`):

   | Hit | Decision |
   | --- | --- |
   | `src/app/helpers.py:8` the definition, `:5` and `:11` `DATE_FORMATS` | move both; `DATE_FORMATS` is used only by `parse_date` |
   | `src/app/importer.py:6` import | edit to `app.dates` |
   | `tests/test_helpers.py:5` import | edit to `app.dates` |
   | `tools/backfill.py:5` import, a script no test runs | edit to `app.dates` |
   | `pyproject.toml:10` `date = "app.helpers:parse_date"`, an entry point no test runs | edit, then reinstall |

3. **Move** the constant and the function to `app/dates.py`, with
   `datetime` added to its import, and leave the explicit re-export:

   ```python
   """Small helpers shared by the importers."""

   # moved to app.dates; kept importable from here for code outside this repository
   from app.dates import DATE_FORMATS as DATE_FORMATS
   from app.dates import parse_date as parse_date
   ```

   Moving `DATE_FORMATS` too matters: in an earlier run it stayed in
   `helpers.py`, `dates.py` imported it from there, and both modules
   failed to import (`cannot import name 'DATE_FORMATS' from partially
   initialized module 'app.helpers' (most likely due to a circular
   import)`) while ruff, mypy and pyright were silent.
4. **Edit the importers**, the script and the entry point.
5. **Search again**: `app.helpers` is left only in the two imports of
   `slug`, which did not move.
6. **Checks**:

   ```
   7 passed in 0.02s
   All checks passed!
   Success: no issues found in 8 source files
   ```

   `mypy --strict src` also passed: the `as` form counts as an explicit
   re-export. `ruff check --fix --diff src` printed nothing, so a later
   `--fix` will not delete the shim (a plain import would be `F401 [*]`).

   The entry point, before and after reinstalling:

   ```powershell
   uv run --no-sync python -c 'from importlib.metadata import entry_points; print([ep.value for ep in entry_points(group="app.parsers")])'
   ['app.helpers:parse_date']
   uv sync -q
   ['app.dates:parse_date']
   ```

   Then import-all over the package, `pyproject.toml` and `tools`:

   ```
   OK   pyproject.toml: app.dates:parse_date
   OK   tools/backfill.py
   import_all: 8 ok, 0 failed, 0 skipped
   ```

   Probe: `probe diff exit: 0`. Public names: `app.dates` gained
   `DATE_FORMATS` and `parse_date`; `app.helpers` lost only `date` and
   `datetime`, imported from the standard library.
7. **Commit**: `22d9e0a Move parse_date and DATE_FORMATS to app.dates`,
   6 files, with the body "Structure only. app.helpers re-exports both
   for code outside this repository; the app.parsers entry point now
   names app.dates."

## The answer

```
## Steps
1. move function: parse_date and DATE_FORMATS from app.helpers to app.dates,
   re-exported from app.helpers. 22d9e0a. pytest 7 passed; ruff All checks
   passed!; mypy Success (8 files, and --strict on src); import_all 8 ok,
   0 failed (entry point and tools/backfill.py included); probe identical.

## References
Edited: src/app/importer.py:6, tests/test_helpers.py:5, tools/backfill.py:5,
pyproject.toml:10 (entry point; reinstalled with uv sync).
Left: the two imports of slug from app.helpers (slug did not move).

## Behaviour
Tests 7 passed before and after; probe identical (six inputs, three errors,
the entry point); public names: nothing of the project's own lost.

## Findings
tests/test_helpers.py now tests app.dates.parse_date; moving those tests to
a test_dates.py is a separate tidy, not done.
```
