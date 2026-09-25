# Environment

**Verdict you produce:** the interpreter and packages that run this code,
and the command that runs it, each shown by a command and its output.

```
interpreter: <full path> (<command that showed it>)
version: <Python version>
packages from: <folder of site-packages>
project installed as: <editable from path | copy of version v | not installed>
run with: <command>
```

## Steps

1. **Name the tool the project uses**, from its files (`python/environment.md`):
   `uv.lock` means uv, `poetry.lock` means poetry, `environment.yml` means
   conda, `requirements*.txt` with a `.venv` means pip.
2. **Find the interpreter that the project's commands use**, not the one
   `python` happens to mean in your terminal. Commands for each tool are in
   `python/environment.md`.
3. **Ask that interpreter about itself** (`tools/terminal-probes.md`):
   its path, version, `sys.path`, and where the project package is
   imported from.
4. **Check the project package.** Imported from the repository folder:
   the source you read is what runs. Imported from `site-packages`: an
   installed copy runs; compare its version with the repository.
5. **Say how to run things**: `uv run <command>`, or `uv run --no-sync
   <command>` to leave the environment as it is. For an environment uv
   does not find, the interpreter's full path.

## Never

- Never assume `python` in the terminal is the project's interpreter.
  On Windows it may be another install, or the Microsoft Store stub that
  opens the Store instead of running Python.
- Never install packages to make something run without being asked. That
  changes the environment you were asked to describe, and air gapped it
  usually fails anyway.
