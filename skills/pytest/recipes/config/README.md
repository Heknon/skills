# Configuration recipes

Two `pyproject.toml` settings blocks for a project with code in `src/`
and tests in `tests/`. Copy the `[tool.pytest...]` table into the
project's `pyproject.toml`; keep only one configuration file with pytest
settings (`core/configuration.md`).

| File | Use when |
| --- | --- |
| `pyproject-8-and-9.toml` | any environment may run pytest 8 (`[tool.pytest.ini_options]`, strings) |
| `pyproject-9-only.toml` | every environment runs pytest 9.0 or later (`[tool.pytest]`, native TOML, `strict = true`) |

## Checked (*lab*, a project with `src/app/__init__.py` and two test files)

| Case | 8-and-9 on 8.4.2 | 8-and-9 on 9.1.1 | 9-only on 9.1.1 | 9-only on 8.4.2 |
| --- | --- | --- | --- | --- |
| as written | `2 passed, 1 xfailed` | same | same | **`ModuleNotFoundError: No module named 'app'`**: 8 ignores `[tool.pytest]`, so `pythonpath` is not set (header still says `configfile: pyproject.toml`) |
| a typo marker `@pytest.mark.slwo` | `'slwo' not found in markers configuration option` | same | same | |
| a typo key `testpahts` | `ERROR: Unknown config option: testpahts` | same | same | |
| an `xfail` test that passes | `[XPASS(strict)] fixed now`, `1 failed` | same | same | |

`filterwarnings = ["error"]` turns every warning into a failure; drop it
for a legacy suite with many warnings, or list the ones to ignore after
it (`"ignore::DeprecationWarning:somepackage.*"`).

`pythonpath = ["src"]` lets tests import the code without installing
it. If the project is installed into the environment (`uv sync` with a
`[build-system]`), remove it: tests then import what users import.
