# Test a plugin with pytester

**Verdict you produce:** tests that run pytest on small generated files
and check what a user would see, passing with the plugin and failing
without it.

```
loaded by:  <installed entry point | -p name | plugins=[module]>
mode:       <in process | subprocess>, and why
with:       <summary line>
without:    <summary line with the plugin disabled>
versions:   <pytest versions run>
```

## Enable it

`pytester` is a built-in plugin that is off by default. Turn it on in
the root `conftest.py` with `pytest_plugins = ["pytester"]`, or with
`-p pytester` in `addopts` (`recipes/plugin/pyproject.toml`).

## How a pytester test works

`pytester` gives each test a new empty directory (`pytester.path`) and
makes it the current directory. You write files into it and run pytest
on it; the inner run's output is captured into a `RunResult`.

```python
def test_reports_slow_test(pytester):
    pytester.makepyfile("""
        import time
        def test_slow():
            time.sleep(0.2)
    """)
    result = pytester.runpytest("--budget-ms=50")
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["*= over budget =*", "*::test_slow: * ms (budget 50 ms)"])
```

| Make | Call |
| --- | --- |
| a test module named after the test | `pytester.makepyfile("...")` (source is dedented) |
| named modules | `pytester.makepyfile(test_one="...", test_two="...")` |
| a conftest | `pytester.makeconftest("...")` |
| `tox.ini` with `[pytest]` | `pytester.makeini("[pytest]\nbudget_ms = 50")` |
| `pyproject.toml` | `pytester.makepyprojecttoml("...")` |
| `pytest.toml` (9.0 and later) | `pytester.maketoml("...")` |
| any file | `pytester.makefile(".txt", name="...")`; folders: `pytester.mkdir`, `pytester.mkpydir` |

## How the plugin gets into the inner run (*lab*, 8.4.2 and 9.1.1)

| Way | In process | Subprocess |
| --- | --- | --- |
| installed with a `pytest11` entry point | loaded | loaded |
| `pytester.runpytest("-p", "myplugin")` | loaded | only if `myplugin` is importable in a new process |
| `pytester.runpytest(plugins=[module_object])` | loaded | not supported |
| `pytester.plugins = ["myplugin"]` | **ignored** by `runpytest` (`fixture 'answer' not found`); used by `parseconfig` | loaded if importable |

Prefer an installed plugin (`uv sync` installs the project): it loads
the way users load it, in both modes. *lab:* a plugin module that was
importable only because it sat next to the tests failed in subprocess
mode with `ImportError: Error importing plugin "myplugin": No module
named 'myplugin'`.

## In process or subprocess

- `pytester.runpytest(...)` runs in process by default: fast, and the
  inner run's objects are available (`inline_run`). An installed plugin
  is imported once, by the outer run, and shared by all inner runs; state
  in module globals leaks between them. *lab:* a global incremented in
  `pytest_configure` read 1 in the outer run, then 2 and 3 in two inner
  runs of one test; with `--runpytest=subprocess` it read 1 each time.
  Keep run state in the stash.
- `pytester.runpytest_subprocess(...)`, or the whole suite with
  `uv run pytest --runpytest=subprocess`: slower, fully isolated. Use it
  for plugins that change global state (logging, warnings filters,
  signals, `sys.modules`), or to check that isolation is not hiding a
  bug. *lab:* the recipe passed in both modes.
- pytester removes `PYTEST_ADDOPTS` for inner runs and sets `HOME` to
  the test directory, so the outer command line and user configuration
  do not reach them; `PYTEST_DISABLE_PLUGIN_AUTOLOAD` does, and stops
  only entry-point plugins. To check tests of a plugin loaded with `-p`
  or `plugins=` without it, break the plugin temporarily
  (`core/write-plugin.md` step 4).

## Checking the result

| Check | Call |
| --- | --- |
| outcome counts | `result.assert_outcomes(passed=1, failed=0, errors=0, skipped=0, xfailed=0, xpassed=0)`; any count not given must be 0 (`warnings`, `deselected` are checked only if given) |
| exit code | `result.ret == pytest.ExitCode.TESTS_FAILED` (0 ok, 1 failed, 2 interrupted, 3 internal, 4 usage, 5 none collected) |
| lines, in order, with `*` and `?` wildcards | `result.stdout.fnmatch_lines(["*first*", "*later*"])` |
| lines by regular expression | `result.stdout.re_match_lines([r"FAILED .*::test_a - assert 0"])` |
| a line is absent | `result.stdout.no_fnmatch_line("*over budget*")` |
| the text | `result.stdout.str()`, `result.outlines`, `result.errlines` |
| the counts as a dict | `result.parseoutcomes()` gives `{"failed": 1}` |

`fnmatch_lines` matches each pattern against a whole line, in the given
order, with other lines allowed between; `consecutive=True` forbids
lines between them (*lab:* failed across the blank line before the
summary). `assert_outcomes` on a run that never reached the summary (a
usage error) raises `ValueError: Pytest terminal summary report not
found`.

**Absent lines.** `no_fnmatch_line` also passes when the plugin is not
loaded at all. *lab:* three of the recipe's tests used only it and still
passed with the plugin disabled. Pair each absence check with something
only the loaded plugin produces: `assert_outcomes(passed=1)` on a run
that uses the plugin's option (a usage error without it), or the
plugin's fixture in the inner test.

## Deeper: the inner run's objects

```python
reprec = pytester.inline_run("-p", "myplugin")
reprec.assertoutcome(passed=1, failed=1)
passed, skipped, failed = reprec.listoutcomes()          # TestReport lists
calls = reprec.getcalls("pytest_collection_modifyitems")  # recorded hook calls
[i.name for i in calls[0].items]
items = pytester.getitems("def test_a(): pass")           # collect only
config = pytester.parseconfig()                            # config only
```

*lab:* each of these ran on both versions. Use them to test collection
or configuration hooks without matching text.

## Never

- Never test a plugin only by running it on the project's own tests;
  write pytester tests with generated files.
- Never rely on `pytester.plugins` with `runpytest` in process.
- Never keep a pytester test that passes with the plugin disabled.
