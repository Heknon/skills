# Config, options, conftests and the stash

For choosing configuration files and import modes, see
`core/configuration.md`.

## Parser: declaring options

In `pytest_addoption(parser, pluginmanager)`:

```python
group = parser.getgroup("budget", "time budget per test")      # a section in --help
group.addoption("--budget-ms", type=float, default=None, dest="budget_ms", help="...")
parser.addini("budget_ms", help="...", type="string", default="")
```

- `addoption` takes `argparse` arguments (`action`, `type`, `default`,
  `dest`, `choices`, `help`). The `dest` defaults to the long name with
  dashes as underscores.
- `addini` types: `string` (default), `bool`, `args` (split like a
  shell), `linelist` (one per line), `paths` (relative to the
  configuration file), `pathlist` (py.path), and from 8.4 `int` and
  `float`. 9.0 added `aliases=[...]`.
- Environment: `PYTEST_ADDOPTS` is put **before** the command-line
  arguments (`config/__init__.py`: `shlex.split(env_addopts) + args`), so
  options typed on the command line win; pytester removes it for inner
  runs.

## Config: reading them (*lab*, both versions)

| Read | Call |
| --- | --- |
| an option | `config.getoption("budget_ms")` or `config.getoption("--budget-ms")`; also `config.option.budget_ms` |
| an option that may not exist | `config.getoption("nope", "dflt")` gives `dflt`; without a default, `ValueError: no option named 'nope'` |
| an ini value | `config.getini("markers")`; unknown: `ValueError: unknown configuration value: 'nope'` |
| rootdir and file | `config.rootpath`, `config.inipath` (`None` without a file) |
| how pytest was invoked | `config.invocation_params.dir`, `.args` |
| is a plugin loaded | `config.pluginmanager.hasplugin("name")` (*lab:* `False` for a plugin blocked with `-p no:`) |
| call a hook | `config.hook.pytest_x(...)` |
| a fixture giving the config | `pytestconfig` |

`config.inicfg` is deprecated in 9.1: use `getini`.

## Stash

Typed storage on `Config` and every node, for plugin data, instead of
setting attributes on pytest's objects:

```python
budget_key = pytest.StashKey[float]()   # one key per value, at module level
item.stash[budget_key] = 0.5
item.stash[budget_key]                 # KeyError if unset
item.stash.get(budget_key, None)
budget_key in item.stash
```

*lab:* a fresh `StashKey` never finds another key's value
(`stash.get(pytest.StashKey[int](), "missing")` gave `missing`). The
config's stash lives for the run; an item's for the item.

## Conftest loading

- **Initial conftests** are loaded during start-up
  (`_set_initial_conftests`, 9.1.1): for each path on the command line
  (without one: `testpaths` when run from the rootdir, else the current
  directory), the conftests in that directory and its parents, and in
  its direct `test*` subdirectories. The upward search stops at
  `confcutdir`, which defaults to the configuration file's directory (or
  the rootdir without one). Only initial conftests can add command-line
  options and use `pytest_plugins`.
- Other conftests are loaded during collection, when their directory is
  collected. *lab:* an option in `tests/sub/conftest.py` gave
  `unrecognized arguments: --flag=1` when running `pytest --flag=1` from
  the root, and worked with `pytest tests/sub --flag=1`; the option
  still existed later with its default. `pytest_plugins` there
  interrupted collection (`Defining 'pytest_plugins' in a non-top-level
  conftest is no longer supported`) from the root, and loaded when the
  path was given.
- Each conftest is registered as a plugin. Hooks called through a node's
  `ihook` (the runtest, report, `collect_file` and fixture hooks) run only
  for nodes under its directory; every other hook, including
  `pytest_collection_modifyitems` and `pytest_terminal_summary`, is
  session-wide (`internals/hooks.md`).
- `--noconftest` skips all conftests; `--confcutdir=DIR` stops the
  upward search at DIR.
- Conftests are always assertion-rewritten (`internals/assertion-rewriting.md`).
