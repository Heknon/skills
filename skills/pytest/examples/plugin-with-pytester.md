# Worked example: a plugin, written and tested with pytester

Kinds: Plugin, Pytester. The result is `recipes/plugin/`; the outputs are
from the lab, on pytest 9.1.1 and 8.4.2 with pluggy 1.6.0.

## The ask

> We want a pytest plugin that tells us which tests are slower than a
> budget, set on the command line or in pyproject, overridable per test,
> and optionally failing them. Several repositories will use it.

## Steps

1. **Where it goes** (`core/write-plugin.md`): several repositories, so
   an installable package with a `pytest11` entry point, not a conftest.
2. **Read the versions**: `pytest 9.1.1`, `pluggy 1.6.0`; CI of one
   consumer still runs 8.4.2, so the plugin must work on both
   (`internals/versions.md`): `[tool.pytest.ini_options]`, no
   `register_fixture`.
3. **Pick the hooks from `internals/hooks.md`**, not from memory:
   `pytest_addoption(parser)` for `--budget-ms`, `--budget-strict` and
   the ini key; `pytest_configure(config)` for the marker and the stash;
   `pytest_runtest_makereport(item, call)` as a `wrapper=True` hook to
   read the call phase's duration and change the outcome;
   `pytest_terminal_summary(terminalreporter, config)` for the report.
4. **Write it** (`recipes/plugin/src/pytest_budget/plugin.py`) and its
   pytester tests (`core/pytester.md`): one generated test file per
   behaviour, a run, `assert_outcomes`, and `fnmatch_lines` on what a
   user sees.
5. **Run with the plugin**: `uv sync; uv run pytest`: `11 passed`.
6. **Run without it** (invariant 7):
   `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"; uv run pytest`:
   `8 failed, 3 passed`. Three tests passed without the plugin:
   `test_no_budget_no_report`, `test_option_beats_ini`,
   `test_marker_beats_option`. Each only checked that "over budget" was
   absent, which is also true when nothing is loaded. Fixed by adding
   checks only the plugin can satisfy: `assert_outcomes(passed=1)` on
   runs that pass `--budget-ms` (a usage error without the plugin), and
   the `budget` fixture in the inner test. Then: `11 failed` without,
   `11 passed` with.
7. **Look for the cases pytest's reports make hard**
   (`internals/runner-and-reports.md`): an xpassed test has outcome
   `passed` and a `wasxfail` attribute, so the plugin would have counted
   it. Added `test_xfail_tests_are_left_alone`, saw it fail, added
   `hasattr(report, "wasxfail")` to the check, saw it pass.
8. **Both versions, both pytester modes**: `uv run pytest`,
   `uv run --with "pytest==8.4.2" pytest`,
   `uv run pytest --runpytest=subprocess`: `12 passed` each; without
   the plugin `12 failed`.
9. **Try it with xdist**, which many consumers use: `uv run --with
   pytest-xdist pytest -n 2 --budget-ms=50` on two slow tests: `2
   passed` and no "over budget" section; with `--budget-strict`, `2
   failed`. The section is built from the stash of the process running
   the tests; under xdist that is a worker, and the summary is printed by
   the controller. Reported as a limitation.

## The answer

```
## Result
New package pytest-budget (entry point pytest11: budget). Options
--budget-ms and --budget-strict, ini key budget_ms, marker
@pytest.mark.budget(ms), fixture budget. A wrapper on
pytest_runtest_makereport records passed call phases over budget in the
config stash and, with --budget-strict, turns them into failures;
pytest_terminal_summary prints an "over budget" section. xfail tests are
left alone.

## Checked
- uv run pytest (pytest 9.1.1): 12 passed.
- uv run --with "pytest==8.4.2" pytest: 12 passed.
- uv run pytest --runpytest=subprocess: 12 passed.
- PYTEST_DISABLE_PLUGIN_AUTOLOAD=1: 12 failed (the first version had 3
  tests passing without the plugin; fixed).
- test_xfail_tests_are_left_alone failed without the wasxfail check.
- With pytest-xdist (-n 2): --budget-strict still failed both slow
  tests, but the "over budget" section was empty, because each worker
  has its own config stash and the summary runs on the controller. Known
  limitation; a fix would read the reports in pytest_runtest_logreport,
  which the controller receives.

## Not checked
- Windows timing resolution for very small budgets.
```
