# Hooks

A hook is a function named `pytest_<something>` that pytest calls at a
fixed point of the run. pytest defines the **specification** (name and
arguments) in `_pytest/hookspec.py`; your conftest or plugin writes an
**implementation** with the same name.

## Rules (*lab*, 8.4.2 and 9.1.1)

- The name must match a specification exactly, or the run stops with
  `PluginValidationError: unknown hook '<name>'` (unless the hook is
  marked `@pytest.hookimpl(optionalhook=True)`, for hooks from plugins
  that may not be installed).
- Take any subset of the specification's arguments, by name; an argument
  not in the specification stops the run (`Argument(s) {'rep'} are
  declared in the hookimpl but can not be found in the hookspec`).
- **Order**: implementations run last-registered first; `tryfirst=True`
  moves one to the front, `trylast=True` to the back. Wrappers run
  around all of them.
- **Results**: a normal hook returns the list of all non-`None` results.
  A **firstresult** hook stops at the first non-`None` result and returns
  it (so returning a value from `pytest_runtest_makereport` or
  `pytest_pyfunc_call` replaces pytest's own work).
- **Historic** hooks are replayed for plugins registered later
  (`pytest_addoption`, `pytest_configure`, `pytest_addhooks`,
  `pytest_plugin_registered`, `pytest_warning_recorded`).
- Call a hook only with keyword arguments: `config.hook.pytest_x(a=1)`.
- **Which tests a conftest's hooks see** (*lab*, 8.4.2 and 9.1.1). Hooks
  that pytest calls through a node's `ihook` are filtered by path: in
  `tests/sub/conftest.py`, `pytest_runtest_setup` ran only for
  `tests/sub/test_s.py::test_s`. These are the `pytest_runtest_*`
  hooks, `pytest_runtest_makereport`, `pytest_runtest_logreport`,
  `pytest_collect_file`, `pytest_fixture_setup`. Every other hook is
  **session-wide**, wherever the conftest is: the same file's
  `pytest_collection_modifyitems` received every item, including
  `tests/other/test_o.py::test_o`; `pytest_configure`,
  `pytest_sessionstart`, `pytest_sessionfinish` and
  `pytest_terminal_summary` run once for the whole session. In a
  session-wide hook, filter by `item.path` yourself if the conftest's
  folder is meant.
- `pytest_addoption` in a conftest found during collection is still
  called, but its options cannot be given on the command line
  (`internals/config-and-conftests.md`). `pytest_load_initial_conftests`
  is never called on a conftest, only on `-p` and installed plugins.

## Wrappers

```python
@pytest.hookimpl(wrapper=True)          # new style, pluggy 1.1+
def pytest_runtest_makereport(item, call):
    report = yield                      # the result of the inner implementations
    ...
    return report                       # required; it becomes the hook's result
```

- Exceptions from inner implementations are raised at the `yield`; wrap
  it in `try`/`except` to handle or replace them (*lab:* a wrapper
  returned a value instead of the `ValueError` raised inside).
- The old style, `@pytest.hookimpl(hookwrapper=True)`, receives an
  outcome object from `yield` (`outcome.get_result()`,
  `outcome.force_result(x)`, `outcome.exception`) and its return value is
  ignored; an exception inside propagates unless the wrapper calls
  `outcome.force_result(...)` (*lab*). Both styles run
  on 8.4 and 9.1; write new code with `wrapper=True`.
- Deprecated: configuring hooks with `@pytest.mark.tryfirst` or function
  attributes; use `@pytest.hookimpl(...)`.

## Catalogue (9.1.1; F = firstresult, H = historic)

Printed from the installed `_pytest.hookspec` of each version. 8.4.2 has
the same hooks but also passes deprecated `py.path` arguments (`path`,
`startdir`) to `pytest_ignore_collect`, `pytest_collect_file`,
`pytest_pycollect_makemodule`, `pytest_report_header` and
`pytest_report_collectionfinish`; 9.0 still passes them (using them is
an error by default), 9.1 removed them. Use the `pathlib`
arguments below, which both have.

**Start-up and configuration**

| Hook | |
| --- | --- |
| `pytest_addhooks(pluginmanager)` | H; add your own hook specifications |
| `pytest_addoption(parser, pluginmanager)` | H; options and ini keys |
| `pytest_load_initial_conftests(early_config, parser, args)` | before initial conftests load |
| `pytest_cmdline_main(config)` | F |
| `pytest_configure(config)` | H; after parsing |
| `pytest_unconfigure(config)` | at exit |
| `pytest_plugin_registered(plugin, plugin_name, manager)` | H |
| `pytest_sessionstart(session)`, `pytest_sessionfinish(session, exitstatus)` | |

**Collection**

| Hook | |
| --- | --- |
| `pytest_collection(session)` | F; the whole collection |
| `pytest_ignore_collect(collection_path, config)` | F; return `True` to skip a path |
| `pytest_collect_directory(path, parent)` | F; the collector for a directory |
| `pytest_collect_file(file_path, parent)` | return a `File` collector for a file you understand |
| `pytest_pycollect_makemodule(module_path, parent)` | F |
| `pytest_pycollect_makeitem(collector, name, obj)` | F; items for a name in a module or class |
| `pytest_generate_tests(metafunc)` | parametrize dynamically: `metafunc.parametrize(...)` |
| `pytest_make_parametrize_id(config, val, argname)` | F; id for a parameter value |
| `pytest_collectstart(collector)`, `pytest_collectreport(report)`, `pytest_itemcollected(item)` | |
| `pytest_make_collect_report(collector)` | F |
| `pytest_collection_modifyitems(session, config, items)` | reorder or remove items in place |
| `pytest_deselected(items)` | call it for items you remove, so they are counted as deselected |
| `pytest_collection_finish(session)` | |

**Running**

| Hook | |
| --- | --- |
| `pytest_runtestloop(session)` | F |
| `pytest_runtest_protocol(item, nextitem)` | F; one item's three phases |
| `pytest_runtest_logstart(nodeid, location)`, `pytest_runtest_logfinish(nodeid, location)` | |
| `pytest_runtest_setup(item)`, `pytest_runtest_call(item)`, `pytest_runtest_teardown(item, nextitem)` | |
| `pytest_pyfunc_call(pyfuncitem)` | F; calls the test function |
| `pytest_runtest_makereport(item, call)` | F; builds the `TestReport`; wrap it to read or change reports |
| `pytest_runtest_logreport(report)` | every report, for reading |
| `pytest_fixture_setup(fixturedef, request)` | F |
| `pytest_fixture_post_finalizer(fixturedef, request)` | |
| `pytest_exception_interact(node, call, report)` | on failures that may enter the debugger |
| `pytest_markeval_namespace(config)` | extra names for `skipif`/`xfail` condition strings |

**Reporting**

| Hook | |
| --- | --- |
| `pytest_report_header(config, start_path)` | lines for the header |
| `pytest_report_collectionfinish(config, start_path, items)` | lines after collection |
| `pytest_report_teststatus(report, config)` | F; the category, letter and word for a report |
| `pytest_terminal_summary(terminalreporter, exitstatus, config)` | add a summary section |
| `pytest_assertrepr_compare(config, op, left, right)` | custom explanation of a failed comparison |
| `pytest_assertion_pass(item, lineno, orig, expl)` | needs `enable_assertion_pass_hook = true` |
| `pytest_warning_recorded(warning_message, when, nodeid, location)` | H |
| `pytest_report_to_serializable(config, report)`, `pytest_report_from_serializable(config, data)` | F; used by xdist |

**Other**: `pytest_internalerror(excrepr, excinfo)`,
`pytest_keyboard_interrupt(excinfo)`, `pytest_enter_pdb(config, pdb)`,
`pytest_leave_pdb(config, pdb)`, `pytest_cmdline_parse(pluginmanager,
args)` (F; only reaches built-in plugins and objects passed to
`pytest.main(plugins=[...])`, not conftests or `-p` plugins; see
`internals/architecture.md`).

## Your own hooks

```python
# myplugin/hooks.py: specifications only
def pytest_budget_exceeded(nodeid, took_ms):
    """Called when a test goes over budget."""

# myplugin/plugin.py
def pytest_addhooks(pluginmanager):
    from myplugin import hooks
    pluginmanager.add_hookspecs(hooks)

# later, anywhere with the config:
config.hook.pytest_budget_exceeded(nodeid=item.nodeid, took_ms=took)
```

*lab:* a conftest implementing `pytest_budget_exceeded` received the
call on both versions.
