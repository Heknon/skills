# How a pytest run works

pytest is a small core plus plugins. Almost everything, including
collection, fixtures, the runner, the terminal output, `-k`, `skip` and
`xfail`, is a plugin in `_pytest/` implementing **hooks**, called through
**pluggy** (`internals/pluggy.md`). Your conftests and installed plugins
implement the same hooks and are called alongside pytest's own.

Find the installed source:
`uv run python -c "import _pytest, pathlib; print(pathlib.Path(_pytest.__file__).parent)"`.

## The phases, in order

Recorded on pytest 9.1.1 (8.4.2 is the same apart from fixture hook
counts) with a plugin that logged every hook call, for one module with
one passing and one failing test, and with `--debug` (`pytestdebug.log`
lists every call with its arguments and result):

**1. Start-up: configuration.** `pytest.main()` / the `pytest` command
builds a `PytestPluginManager` and a `Config`.

| Hook | Notes |
| --- | --- |
| `pytest_addhooks` | a plugin adds hook specifications |
| `pytest_addoption` | options and ini keys (`internals/config-and-conftests.md`) |
| `pytest_load_initial_conftests` | only called on plugins loaded before the conftests (`-p`, installed); *lab:* not called on a conftest |
| (command line parsed; initial conftests loaded) | |
| `pytest_cmdline_main` | firstresult: runs the session and returns the exit code |
| `pytest_configure` | after parsing; register markers, create stash data |

`pytest_cmdline_parse` is called before `-p` and installed plugins are
loaded; *lab:* an implementation in a `-p` plugin or a conftest is
never called. Output written to stdout or stderr during start-up is
captured and not shown; write to a file when checking these hooks.

**2. Session start.** `pytest_sessionstart`, then the header
(`pytest_report_header`).

**3. Collection** (`internals/collection.md`): `pytest_collection`, then
for each directory and file `pytest_collectstart`,
`pytest_make_collect_report`, `pytest_collect_directory`,
`pytest_ignore_collect`, `pytest_collect_file`,
`pytest_pycollect_makemodule`, `pytest_pycollect_makeitem` per name in a
module, `pytest_generate_tests` per test function, `pytest_itemcollected`
per item, `pytest_collectreport`; then `pytest_collection_modifyitems`,
`pytest_collection_finish`, `pytest_report_collectionfinish`.

**4. Running** (`internals/runner-and-reports.md`): `pytest_runtestloop`
calls, for each item, `pytest_runtest_protocol`:

```
pytest_runtest_logstart
  setup:    pytest_runtest_setup -> pytest_fixture_setup (per fixture)
            pytest_runtest_makereport -> pytest_runtest_logreport -> pytest_report_teststatus
  call:     pytest_runtest_call -> pytest_pyfunc_call
            (on a failed assert comparison: pytest_assertrepr_compare)
            pytest_runtest_makereport -> pytest_runtest_logreport -> pytest_report_teststatus
            (on failure: pytest_exception_interact)
  teardown: pytest_runtest_teardown -> pytest_fixture_post_finalizer
            pytest_runtest_makereport -> pytest_runtest_logreport -> pytest_report_teststatus
pytest_runtest_logfinish
```

**5. End.** `pytest_sessionfinish`, `pytest_terminal_summary`,
`pytest_unconfigure`.

## Where each part lives (9.1.1 source)

| Part | Module |
| --- | --- |
| entry, `Config`, plugin manager, conftest loading | `_pytest/config/__init__.py`, options: `config/argparsing.py` |
| hook specifications | `_pytest/hookspec.py` |
| `Session`, `Dir`, the collection loop, `--co` | `_pytest/main.py` |
| `Module`, `Class`, `Function`, `Package`, parametrize | `_pytest/python.py` |
| `Node`, `Item`, `File`, `Collector` base classes | `_pytest/nodes.py` |
| fixtures | `_pytest/fixtures.py` |
| setup/call/teardown, `CallInfo`, `SetupState` | `_pytest/runner.py` |
| `TestReport`, `CollectReport` | `_pytest/reports.py` |
| skip and xfail | `_pytest/skipping.py` |
| assertion rewriting | `_pytest/assertion/rewrite.py`, comparisons: `assertion/util.py` |
| terminal output | `_pytest/terminal.py` |
| stash | `_pytest/stash.py` |
| pytester | `_pytest/pytester.py` |
