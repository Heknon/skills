# Run the checks the way CI runs them

**Verdict you produce:** the commands CI runs, the versions on both
sides, and the output of the same commands here.

```
ci runs:   uv run --no-sync ruff check .   (from .gitlab-ci.yml, job lint)
versions:  ruff 0.16.9 in uv.lock, 0.16.9 here (uv run), 0.16.9 in the CI log
config:    ruff read pyproject.toml (Settings path)
result:    <the summary line, such as "All checks passed!" or "Found 2 errors.">
```

## 1. Find what CI runs

Read the CI file (`.gitlab-ci.yml` and what it includes; the deployment
skill maps includes and components). Copy each checker command exactly:
the paths (`.` or `src tests`), the flags, and the steps before it
(`uv sync --locked`). A job log shows the same, and also the versions
it installed:

```
$ uv sync --locked
 + ruff==0.15.8
$ uv run --no-sync ruff check .
```

## 2. Compare versions before changing anything

| Where | Command (PowerShell) |
| --- | --- |
| the lock | `uv tree --frozen --only-group dev --depth 1` or `Select-String -Path uv.lock -Pattern '^name = "ruff"' -Context 0,1` |
| the project environment | `uv run --no-sync ruff --version`, `uv run --no-sync mypy --version`, `uv run --no-sync pyright --version` |
| whatever is on `PATH` | `Get-Command ruff` then `ruff --version` |
| CI | the `+ ruff==...` line of `uv sync` in the job log |

All four printed offline in the lab. When they differ, the lock and CI
decide. `uv sync --locked` makes `.venv` match the lock; it changes
nothing else.

*Lab, ruff 0.15.8 on `PATH`, 0.16.9 in the lock:* a bare `ruff check`
and `uv run --no-sync ruff check` gave different findings on the same
code. The version matters more than it looks: with no `select` in the
config, ruff 0.15.8 enabled 59 rules and 0.16.9 enabled 413
(`ruff/rules.md`).

## 3. Make sure the environment is the lock's

`uv run --no-sync` does not install anything. In a checkout whose
`.venv` is missing or empty (a new clone or `git worktree`), it created
an empty `.venv` and then ran the first `ruff` on `PATH`, a global one
of another version, with no warning (*lab, uv 0.12.19*). Two ways to
notice or avoid it:

```
uv run --no-sync python -m ruff --version   # "No module named ruff" when the env lacks it
uv run --frozen ruff --version              # installs the lock's version if missing
```

`uv run --frozen` also put back the locked ruff after someone had
installed another version into `.venv` by hand. It needs the packages
in uv's cache or the mirror. In a uv workspace add `--all-packages`,
or the members are not installed (`pre-commit/monorepo.md`).

## 4. Check the config each tool read

The same command reads a different file when two exist, or when it is
run from another folder. Ask the tool (`core/config-files.md`):

```
uv run --no-sync ruff check --show-settings src/app/core.py   # "Settings path: ..."
uv run --no-sync mypy -v src 2>&1 | Select-String "Config File"
uv run --no-sync pyright --verbose | Select-String "configuration|pyproject"
```

mypy picks its config by the current folder, not by the files checked,
so run it from the folder CI runs it from.

## 5. Run the same command and read the summary

| Tool | Clean | Findings | Broken run |
| --- | --- | --- | --- |
| `ruff check` | `All checks passed!`, exit 0 | `Found N errors.`, exit 1 | `ruff failed`, exit 2 (an unknown code in `--select`) |
| `ruff format --check` | `N files already formatted`, exit 0 | `N files would be reformatted`, exit 1 | |
| `mypy` | `Success: no issues found in N source files`, exit 0 | `Found N errors in M files (checked K source files)`, exit 1 | exit 2 (`Cannot read file`) |
| `pyright` | `0 errors, 0 warnings, 0 informations`, exit 0 | `N errors, ...`, exit 1; warnings alone exit 0 unless `--warnings` | exit 1 with a config message (an unknown `typeCheckingMode`) |

mypy checks for the Python version it runs under unless `python_version`
is set; uv picked Python 3.14 in the lab when `requires-python = ">=3.12"`
and no `.python-version` pinned it. Compare the interpreter too:
`uv run --no-sync python --version`.

## Never

- Never "fix" findings that only another version reports. Show the
  versions, fix what CI reports, and offer an upgrade as its own change.
- Never trust a green run from a global tool, `uvx ruff`, or Zed's
  panel as CI's verdict (`core/zed.md`).
