# Write a plugin, or hooks in conftest.py

**Verdict you produce:** hooks and fixtures that pytest loads, checked
by pytester tests that pass with the plugin and fail without it.

```
where:     <conftest.py path | installed package with entry point name>
hooks:     <hook names, and which are wrappers>
checked:   <pytester test summary line on each pytest version in use>
without:   <summary line with the plugin disabled: every test must fail>
```

## Where the code goes

| Scope | Put it in |
| --- | --- |
| one folder of one project | that folder's `conftest.py`; only the runtest, report and fixture hooks are limited to that folder, others such as `pytest_collection_modifyitems` see the whole session (`internals/hooks.md`) |
| the whole project | the root `conftest.py` (the rootdir or the `testpaths` folder) |
| several projects | an installed package with a `pytest11` entry point (`recipes/plugin/`) |
| a plugin module in the project, loaded by name | `pytest_plugins = ["pkg.module"]` in the **root** `conftest.py`, or `-p pkg.module` |

*lab (8.4 and 9.1):* `pytest_plugins` in `tests/sub/conftest.py`
interrupted collection when running from the root: `Defining
'pytest_plugins' in a non-top-level conftest is no longer supported`.

## Steps

1. **Find the hook** in `internals/hooks.md`, with its exact arguments.
   Never name a hook from memory: *lab:* a typo (`pytest_runtest_makerport`)
   stops the run with `PluginValidationError: unknown hook
   'pytest_runtest_makerport' in plugin <module 'conftest' ...>`, and an
   argument not in the spec (`def pytest_runtest_makereport(item, rep)`)
   with `Argument(s) {'rep'} are declared in the hookimpl but can not be
   found in the hookspec`. A hook implementation may take **fewer**
   arguments than the spec, by name, in any order.
2. **Write the smallest hook** that does the job (patterns below).
3. **Write pytester tests** first for what users will see: the option in
   `--help`, the output lines, the outcomes (`core/pytester.md`).
4. **Run the tests with the plugin, then without it.** For an installed
   plugin: `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"; uv run pytest;
   Remove-Item Env:PYTEST_DISABLE_PLUGIN_AUTOLOAD` (inner pytester runs
   inherit it and do not load the plugin). *lab:* 12 passed with it, 12
   failed without it. The switch only stops entry-point loading: a plugin
   the tests load themselves (`runpytest("-p", name)`, `plugins=[module]`)
   still loads, and `-p no:` cannot be passed to inner runs because
   pytester removes `PYTEST_ADDOPTS`. For those, break the plugin on
   purpose instead (rename its hook function, or return early from it),
   run, and restore it. A test that passes without the plugin checks
   nothing; see "absent lines" in `core/pytester.md`.
5. Run on every pytest version the project supports
   (`uv run --with "pytest==8.4.2" pytest`).

## Patterns (all in `recipes/plugin/`, verified on 8.4.2 and 9.1.1)

**Command-line option with a configuration-file default**

```python
def pytest_addoption(parser):
    group = parser.getgroup("budget", "time budget per test")
    group.addoption("--budget-ms", type=float, default=None, help="...")
    parser.addini("budget_ms", help="default for --budget-ms", default="")
```

Read them with `config.getoption("budget_ms")` (the `dest`: dashes become
underscores) and `config.getini("budget_ms")`. Options are only parsed
from the command line if the file defining them is loaded at startup: an
installed plugin, or an initial conftest (*lab:* an option defined in
`tests/sub/conftest.py` gave `unrecognized arguments: --flag=1` from the
root, and worked with `pytest tests/sub --flag=1`).

**Marker**

```python
def pytest_configure(config):
    config.addinivalue_line("markers", "budget(ms): time budget for this test")
```

Read it with `item.get_closest_marker("budget")` (`.args`, `.kwargs`).

**Change or read a report: a new-style wrapper**

```python
@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield          # the report the other implementations made
    if report.when == "call" and report.passed:
        ...                 # read or change the report
    return report           # always return it
```

*lab:* forgetting `return report` stops the run with `AttributeError:
'NoneType' object has no attribute 'when'`; writing `yield` without
`wrapper=True` hands a generator to pytest: `AttributeError: 'generator'
object has no attribute 'skipped'`. The old style
(`hookwrapper=True`, `outcome = yield`, `outcome.get_result()`) still
works on both versions; keep it in old code, use `wrapper=True` in new
code.

**State for the run: the stash**

```python
key = pytest.StashKey[list[str]]()      # module level
config.stash[key] = []                  # in pytest_configure
config.stash.get(key, [])               # anywhere with the config
```

Items and nodes have a `stash` too (`item.stash[key]`). Never keep run
state in module globals: in-process pytester runs import the plugin
once, so globals leak between runs.

**Summary at the end**

```python
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    terminalreporter.section("over budget")
    terminalreporter.write_line("...")
```

**Fixture**: define it in the plugin module with `@pytest.fixture`, as in
a conftest.

**A hook of your own, for other plugins to implement**: a module of
specifications, added in `pytest_addhooks(pluginmanager)` with
`pluginmanager.add_hookspecs(module)`; call it with keyword arguments
only: `config.hook.pytest_budget_exceeded(nodeid=..., took_ms=...)`.
Implement a hook that may not exist with
`@pytest.hookimpl(optionalhook=True)` (*lab:* without it, an unknown
hook stops the run).

## Never

- Never write `hookwrapper=True` and `wrapper=True` behaviour mixed: in
  `wrapper=True`, `yield` gives the result and you return it; in
  `hookwrapper=True`, `yield` gives an outcome object and the return
  value is ignored.
- Never mark hooks with `@pytest.mark.tryfirst` or attributes; use
  `@pytest.hookimpl(tryfirst=True)` (the old way is deprecated since 7.2).
- Never call a hook with positional arguments (*lab:*
  `HookCaller.__call__() takes 1 positional argument but 2 were given`).
- Never ship a plugin whose tests pass with it disabled.
