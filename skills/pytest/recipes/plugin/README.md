# pytest-budget: an installable plugin with pytester tests

A complete plugin that reports tests whose call phase takes longer than
a time budget. It shows each part a plugin usually needs:

| Part | Where in `src/pytest_budget/plugin.py` |
| --- | --- |
| entry point, so installing it loads it | `pyproject.toml`: `[project.entry-points.pytest11] budget = "pytest_budget.plugin"` |
| command-line options in their own `--help` group | `pytest_addoption`: `--budget-ms`, `--budget-strict` |
| configuration-file key as the default | `parser.addini("budget_ms", ...)`, read with `config.getini` |
| a registered marker | `pytest_configure`: `config.addinivalue_line("markers", ...)`; read with `item.get_closest_marker("budget")` |
| a fixture | `budget` |
| a new-style wrapper that reads and changes reports | `pytest_runtest_makereport` with `@pytest.hookimpl(wrapper=True)` |
| run state in the stash | `over_budget_key = pytest.StashKey[...]()` |
| a terminal summary section | `pytest_terminal_summary` |

## Run it (PowerShell or POSIX)

```
cd recipes/plugin
uv sync                                        # installs pytest and the plugin itself, editable
uv run pytest                                  # 12 passed
uv run --with "pytest==8.4.2" pytest           # 12 passed
uv run pytest --runpytest=subprocess           # 12 passed, inner runs in subprocesses
```

Plugin disabled, every test must fail:

```
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"; uv run pytest; Remove-Item Env:PYTEST_DISABLE_PLUGIN_AUTOLOAD
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest     # POSIX
```

*lab:* `12 failed` on 9.1.1 and 8.4.2. `pytester` is enabled with `-p
pytester` in `addopts`, so it still loads.

## Checked (*lab*)

- 12 passed on pytest 9.1.1 and 8.4.2 (pluggy 1.6.0), in process and
  with `--runpytest=subprocess`.
- 12 failed with the plugin disabled. The first version had three tests
  that only checked that a line was absent; they passed with the plugin
  disabled and were fixed by also asserting outcomes that need the
  plugin.
- `test_xfail_tests_are_left_alone` failed when the `wasxfail` check was
  removed from the wrapper, and passes with it.

## Limitation: pytest-xdist

*lab:* with `-n 2`, `--budget-strict` still fails slow tests (the
changed report is sent to the controller), but the "over budget"
section is empty: the stash is filled in the worker processes and the
summary runs in the controller. To support xdist, collect the entries
in `pytest_runtest_logreport(report)`, which runs in the controller for
every report, and carry the duration and budget on the report
(`report.user_properties`).

## Use it as a template

Rename the package, the entry point name and the options; keep the
tests' shape: for each behaviour, a generated test file, a run, a check
of outcomes and of the lines a user sees. Delete `.venv`, `uv.lock` and
`.pytest_cache` if they were created by trying it out.
