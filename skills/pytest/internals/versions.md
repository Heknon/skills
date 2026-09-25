# pytest 8 and 9

Check first: `uv run pytest --version`, and read the patch number too:
9.0.x and 9.1.x differ in ways that matter below. Both lines below were run in the
lab unless marked "changelog".

| Topic | 8.4 | 9.0 / 9.1 |
| --- | --- | --- |
| Python | 3.9+ | 3.10+ (changelog) |
| `[tool.pytest]` in `pyproject.toml`, native TOML types | **ignored silently** (*lab:* markers there were not registered) | read (9.0) |
| `[tool.pytest.ini_options]` | read | read |
| `pytest.toml` / `.pytest.toml` | not a config file | first in the search order (9.0) |
| two config files present | first one wins | first wins, header warns `(WARNING: ignoring pytest config in pyproject.toml!)` |
| `strict = true`, `strict_parametrization_ids`, and the keys `strict_markers`, `strict_config` | unknown (*lab:* `Unknown config option: strict_markers`, and a typo marker only warns) | 9.0 |
| `--strict-markers`, `--strict-config` in `addopts` | work | **ignored in 9.0.x** (changelog #14442), work again from 9.1.0 |
| both `[tool.pytest]` and `[tool.pytest.ini_options]` in one file | runs (ignores `[tool.pytest]`) | error: `Cannot use both [tool.pytest] ... and [tool.pytest.ini_options] ... simultaneously` |
| `strict_xfail` | named `xfail_strict` | `strict_xfail`, `xfail_strict` kept as alias |
| `subtests` fixture | `fixture 'subtests' not found` | built in (9.0), reported as `SUBFAILED[msg] (i=1)` |
| `PytestRemovedIn9Warning` | warning | error (changelog) |
| hook arguments `path`, `startdir` (py.path) | passed, deprecated | 9.0: still passed, using them is an error by default; 9.1: removed |
| `pytest.register_fixture` | missing | 9.1 |
| same-name fixtures registered by plugin code | last registered wins | the more specific node wins, then last registered (9.1) |
| `pytester.maketoml` | missing | 9.0 |
| `pytester` subprocess mode with several `pytester.plugins` | only the first used (changelog) | all used (9.0 fix) |
| `Parser.addini(aliases=...)` | missing | 9.0 |
| `--max-warnings`, `assertion_text_diff_style`, `approx` with datetimes | missing | 9.1 (changelog) |
| custom item failure text on the `FAILED` summary line | node id only | node id and `repr_failure` text |
| deprecated in 9.1, removed in 10 | | `FixtureDef` `baseid`/`nodeid` strings, `FixtureDef.has_location`, class-scoped fixtures as instance methods, non-Collection iterables in `parametrize`, `config.inicfg`, `--pastebin`, `pytest.console_main`, `getfixturevalue` of a new fixture during teardown |

Same on both (*lab*): the hook catalogue apart from the py.path
arguments, the hook call order, `wrapper=True` and `hookwrapper=True`,
pytester's API used in `recipes/plugin/`, exit codes, the import
mismatch error, assertion rewriting rules, fixture resolution, report
fields and outcomes.

## Supporting both

- Configuration in `[tool.pytest.ini_options]` (strings, as in ini
  files) with `--strict-markers` in `addopts`; not `[tool.pytest]`, not
  `strict = true` (`recipes/config/`). Exclude pytest 9.0.x, which
  ignores those flags: `pytest>=8.4,!=9.0.*`.
- Parametrize instead of `subtests`.
- Hooks with the `pathlib` arguments only (`collection_path`,
  `file_path`, `module_path`, `start_path`).
- Fixtures with `@pytest.fixture`, not `pytest.register_fixture`.
- Run the suite on each: `uv run --with "pytest==8.4.2" pytest` and
  `uv run --with "pytest==9.1.1" pytest`.
