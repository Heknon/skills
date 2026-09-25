# Configuration, rootdir, conftest and imports

**Verdict you produce:** the configuration pytest actually used, and the
cause of an import or collection problem.

```
rootdir:    <path>             (from the header)
configfile: <file or none>     (from the header, with any WARNING on the same line)
import:     <prepend | append | importlib>, sys.path gets <what>
cause:      <the setting or file that explains the problem>
```

## Read the header first

```
uv run pytest --co | Select-Object -First 10
```

prints `rootdir:`, `configfile:`, `testpaths:` and `plugins:` (other
plugins may add lines, so read ten, not six). *lab, 9.1.1:* with both
a `pytest.ini` and a `pyproject.toml` present, the header said
`configfile: pytest.ini (WARNING: ignoring pytest config in
pyproject.toml!)`.

## Which file configures pytest (9.1)

Searched from the common ancestor of the paths given (or the current
directory) upwards; the first match wins, and **files are never merged**:

1. `pytest.toml`, `.pytest.toml` (9.0 and later): always match, even empty; table `[pytest]`.
2. `pytest.ini`, `.pytest.ini`: always match, even empty; section `[pytest]`.
3. `pyproject.toml` with `[tool.pytest]` (9.0 and later, native TOML types) or `[tool.pytest.ini_options]` (strings, as in ini files).
4. `tox.ini` with `[pytest]`.
5. `setup.cfg` with `[tool:pytest]`.

The configfile's directory becomes the rootdir. `--rootdir` forces it
(not from `addopts`); `-c file` picks the file.

**Versions matter.** pytest 8 does not read `[tool.pytest]` at all:
*lab:* with markers registered only in `[tool.pytest]`, 8.4.2 ran
without them and warned `PytestUnknownMarkWarning: Unknown
pytest.mark.slow`. A project supporting 8 keeps `[tool.pytest.ini_options]`
(`recipes/config/`).

## Strict settings

| Setting | Effect |
| --- | --- |
| `--strict-markers` in `addopts` (both); the key `strict_markers` (9.0 and later) | an unregistered marker is an error at collection (*lab:* ``'typo_mark' not found in `markers` configuration option``) |
| `--strict-config` in `addopts` (both); the key `strict_config` (9.0 and later) | unknown configuration keys are errors (`ERROR: Unknown config option: testpahts`) |
| `xfail_strict` (both versions; 9.0 adds the name `strict_xfail`) | an xfail test that passes fails the run |
| `strict_parametrization_ids` (9.0) | duplicate parametrize ids are errors |
| `strict = true` (9.0) | all of the above (*lab:* same error for the unknown marker) |

Register markers in the configuration: `markers = ["slow: slow tests"]`.

*lab:* on 8.4.2, the keys `strict_markers = true` or `strict_config =
true` are themselves unknown options: pytest warns `Unknown config
option: strict_markers` and a typo marker passes with only a warning.
On 8.x use the command-line flags in `addopts`.

**pytest 9.0.x ignored `--strict-markers` and `--strict-config` given
in `addopts`** (fixed in 9.1.0, changelog #14442). Read the full
version: on 9.0.x, use the keys (`strict_markers = true`, or `strict =
true`) instead of the flags.

## Imports

`rootdir` does not change `sys.path`. What imports tests is the **import
mode** (`--import-mode`, or `addopts`):

| Mode | sys.path | Same file names in two folders |
| --- | --- | --- |
| `prepend` (default) | the test file's base directory (the first folder upwards without `__init__.py`) is put first | fails: `import file mismatch` (*lab*) unless the folders are packages |
| `append` | the same, appended | same |
| `importlib` | not changed | works (*lab:* `2 passed`); tests cannot import each other, and test helpers must live in an importable package |

Why `python -m pytest` works and `pytest` does not: `python -m` puts the
current directory on `sys.path`, the `pytest` command does not. *lab*,
flat layout (`mypkg/` next to `tests/`): `pytest` gave
`ModuleNotFoundError: No module named 'mypkg'`, `python -m pytest`
passed. Fix it so both work:

1. **Install the project** into the environment: in a uv project with a
   `[build-system]`, `uv sync` installs it editable, and `uv run pytest`
   imports it from anywhere. Preferred.
2. Or `pythonpath = ["src"]` (or `["."]`) in the configuration. *lab:* a
   src layout passed with `pythonpath = ["src"]`.
3. Or a `tests/__init__.py` in a flat layout, which makes the project
   root the base directory (*lab:* passed). Not for src layouts.

## conftest.py

- Loaded for its folder and every folder below. The ones in the rootdir
  and in the folders of the paths given on the command line are loaded
  at startup ("initial conftests"): only those can add command-line
  options (`pytest_addoption`).
- `pytest_plugins = [...]` is allowed only in the root `conftest.py`.
- Hooks in a conftest: the runtest, report and fixture hooks apply only
  to tests under its folder, but `pytest_collection_modifyitems`,
  `pytest_terminal_summary` and the session hooks see the whole session
  wherever the conftest is (*lab*); filter by `item.path` when only the
  folder is meant (`internals/hooks.md`).
- `confcutdir` stops the upward search.
- Do not import from `conftest.py` (`core/fixtures.md`).

## Never

- Never fix an import error by adding `sys.path.insert` to a test or a
  conftest; choose one of the three fixes above.
- Never keep two configuration files with pytest settings; one is
  silently ignored.
- Never move to `[tool.pytest]` while any environment still runs pytest 8.
- Never have both `[tool.pytest]` and `[tool.pytest.ini_options]` in one
  `pyproject.toml`. *lab, 9.1.1:* `ERROR: .../pyproject.toml: Cannot use
  both [tool.pytest] (native TOML types) and [tool.pytest.ini_options]
  (string-based INI format) simultaneously.` pytest 8 runs, because it
  ignores `[tool.pytest]`. Move settings from one table to the other;
  never copy them.
