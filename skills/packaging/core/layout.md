# Layout: src or flat, subpackages, data files

**Verdict you produce:** the tree, and the listing that proves the files
are in both distributions.

```
tree:     <src/acme_report/..., each file that must ship>
backend:  <the key that selects the files, or "default: folder matches the name">
listing:  inspect_dist.py --against <folder>: "every source file is in the distribution"
          (for the sdist and for the wheel)
```

## Which layout

- **New project: src layout** (`src/<import_name>/`). The checkout's copy
  cannot be imported by accident, so tests that pass against an install
  mean something. `uv init --package` and `uv init --lib` make it.
- **Existing flat project: fix, do not convert** unless asked. Moving to
  src changes every path in CI, Dockerfiles and tool configuration.

## What each backend ships by default

Lab, one package with `templates/report.html`, `data/rates.json` and
`py.typed` beside the `.py` files:

| Backend | `.py` files | `py.typed` | other data inside the package | files ignored by `.gitignore` |
| --- | --- | --- | --- | --- |
| hatchling 1.32.4 | yes, if the folder is found | yes | yes | **left out**, even with no `.git` folder |
| setuptools 84.0.0 | yes, if the package is found | yes (built in: `*.pyi`, `py.typed`) | **no**, unless listed in `package-data` or `MANIFEST.in` | not consulted |
| uv_build 0.12.19 | yes, if `src/<module>/__init__.py` exists | yes | yes | not consulted |

Each backend's file (`backends/`) has the keys to change this.

## Found or not found

The backend looks for a folder named after the project, with `-` as `_`:
`acme-report` finds `src/acme_report/` or `acme_report/`. When the folder
has another name:

| Backend | Not found | Tell it |
| --- | --- | --- |
| hatchling | `ValueError: Unable to determine which files to ship inside the wheel` ... `no directory that matches the name of your project (acme_report)` | `[tool.hatch.build.targets.wheel] packages = ["src/report"]` |
| uv_build | `Expected a Python module at: src/acme_report/__init__.py` | `[tool.uv.build-backend] module-name = "report"` |
| setuptools | finds any package under `src/`; in a flat layout, stops on two top-level packages: `Multiple top-level packages discovered in a flat-layout: ['ledger', 'reports']` | `[tool.setuptools.packages.find] include = ["ledger*"]` (flat), `where = ["src"]` (src, found by default) |

**The silent case.** hatchling with `packages = ["report"]` while the
code is in `src/report/` builds a wheel with only `.dist-info` files: no
error, and `inspect_dist.py` prints `PROBLEM: the wheel holds no Python
module`. setuptools in a flat layout silently skips folders it reserves:
`tools`, `utils`, `util`, `scripts`, `tests`, `docs`, `examples`,
`benchmarks` and more (`FlatLayoutPackageFinder._EXCLUDE` in
`setuptools/discovery.py`, 84.0.0). A package named `utils` is never found
until it is named in `include`.

## Namespace packages (`acme.core`, `acme.api`)

The shared folder (`src/acme/`) has no `__init__.py`; each distribution
ships only its own subfolder. Lab, each built and installed together
into one venv, `import acme.core` and `import acme.api` both work:

| Backend | Setting |
| --- | --- |
| hatchling | `[tool.hatch.build.targets.wheel] packages = ["src/acme"]` (the wheel holds `acme/core/...`, no `acme/__init__.py`) |
| uv_build | `[tool.uv.build-backend] module-name = "acme.core"`; an `__init__.py` in `src/acme` stops the build: `For namespace packages, __init__.py[i] is not allowed in parent directory: src/acme` |
| setuptools | nothing: with `src/acme/core/__init__.py` and no `src/acme/__init__.py`, the wheel held `acme/core/...`; package data is keyed by the dotted name, `"acme.core" = ["data/*.json"]` |

## Steps

1. Build: `uv build` (the sdist, then the wheel from it).
2. List both against the package folder:
   `uv run --no-project python <skill>\recipes\tools\inspect_dist.py "dist\*" --against src\acme_report`.
3. For each `MISSING` line, the backend's key from the table above or
   from `backends/`; rebuild; list again.
4. `core/verify.md`: install the wheel in a fresh venv and read the file
   through the package (`importlib.resources.files("acme_report")`).

## Never

- Never fix a missing module with `sys.path`, `PYTHONPATH` or pytest's
  `pythonpath`: they make the checkout importable and hide the wheel.
- Never read a data file with a path relative to the working directory
  or `__file__` of a script outside the package; read it through
  `importlib.resources` so it works from the wheel.
