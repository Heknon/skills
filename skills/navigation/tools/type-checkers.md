# Type checkers: ty, mypy, Pyright

**What it decides:** how to get a type from a checker, offline, from the
right environment. Output below was captured with ty 0.0.84, mypy 2.3.1
and Pyright 1.1.414; read the installed version with `ty version`,
`mypy --version`, `pyright --version`, and expect wording to move a
little between versions.

## Ask for one type with `reveal_type`

Do not edit project code to do it, and do not create other files such as
an annotated copy of the module. Write one probe file, `nav_probe.py`, in
the project folder, check it, read the answer, delete it. Say in the
answer that it was deleted.

```python
# nav_probe.py, in the project folder; delete it afterwards
from app.rows import parse_rows

reveal_type(parse_rows)
reveal_type(parse_rows([]))
```

`reveal_type` needs no import for the checkers. ty adds a warning that it
was not imported; ignore it. Never run the probe file with Python: at
runtime `reveal_type` without an import is an error.

## Point the checker at the project's environment

This matters. With the wrong environment, imports of installed packages
come back unresolved, or resolve to a different version.

| Checker | Finds the project's `.venv` by itself | Otherwise pass |
| --- | --- | --- |
| ty | yes, a `.venv` in the project folder, or the active virtual environment | `--python .venv` (a folder or an interpreter path) |
| mypy | no: it uses the interpreter it is installed in | `--python-executable .venv\Scripts\python.exe` |
| Pyright | no: it uses `python` on `PATH` | `--pythonpath .venv\Scripts\python.exe` |

## Commands and what they print

When a checker is installed in the project's environment, run it through
uv: `uv run --no-sync ty check ...`. When it is installed on its own, as
a uv tool or on `PATH`, call it by name as below.

```powershell
ty check nav_probe.py --output-format concise
mypy nav_probe.py --python-executable .venv\Scripts\python.exe
pyright nav_probe.py --pythonpath .venv\Scripts\python.exe
```

| Checker | The line to read |
| --- | --- |
| ty | `nav_probe.py:4:13: info[revealed-type] Revealed type: ` followed by the type in backticks |
| mypy | `nav_probe.py:4: note: Revealed type is "<type>"` |
| Pyright | `nav_probe.py:4:13 - information: Type of "parse_rows" is "<type>"` |

Copy the whole line into the answer.

## When the checker cannot see a package

| Message | Meaning | Do |
| --- | --- | --- |
| mypy `Cannot find implementation or library stub for module named "x"  [import-not-found]` | not installed in the environment mypy uses | pass `--python-executable` |
| mypy `Library stubs not installed for "x"  [import-untyped]` | installed, but it has no types | add `--follow-untyped-imports`; installing stubs is not possible air gapped |
| Pyright `Import "x" could not be resolved (reportMissingImports)` | not in the environment Pyright uses | pass `--pythonpath` |
| ty ``error[unresolved-import] Cannot resolve imported module `x` `` | not in the environment ty found | pass `--python` |

To see which environment Pyright used, add `--verbose`: it prints
`Search paths:`. ty prints its Python version with `-v`.

These flags answer one probe. Settings that fix missing imports for good
are the linting skill's (`mypy/stubs.md`, `pyright/config.md`).

## Unannotated functions

For the return type of a function with no annotations, use Pyright: it
infers it from the body. ty prints `Unknown` and mypy prints `Any` for
the same call, meaning only that there is no annotation.

## Which one to use

Any of the three answers "what type is this". Use the one the project
configures (`[tool.mypy]`, `[tool.pyright]`, `[tool.ty]` in
`pyproject.toml`, or `mypy.ini`, `pyrightconfig.json`, `ty.toml`),
because its settings match the project. If none is configured, ty is the
fastest and finds the environment by itself. They disagree on some
inferred types (`python/types.md`); when the difference matters, run two.
