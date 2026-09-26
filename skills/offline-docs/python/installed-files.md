# Installed files: what a package put on disk

**What it decides:** which files belong to an installed distribution,
which of them run, and where the standard library's source is.

Where the virtual environment and its `site-packages` folder are is
navigation's (`python/environment.md` there). This file starts inside
`site-packages`.

## One distribution in site-packages

Lab, fetchkit 2.0.0 installed by uv 0.12.19 from an index:

```
site-packages/
  fetchkit/                   the import package: __init__.py, _transport.py
  fetchkit-2.0.0.dist-info/
    INSTALLER                 "uv"
    METADATA                  name, version, dependencies, summary, often the README
    RECORD                    every installed file, with its sha256 and size
    REQUESTED                 uv writes it for every package, even a dependency
    WHEEL                     the wheel format and tags
    uv_cache.json             uv's own record
```

Others add `entry_points.txt` (console commands), `licenses/`, `sboms/`
(orjson 3.12.0), `top_level.txt` (PyYAML 6.0.3: `_yaml` and `yaml`) and
`direct_url.json` (editable or direct installs, `core/pin-version.md`).

An editable install puts no code in `site-packages`: ledgerlib 0.1.0,
installed editable by `uv sync`, had only its `.dist-info` and a
`ledgerlib.pth` file holding `/home/user/od-lab/editable/src`, the folder
the code is read from (*lab*).

## RECORD: every file

```powershell
uv pip show --files types-fetchkit
```

```
Files:
  fetchkit-stubs/__init__.pyi
  types_fetchkit-1.6.0.20260101.dist-info/INSTALLER
  ...
```

`RECORD` answers "which package put this file here" and "what did this
package install" without importing anything. The same list is in
`importlib.metadata.files('<dist>')` (`python/metadata.md`).

## Compiled modules

| Platform | Compiled module file (*lab*: read in wheels for both) |
| --- | --- |
| Linux | `main.cpython-312-x86_64-linux-gnu.so`, `orjson.cpython-312-x86_64-linux-gnu.so` |
| Windows | `main.cp312-win_amd64.pyd`, `orjson.cp312-win_amd64.pyd` (from the win_amd64 wheels; not run on Windows) |

When a folder has both `main.py` and a compiled `main` module, the
compiled one is imported: the import system tries extension modules
before source files (`importlib/_bootstrap_external.py:1733-1736` in
3.12.14: `return [extensions, source, bytecode]`). pydantic 1.10.26 ships
both for 25 of its modules; `pydantic.main.__file__` was the `.so`. The
`.py` is the source it was compiled from, from the same wheel
(`core/evidence.md`). A compiled module with no `.py` beside it (orjson)
has no source on the machine: use its stub.

Search `site-packages` with the recipe's `grep`, or read a file with
`lines`: the editor's own search may skip `.venv`, because uv writes a
`.gitignore` holding `*` into it (*lab*; Zed's search was not tested).

## The standard library

```powershell
uv run --no-sync python -c "import sysconfig; print(sysconfig.get_paths()['stdlib'])"
```

Lab: `/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12`
for a uv-managed Python (on Windows the folder is `Lib` under the Python
install; not run on Windows). What the uv-managed 3.12.14 held:

| Item | Present |
| --- | --- |
| the pure-Python modules (`json/`, `urllib/`, `socket.py`, `pydoc.py`, ...) | yes, 33 MB in all |
| `pydoc_data/topics.py` (the language topics for `pydoc`) | yes |
| `idlelib`, `tkinter`, `ensurepip`, `lib2to3`, `venv`, `unittest` | yes |
| `test/` (CPython's own test suite) | **no** |
| `EXTERNALLY-MANAGED` | yes: `This Python installation is managed by uv and should not be modified.` |
| `site-packages/` | pip 26.2.1 only |

Many modules have no file at all: 96 modules are built into the
interpreter (`sys.builtin_module_names`), among them `_socket`, `_json`,
`_collections`, `_datetime` and `math`; `lib-dynload/` held only three
compiled modules. A Python module often imports its speed-up from one of
these, so its source is only a fallback (`python/inspect.md`).

## Never

- Never edit a file in `site-packages` or `Lib` to test an idea.
- Never read a `.pyc` file or a compiled module as if it were source.
