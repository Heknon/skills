# Move function

Move a function (or class) from one module to another, keeping the old
import path working when anything outside may use it.

## Preconditions

- Every importer of the old path is listed (`core/every-reference.md`),
  including scripts outside the package, `pyproject.toml` entry points,
  config files and patch targets.
- You know what the function needs from its old module: private
  helpers, constants, imports. Those that only it uses move with it.
- The shim decision is made (`core/public-surface.md`).

## Mechanics

1. Copy the function, with the constants and private helpers only it
   uses, to the new module; add the imports it needs there.
2. At the old place, replace the definition with the explicit re-export:

   ```python
   from app.dates import parse_date as parse_date
   ```

   Keep the constants that moved importable the same way if they are
   public.
3. Change the importers in this repository to the new path: code, tests,
   scripts, patch targets (to the module where the name is now used).
4. Entry points in `pyproject.toml`: change them, or leave them on the
   shim. After changing one, reinstall before checking it (step 6).
5. Search again for the old path and the name.
6. Checks, with `import_all.py <package> --config pyproject.toml
   --config <other configs> --scripts <scripts folder>`. After an entry
   point edit, `uv sync` first: `uv run --no-sync` kept loading
   `app.helpers:parse_date` from the installed metadata until the project
   was reinstalled (lab, uv 0.8.17).
7. Commit: "Move parse_date to app.dates".

## Traps seen in the lab

| Trap | What happened |
| --- | --- |
| moved, callers in the package and tests changed, no shim | 7 passed, ruff clean; `tools/backfill.py` failed with `ImportError: cannot import name 'parse_date' from 'app.helpers'`, and the entry point with `AttributeError: module 'app.helpers' has no attribute 'parse_date'`. mypy saw the script only when `tools` was on its command line; `import_all.py` saw both |
| the shim written as `from app.dates import parse_date` | ruff `F401 [*] 'app.dates.parse_date' imported but unused`: `ruff check --fix` deletes it. `mypy --strict`: `Module "app.helpers" does not explicitly export attribute "parse_date"`. The `as parse_date` form passed both |
| the constant left behind: `dates.py` imports `DATE_FORMATS` from `helpers.py`, which imports `parse_date` from `dates.py` | `ImportError: cannot import name 'DATE_FORMATS' from partially initialized module 'app.helpers' (most likely due to a circular import)`, whichever module was imported first; ruff, mypy and pyright were silent. Move the constant with the function |
| the destination module is new, and the moved function gains an `except` on the way | seniority's change check does not compare new files, so it passes; only reading the diff shows it (`reference/change-check.md`). Move the body unchanged |

## Probe inputs

The function through the old import path and the new one, on its edge
inputs, and each entry point or config path that names it
(`importlib.metadata.entry_points(group=...)` and `ep.load()`).

**Done when:** the old path and the new one both import the same
object, every importer found works (import-all `0 failed`), and the
checks and probe are unchanged.
