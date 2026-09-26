# Offline pre-commit hooks for a uv workspace

`.pre-commit-config.yaml` here is the only hook config of a workspace
with members `services/api`, `services/worker` and `packages/common`.
Why each part is there: `pre-commit/monorepo.md`.

## Needs

The root `pyproject.toml` has the workspace and the dev group with
`ruff`, `mypy` and `pre-commit`; `services/api/pyproject.toml` has its
own `[tool.mypy]` (`strict = true`). No member has a
`.pre-commit-config.yaml`; delete any that exist.

## Change

The member paths in `files`, `--config-file` and the mypy paths. One
mypy hook per member that has its own settings or should be checked on
its own; one ruff hook for all.

## Checked

*Lab:* pre-commit 4.6.2, uv 0.12.19, network cut off, `.venv`
deleted first.

```
$ uv run --frozen pre-commit validate-config        # no output, exit 0
$ uv run --frozen pre-commit run --all-files
Using CPython 3.12.14
Creating virtual environment at: .venv
Installed 17 packages in 30ms
ruff check...............................................................Passed
ruff format..............................................................Passed
mypy (services/api, strict)..............................................Failed
- hook id: mypy-api
- exit code: 1

services/api/src/api/__init__.py:8: error: Function is missing a type annotation  [no-untyped-def]
Found 1 error in 1 file (checked 1 source file)

mypy (services/worker)...................................................Passed
mypy (packages/common)...................................................Passed
```

The api failure is a real finding in the sample (`def parse_qty(raw)`
under strict). With only a worker file staged, `mypy-api` printed
`(no files to check)Skipped`.
