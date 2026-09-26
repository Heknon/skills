# import_all.py

**What it decides:** whether every module of a package still imports,
every dotted path to it in config files still resolves, and every
script still finds what it imports. It is the check that sees what the
tests do not run.

Run it from the project's root folder with the project's interpreter:

```powershell
uv run --no-sync python <skill>/tools/import_all.py app --config pyproject.toml --config config/jobs.yaml --scripts tools
```

| Option | Does |
| --- | --- |
| `PACKAGE ...` | top-level import names; every module under each is imported (`pkgutil.walk_packages`), except `__main__` modules, listed as `SKIP ... __main__ runs the program when imported` |
| `--path DIR` | puts a folder on `sys.path` after the current one: `--path src` for a `src` layout that is not installed |
| `--config FILE` | reads the file as text, finds each dotted path that starts with a PACKAGE name, in the forms `app.helpers:parse_date` and `app.users.get_user`, and resolves it; the name of an entry point group (`[project.entry-points."app.parsers"]`) is skipped |
| `--scripts DIR` | imports each `.py` file under a private name if it has an `if __name__ == "__main__":` guard, so its imports run and its program does not; a script without the guard is `SKIP ... run it with --help instead` |

It prints `OK`, `FAIL` with the error, or `SKIP` with the reason, one
line per item, then `import_all: <n> ok, <n> failed, <n> skipped`. Exit
0 when nothing failed, 1 when something did, 2 on a usage error.
Standard library only; lab: Python 3.12.14, flat and `src` layouts.

## What it caught in the lab

```
FAIL config/jobs.yaml: app.users.get_user  AttributeError: module 'app.users' has no attribute 'get_user'
FAIL pyproject.toml: app.helpers:parse_date  AttributeError: module 'app.helpers' has no attribute 'parse_date'
FAIL tools/backfill.py  ImportError: cannot import name 'parse_date' from 'app.helpers' (...)
FAIL config/routes.yaml: events.handlers.on_invoice  AttributeError: module 'events.handlers' has no attribute 'on_invoice'
FAIL app.reports  ImportError: cannot import name 'Order' from partially initialized module 'app.reports' (most likely due to a circular import) (...)
```

In each case the tests passed or could not have run the code.

## Reading a FAIL

- `No module named 'app'` on the package itself: the command ran in the
  wrong folder, or a `src` layout needs `--path src`.
- An error inside a module you did not touch: read it anyway; importing
  runs module-level code, and the step may have changed what it imports.
- A script that does work at import time (no guard) is not imported;
  run it the way the project runs it, with `--help` or a harmless
  argument, and say so under *Checked*.

## Limits

It imports; it does not call. A name reached by `getattr` with a
default, a dispatch key, or a string built at run time is not a dotted
path in a file: the probe covers those (`core/every-reference.md`).
Importing a module runs its top-level code: for a package that connects
to something at import, run it where that is harmless, or not at all.
