# setuptools

Verified on setuptools 84.0.0 (setuptools-scm 10.3.4 for versions from
git), built with uv 0.12.19. Recipe: `recipes/flat-setuptools/`. Source
to read when something is not here: `setuptools/discovery.py` (finding
packages), `setuptools/command/build_py.py` (data files),
`setuptools/config/pyprojecttoml.py` (the `[tool.setuptools]` table).

```toml
[build-system]
requires = ["setuptools==84.0.0"]          # add "setuptools-scm" for git versions
build-backend = "setuptools.build_meta"
```

## Finding packages

| Layout | Default (lab) | Key |
| --- | --- | --- |
| src | every package under `src/` found, including namespace packages (`src/acme/core/` with no `acme/__init__.py`) | `[tool.setuptools.packages.find] where = ["src"]` if you must say it |
| flat, one package | found | `include = ["ledger*"]` to be sure |
| flat, two packages | `error: Multiple top-level packages discovered in a flat-layout: ['ledger', 'reports'].` | `[tool.setuptools.packages.find] include = ["ledger*"]` |
| flat, a package with a reserved name | **skipped without a word** | name it in `include` |

The reserved flat-layout names (`FlatLayoutPackageFinder._EXCLUDE`,
84.0.0) include `ci`, `bin`, `doc`, `docs`, `test`, `tests`, `example`,
`examples`, `scripts`, `tools`, `util`, `utils`, `python`, `build`,
`dist`, `venv`, `env`, `requirements`, `tasks`, `benchmark`,
`benchmarks`, and any name starting with `.` or `_`. Lab: a flat project
with `ledger/` and `tools/` built a wheel with `ledger` only.

## Data files

`*.pyi` and `py.typed` inside a package ship without being named
(`_IMPLICIT_DATA_FILES` in `build_py.py`). Everything else that is not
`.py` is left out of **both** the sdist and the wheel until one of these
names it (lab: `templates/report.html` missing, `FileNotFoundError` once
installed, editable install fine):

```toml
[tool.setuptools.package-data]
invoicer = ["templates/*.html"]            # key: the package's dotted name
"acme.core" = ["data/*.json"]              # a namespace subpackage
```

or a `MANIFEST.in` line such as `recursive-include
src/invoicer/templates *.html`. With `pyproject.toml` configuration,
`include-package-data` defaults to true (`pyprojecttoml.py`: `setdefault
("include-package-data", True)`), so files `MANIFEST.in` puts in the
sdist also reach the wheel. Both forms passed in the lab. `.gitignore` is
not consulted.

## Version

| Source | Configuration | Lab |
| --- | --- | --- |
| static | `[project] version = "0.4.0"` | `0.4.0` |
| an attribute | `dynamic = ["version"]`, `[tool.setuptools.dynamic] version = { attr = "ledger.__version__" }` | `0.2.0` |
| git tags | `requires = ["setuptools", "setuptools-scm"]`, `dynamic = ["version"]`, `[tool.setuptools_scm]` | tag `v2.3.0`: `2.3.0` |
| git tags, written to a file | `[tool.setuptools_scm] version_file = "src/ledger/_version.py"` | the wheel has `ledger/_version.py` with `__version__ = version = '2.3.0'`; ignore the file in git |

## Metadata warnings

| Warning (lab) | Write instead |
| --- | --- |
| ``SetuptoolsDeprecationWarning: `project.license` as a TOML table is deprecated`` | `license = "LicenseRef-Proprietary"` (METADATA: `License-Expression`) |
| `warning: sdist: standard file not found: should have one of README, README.rst, README.txt, README.md` | a `README.md` and `readme = "README.md"` |

## Build leftovers

setuptools writes `<name>.egg-info/` next to the package (`src/` or the
root) when uv builds the sdist (lab); the wheel itself is built from the
unpacked sdist elsewhere. Keep `*.egg-info/` out of git, and delete it if
an old file seems to come back.

## Messages and meanings

| Message or sign | Meaning |
| --- | --- |
| `Multiple top-level packages discovered in a flat-layout` | name the package in `packages.find` `include` |
| a folder named `utils` or `tools` missing from the wheel | reserved flat-layout name |
| a data file missing from the sdist and wheel | not in `package-data` or `MANIFEST.in` |
| `Generator: setuptools (84.0.0)` in `WHEEL` | the version that built it |
