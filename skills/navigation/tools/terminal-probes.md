# Terminal probes: asking the interpreter

**What it decides:** what the running Python actually loads, where from,
and what a name is, when reading the repository is not enough.

Run every probe with `uv run --no-sync python`, which uses the project's
environment and does not change it (`python/environment.md`). For an
environment uv does not find, use that environment's `python.exe`
directly. In PowerShell, keep the Python code
inside double quotes and use only single quotes within it. Run from the
project folder the program is normally run from, because the current
folder is on the search path.

**Importing runs a module's top-level code.** Most modules only define
things, but some connect to databases, read files or start work when
imported. Prefer the probes marked *no import* when you do not know the
module.

## Where a module comes from (*no import* of the module itself)

```powershell
uv run --no-sync python -c "import importlib.util as u; s = u.find_spec('app.billing'); print(s.origin if s else 'not found')"
```

It prints the file the import would load. For a package it is the
package's `__init__.py`. It does import the parent packages (`app` here).

## Where a module comes from (imports it)

```powershell
uv run --no-sync python -c "import app.billing as m; print(m.__file__)"
```

## Where a name is defined

```powershell
uv run --no-sync python -c "import inspect, app.billing as m; o = m.Client; print(inspect.getsourcefile(o), inspect.getsourcelines(o)[1])"
```

Prints the file and first line of the definition, following any
re-export. Works for functions, classes and methods; for a plain value
such as a constant it fails: locate it by search instead.

## A signature

```powershell
uv run --no-sync python -c "import inspect, app.billing as m; print(inspect.signature(m.charge))"
```

## The search path

```powershell
uv run --no-sync python -c "import sys; print(chr(10).join(sys.path))"
```

`chr(10)` is a newline; it avoids quoting trouble. An empty first line
means the current folder, which is searched first.

## Installed packages

```powershell
uv pip show --files <package>
uv run --no-sync python -c "import importlib.metadata as md; print(md.version('<package>'))"
uv run --no-sync python -c "import importlib.metadata as md; print([e for e in md.entry_points(group='console_scripts') if e.name == '<command>'])"
```

The last one shows which function a command such as `mytool` runs.

## Never

- Never probe with a bare `python`. Use `uv run --no-sync python`.
- Never run the program's main entry point to "see what happens" when
  it may change data or call out. Probe with imports and `inspect`.
