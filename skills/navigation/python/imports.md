# Python imports: from an import line to a file

**What it decides:** which file an import loads.

Python looks for a module in the folders of `sys.path`, in order, and
takes the first match. The order, for a normal run:

1. the folder of the script being run, or the current directory for
   `python -m` and for the interactive interpreter;
2. the folders in the `PYTHONPATH` environment variable;
3. the standard library;
4. `site-packages` of the interpreter that runs, which holds installed
   packages, and entries added by `.pth` files there (editable installs
   work this way).

To see the real list: `tools/terminal-probes.md`, "the search path".

## From an import line to a path

| Import line | Look for |
| --- | --- |
| `import a.b.c` | `a/b/c.py` or `a/b/c/__init__.py` under a `sys.path` folder |
| `from a.b import c` | first the name `c` defined or imported in `a/b/__init__.py` (or `a/b.py`); only if there is none, the submodule `a/b/c.py` or `a/b/c/__init__.py` |
| `from . import c` in `a/b/x.py` | first the name `c` in `a/b/__init__.py`; if there is none, the submodule `a/b/c.py` |
| `from .c import d` in `a/b/x.py` | the name `d` in `a/b/c.py` or `a/b/c/__init__.py` |
| `from ..c import d` in `a/b/x.py` | the name `d` in `a/c.py` or `a/c/__init__.py` |
| `from a.b import *` | every public name of `a.b`, or exactly the names in its `__all__` if it has one |
| `import a.b as z` then `z.d` | the name `d` in module `a.b` |
| `from a.b import c as d` | uses of `d` in this file are `c` from `a.b` |

Dots in a relative import count packages up from the file's own package:
one dot is the file's package, two dots its parent.

## Layouts

- **`src` layout**: code in `src/<package>/`. The import `<package>` is
  found only if the project is installed (often editable) or `src` is on
  `sys.path`. Imports never contain `src`.
- **Flat layout**: `<package>/` at the repository root, found when the
  root is the current directory or installed.
- **No `__init__.py`**: a namespace package. Several folders can
  contribute to one package name; search every `sys.path` folder.

## Where resolution goes wrong

1. **Shadowing.** A project file named like a standard or installed module
   (`json.py`, `logging.py`, `requests.py`, `types.py`, `test.py`) is
   found first when its folder is first on `sys.path`, and hides the real
   one.
2. **Two copies.** The package exists in the repository and installed in
   `site-packages` as a non-editable copy. The installed one wins unless
   the repository folder comes first on `sys.path`. See `core/resolve.md`.
3. **Re-exports.** `__init__.py` files import names from submodules so
   users can write `from pkg import Client`. The definition is in the
   submodule; follow the chain (`core/locate.md` step 5).
4. **Conditional imports.** `try: import ujson as json` / `except
   ImportError: import json`. Which one runs depends on what is installed:
   ask the interpreter.
5. **`if TYPE_CHECKING:` imports.** They exist only for type checkers;
   at runtime the name is not imported there.
6. **Imports inside functions.** Search the whole file, not only the top.
7. **Dynamic imports.** `importlib.import_module("a." + name)`,
   `__import__`: see `python/dynamic.md`.

## Confirm

When it matters, confirm with the interpreter the project uses
(`tools/terminal-probes.md`, "where a module comes from"). The rules above
tell you where to look; the interpreter tells you what actually loads.
