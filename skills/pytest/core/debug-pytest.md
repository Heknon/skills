# Ask pytest what it is doing

**Verdict you produce:** a claim about pytest's behaviour (which plugin,
which fixture, which hook, which order, which file) with the command
output that shows it.

```
question: <what you needed to know>
command:  <the command>
evidence: <the lines that answer it>
```

Use this before reading pytest's source and before any claim in
`internals/`: the running pytest is the version that matters.

## Which command answers which question (*lab*, 9.1.1 and 8.4.2)

| Question | Command | Shows |
| --- | --- | --- |
| which versions and plugins | `uv run pytest -VV` | pytest version and path, then `registered third-party plugins:` with each plugin's version and file |
| which config, rootdir, plugins for this run | `uv run pytest --co \| Select-Object -First 6` | `rootdir:`, `configfile:`, `plugins:` |
| which tests are collected, and their node ids | `uv run pytest --co -q` | one node id per line |
| the collection tree | `uv run pytest --co` | `<Dir>`, `<Package>`, `<Module>`, `<Class>`, `<Function>` nested |
| which fixtures exist here | `uv run pytest --fixtures tests/api` | every fixture visible there, grouped by where it is defined |
| which fixture definition a test uses | `uv run pytest --fixtures-per-test "<node id>"` | each fixture with `file:line` |
| fixture order and scope, without running tests | `uv run pytest --setup-plan "<node id>"` | `SETUP S name` ... `TEARDOWN S name` |
| the same while running | `uv run pytest --setup-show "<node id>"` | the same, interleaved with the test |
| which plugin modules and conftests got registered | `uv run pytest --trace-config --co -q` | `PLUGIN registered: <module 'conftest' from '...'>` per plugin |
| every hook call, with arguments and results | `uv run pytest --debug "<node id>"` | writes `pytestdebug.log`: `pytest_runtest_makereport [hook]`, its arguments, then `finish pytest_runtest_makereport --> <TestReport ... when='setup' outcome='passed'>` |
| does a plugin cause it | `uv run pytest -p no:<name> ...` | the run without that plugin; `<name>` as in `-VV` or the entry point name |
| do installed plugins cause it | `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"; uv run pytest ...; Remove-Item Env:PYTEST_DISABLE_PLUGIN_AUTOLOAD` | no third-party plugin is loaded unless named with `-p` (*lab:* the `plugins:` line disappears) |
| does a conftest cause it | `uv run pytest --noconftest ...` | the run without any `conftest.py` |
| what a configuration value is | `uv run pytest --help` bottom part lists ini keys; in code: `config.getini("name")` | |

`--debug` overwrites `pytestdebug.log`; delete it after reading.
`--debug=other.log` names the file.

## Steps

1. Write the question in one sentence.
2. Pick the command from the table, run it on the smallest selection
   (one node id) and read the lines it names.
3. If no command answers it, write a pytester test or a tiny
   `conftest.py` in a scratch folder that prints what you need from a
   hook (`internals/hooks.md`), and run that.
4. Only then read pytest's source, in the installed version:
   `uv run python -c "import _pytest, pathlib; print(pathlib.Path(_pytest.__file__).parent)"`.
5. Write the verdict with the evidence lines.

## Never

- Never state which fixture, plugin or configuration file wins without
  one of the outputs above.
- Never leave `pytestdebug.log`, scratch conftests or `-p no:` in the
  project after investigating.
