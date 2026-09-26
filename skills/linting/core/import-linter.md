# Run import-linter where the project has contracts

**Verdict you produce:** whether the project's layer contracts hold,
from the tool the project locks.

```
config:    [tool.importlinter] in pyproject.toml | .importlinter | setup.cfg
version:   import-linter <version> in uv.lock (uv tree --frozen --only-group dev --depth 1)
command:   uv run --frozen lint-imports --no-logo
result:    Contracts: <n> kept, <m> broken.   (exit 0 | 1)
broken:    <contract name>: <module> is not allowed to import <module> (l.<line>)
verdict import-linter: <kept | broken: <contracts> | not run: <why>>
```

Verified on import-linter 2.15 (with grimp 3.17), Python 3.12, uv
0.12.19. The rules themselves (which layer may import which) are the
architecture skill's (`skills/architecture/core/layers.md`); its
recipes carry optional contracts in
`skills/architecture/recipes/beanie_service/pyproject.toml` and
`skills/architecture/recipes/sqlalchemy_service/pyproject.toml`. This
file only runs the tool and reads what it says.

## Steps

1. **Does the project use it?** Look for `[tool.importlinter]` in
   `pyproject.toml`, or an `[importlinter]` section in `.importlinter`
   or `setup.cfg` (the files `lint-imports` reads, from its source,
   `adapters/user_options.py`), and for `import-linter` in the dev
   group or `lint-imports` in `.pre-commit-config.yaml` and the CI file.
   None of them: it is not the project's tool. Never add it unasked; a
   layering question then goes to the architecture skill's searches.
2. **Run it from the project's top folder**, with the locked version:
   ```
   uv run --frozen lint-imports --no-logo
   ```
   It reads its config from the current folder only: *lab,* from `app\`
   it printed `Could not read any configuration.` It puts the current
   folder on `sys.path` (`cli.py`), so a package at the top level is
   found without being installed.
3. **Read the summary.** *lab,* the architecture skill's Beanie recipe:
   ```
   Layers inside a feature point one way KEPT
   The service knows no HTTP and no database KEPT

   Contracts: 2 kept, 0 broken.
   ```
   exit 0. With `from fastapi import HTTPException` added to the
   service, exit 1 and:
   ```
   Contracts: 1 kept, 1 broken.
   ...
   app.accounts.service is not allowed to import fastapi:

   -   app.accounts.service -> fastapi (l.1)
   ```
   Each broken contract names the importing module, the imported one
   and the line.
4. **Fix the import, not the contract.** A broken contract is a
   finding like any other (`core/decide.md`): move the code to the
   layer that may import it (the architecture skill says where).
   Changing `layers`, adding an `ignore_imports` entry or deleting a
   contract to make the run pass is a change of the rules, which the
   person decides.

## What goes wrong

| Output | Cause | Fix |
| --- | --- | --- |
| `Could not read any configuration.` | run from a subfolder, or no `[tool.importlinter]` table | run from the folder that holds the config |
| `Could not find package 'shop' in your Python path.` | a `src` layout whose package is not installed (`[tool.uv] package = false`) | the project installs itself (`package = true` and a `[build-system]`, the packaging skill's); then `uv sync` and run again |
| `Could not find contract 'layers'.` with `--contract layers` | `--contract` takes a contract's `id`, and a `[[tool.importlinter.contracts]]` entry has none unless it sets `id = "layers"` | run all contracts, or give the entry an `id` |
| ``error: Failed to spawn: `lint-imports` `` (exit 2) | not in the project's environment | not the project's tool (step 1); air gapped, nothing is installed to run it |

All four ran in the lab.

## As a pre-commit hook

A local hook, like the others in `pre-commit/catalogue.md`:

```yaml
- repo: local
  hooks:
    - id: lint-imports
      name: import-linter
      entry: uv run --frozen lint-imports --no-logo
      language: system
      pass_filenames: false
      types: [python]
```

`pass_filenames: false` because it checks the whole package, not the
staged files. *Lab* (pre-commit 4.6.2): a commit that made the service
import `fastapi` was refused with the broken contract above, exit 1.

`lint-imports` writes a cache to `.import_linter_cache/` (its default,
`configuration.py`; `--no-cache` turns it off). Keep that folder in
`.gitignore`.
