# Checker tables for pyproject.toml

`pyproject-tables.toml` is a complete `pyproject.toml` for a sample
project; copy the `[tool.ruff*]`, `[tool.mypy*]`, `[tool.pydantic-mypy]`
and `[tool.pyright]` tables into a real one. `[project]` and the dev
group are the packaging skill's; they are here so the file runs.

| Table | Choices made, and why |
| --- | --- |
| `[tool.ruff]` | `required-version` refuses another ruff; `select` pinned (`ruff/rules.md`); `S101` allowed in tests; the project's package as first-party |
| `[tool.mypy]` | strict for all, `files` so CI and people check the same paths, the pydantic plugin, codeless ignores reported, and legacy modules relaxed by an override (never `strict` in an override: `mypy/strictness.md`) |
| `[tool.pydantic-mypy]` | typed `__init__`, no extra arguments (`mypy/pydantic.md`) |
| `[tool.pyright]` | the same paths, standard mode, and the project's `.venv` wherever pyright starts |

A project normally runs one type checker in CI. Keep both tables only
if both run; otherwise delete the other.

## Checked (*lab*, Python 3.12, a model, a legacy module, one test)

```
$ uv run --no-sync ruff check .
All checks passed!
$ uv run --no-sync ruff format --check .
5 files already formatted
$ uv run --no-sync mypy
Success: no issues found in 5 source files
$ uv run --no-sync pytest -q
1 passed in 0.14s
$ uv run --no-sync pyright
  src/app/models.py:12:12 - error: Argument missing for parameter "displayName" (reportCallIssue)
  src/app/models.py:12:29 - error: No parameter named "display_name" (reportCallIssue)
2 errors, 0 warnings, 0 informations
```

The two pyright errors are the known disagreement: the model has
`validate_by_name=True`, which mypy understands through the plugin and
pyright does not (`mypy/pydantic.md`). The legacy module with untyped
functions passed both checkers.
