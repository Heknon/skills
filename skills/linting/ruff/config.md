# ruff configuration

**What it decides:** where a ruff setting goes and how to prove ruff
read it. Which file wins is in `core/config-files.md`. Verified on ruff
0.16.9.

## The same settings in the two file forms

```toml
# pyproject.toml                         # ruff.toml (or .ruff.toml)
[tool.ruff]                              line-length = 100
line-length = 100                        extend-exclude = ["migrations"]
extend-exclude = ["migrations"]
                                         [lint]
[tool.ruff.lint]                         select = ["E", "F", "B", "S"]
select = ["E", "F", "B", "S"]            ignore = ["E501"]
ignore = ["E501"]
                                         [lint.per-file-ignores]
[tool.ruff.lint.per-file-ignores]        "tests/**" = ["S101"]
"tests/**" = ["S101"]
                                         [format]
[tool.ruff.format]                       quote-style = "double"
quote-style = "double"
```

Top level: files and shared settings (`line-length`, `target-version`,
`exclude`, `extend-exclude`, `src`, `extend`, `required-version`).
`lint`: rules and their options. `format`: the formatter. `ruff config`
lists the keys at each level; `ruff config lint` lists the lint ones.

## Keys used most

| Key | Does (from `ruff config <key>`, and the lab) |
| --- | --- |
| `extend = "../pyproject.toml"` | start from another config file, then apply this one; the only way a nested config inherits |
| `lint.per-file-ignores` | `{"<glob>" = ["<codes>"]}`; a leading `!` negates the pattern; `extend-per-file-ignores` adds to the parent's |
| `extend-exclude` | files and folders to skip, on top of the defaults (`.git`, `.venv`, `.mypy_cache` and others) |
| `force-exclude` (or `--force-exclude`) | apply the excludes even to files named on the command line; pre-commit names files, so its ruff hooks pass it. *Lab:* `ruff check migrations/m1.py` reported the file; with `--force-exclude` it said `No Python files found` |
| `src` | where first-party code lives, for import sorting; default the project folder and `src` |
| `target-version` | the oldest Python to support; taken from `requires-python` when not set |
| `required-version = ">=0.16.9"` | refuse to run on another version: `ruff failed` / ``Required version `>=0.17` does not match the running version `0.16.9` ``, exit 2 |

`required-version` is a cheap guard against the wrong-version problem
(`core/run-like-ci.md`), if the team wants one.

## Per-file ignores for tests

The usual request: tests may `assert`.

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]
```

Put it in the file ruff reads (*lab:* the same table in `pyproject.toml`
did nothing while a `ruff.toml` existed). Prove it:
`uv run --no-sync ruff check --show-settings tests/test_status.py` lists
it under `linter.per_file_ignores` as `assert (S101)`, and `ruff check`
passes.

## One-off overrides

`--config "line-length = 100"` overrides one key for one run and beats
every file. PowerShell passes the inner single quotes through:

```powershell
uv run --no-sync ruff check --config "lint.per-file-ignores = {'tests/**' = ['S101']}" .
```

(*lab, PowerShell 7.4 on Linux*: `All checks passed!`). Use it to try
a setting, then write it into the file.

## A uv workspace

Each member's `pyproject.toml` with a `[tool.ruff]` table is that
member's config, and it replaces the root one for its files. *Lab:* a
member with `select = ["E"]` stopped reporting the root's `F401` for its
files. Members without a `[tool.ruff]` table use the root's. Use
`extend = "../../pyproject.toml"` in a member that should inherit.
