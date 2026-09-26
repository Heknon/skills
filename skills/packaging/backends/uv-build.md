# uv_build

uv's own build backend, verified with uv 0.12.19 and uv_build 0.12.19.
Recipe: `recipes/uv-build/`. Used here for pure-Python packages only
(compiled extensions are out of this skill's scope). It is what `uv init
--package` and `uv init --lib` write on 0.12.19:

```toml
[build-system]
requires = ["uv_build>=0.12.19,<0.13.0"]
build-backend = "uv_build"
```

(`uv init --build-backend hatch` writes `requires = ["hatchling"]`;
`--build-backend setuptools` writes `requires = ["setuptools>=61"]`.)

## No mirror needed, usually

`uv build` and `uv sync` use the copy of uv_build built into uv when the
`requires` range holds the running uv, and fetch nothing (lab: built with
a mirror that had no uv_build). With a range that does not hold it, the
build still ran but warned:

```
warning: `build_system.requires = ["uv-build>=0.11,<0.12"]` does not contain the current uv version 0.12.19
```

`uv build --force-pep517`, pip, and any other frontend fetch uv_build
from the index (lab, mirror without it: `Because uv-build was not found in
the package registry`). The mirror carries uv_build wheels per platform
(`...-py3-none-manylinux_2_17_x86_64...whl`, `...-py3-none-win_amd64.whl`).

## Which files

The module must be at `src/<name with - as _>/__init__.py`; otherwise:

```
error: Failed to build `<path>`
  cause: Expected a Python module at: src/acme_report/__init__.py
```

| Need | `[tool.uv.build-backend]` key (lab result) |
| --- | --- |
| a module with another name | `module-name = "report"` |
| a flat layout | `module-root = ""` (module found at `ledger/__init__.py`) |
| a namespace package | `module-name = "acme.core"`; an `__init__.py` in `src/acme` fails: `For namespace packages, __init__.py[i] is not allowed in parent directory: src/acme` |
| tests or other files in the sdist | `source-include = ["tests/**"]` |

What ships by default (lab): the wheel has every file inside the module
folder, `py.typed` and data included, whatever `.gitignore` says; the
sdist has the module, `pyproject.toml` and the readme, **not `tests/`**.
The sdist's `pyproject.toml` is rewritten without comments, and the
original is kept beside it as `pyproject.toml.orig`.

## Keys are not checked

An unknown key in `[tool.uv.build-backend]` is ignored with no warning
(lab: `nonsense-key = 1` built fine). A misspelled `module_name` is
therefore silent, and the build then fails with `Expected a Python module
at`. A wrong type is caught:

```
module-root = 5
              ^
invalid type: integer `5`, expected path string
```

## Messages and meanings

| Message or sign | Meaning |
| --- | --- |
| `Expected a Python module at: src/<name>/__init__.py` | set `module-name`, or check its spelling |
| `does not contain the current uv version` | the `requires` range and the running uv disagree; builds still use the built-in copy |
| `Generator: uv 0.12.19` in `WHEEL` | built by uv_build |
