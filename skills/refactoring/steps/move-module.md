# Move or rename a module

Give a module file a new name or a new package, keeping the old import
path working when anything outside may use it. Splitting one module
into several is `split-module.md`.

## Preconditions

- Every reference to the module path is listed (`core/every-reference.md`
  step 1: dotted, file path, relative imports, `from app import helpers`,
  `import ... as`), including `python -m app.helpers` in docs, CI and
  scripts, patch targets, coverage settings and config files.
- The shim decision is made (`core/public-surface.md`).

## Mechanics

1. Move the file with git, so the move is recorded as one:

   ```powershell
   git mv app/export_tool.py app/tools/export.py
   ```

   The target folder must exist and be a package (`__init__.py`) if the
   project uses them. In the lab `git status --short` showed
   `R  app/export_tool.py -> app/tools/export.py`.
2. If a shim is needed, create a new file at the old path that
   re-exports every public name explicitly, and keeps a `__main__` block
   if the old module had one:

   ```python
   from app.tools.export import main as main

   if __name__ == "__main__":
       main()
   ```

   Without that block, `python -m app.export_tool` ran the shim, printed
   nothing and exited 0 (lab). After the shim is added, `git status`
   shows the old file modified and the new one added, and
   `git log --follow -- app/tools/export.py` still listed the commit
   before the move (lab, git 2.43.0).
3. Change imports, patch targets, `python -m` lines and config in this
   repository to the new path.
4. Search again for the old path; checks with `import_all.py` over the
   package, configs and scripts; commit: "Move export_tool to
   app.tools.export".

## Traps

| Trap | What happens |
| --- | --- |
| a shim written as `from app.tools.export import *` | skips names starting with `_` and anything left out of the new module's `__all__`: `ImportError: cannot import name 'load'`; seniority's change check reports it as `removed or renamed` (`reference/change-check.md`). List names explicitly |
| an old `app/reports.py` left beside a new package `app/reports/` | the package wins and the file is ignored without a word (lab: `app.reports.__file__` was `app/reports/__init__.py`); delete the file with `git mv` or `git rm` in the same step |
| a case-only rename (`Reports.py` to `reports.py`) | on Windows the file system ignores case but Python does not: its finder compares the names in the folder listing exactly unless `PYTHONCASEOK` is set (source: `importlib/_bootstrap_external.py`, 3.12), so `import reports` does not find `Reports.py`. Rename with `git mv`, which records it (git's `reference/windows.md`); `not run on Windows` |
| pickled objects of a class in the module | stored data names the old module path; keep the shim (`core/public-surface.md`) |

## Probe inputs

Import every public name through the old path and the new one, and run
`python -m` on the old path if it had a `__main__` block.

**Done when:** both paths import the same objects (or every caller moved
and nothing outside uses the old path), and import-all and the checks
are green.
