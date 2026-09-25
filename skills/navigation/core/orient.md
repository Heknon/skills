# Orient

**Verdict you produce:** a short map of the repository: what it is, how it
starts, how it is built and tested, and its top folders, each line with
the file that shows it.

```
what: <one line, from the README or pyproject description>
starts: <command> (<file:line that defines it>)
tests: <command> (<file that configures it>)
build or install: <command> (<file>)
environment: <how the interpreter and packages are set up> (<file>)
folders: <folder> - <what is in it>, one line each for the top level
```

## Steps

1. **List the top level** with `list_directory`. Do not open anything yet.
2. **Read the project files that exist**, in this order, and only these:
   `pyproject.toml`, `setup.cfg`, `setup.py`, `README*`, `requirements*.txt`,
   `uv.lock` or `poetry.lock` (only their first lines), `.python-version`,
   `Dockerfile`, `docker-compose*.yml`, `Makefile`, `justfile`, `tasks.py`,
   `noxfile.py`, `tox.ini`, `pytest.ini`, `conftest.py` at the root, and
   `.github/workflows/*.yml` or other CI files.
3. **Find how it starts** with `python/entry-points.md`. There may be
   several: a web app, a worker, a command line tool. List each.
4. **Find how tests run.** The test command in CI is the most reliable,
   because it is the one that is run. Then pytest settings in
   `pyproject.toml` under `[tool.pytest.ini_options]`, or `pytest.ini`,
   `setup.cfg` `[tool:pytest]`, `tox.ini`.
5. **Find the environment** with `python/environment.md`, only as far as
   naming the tool: uv, poetry, pip with a venv, conda.
6. **Name the top folders.** One line each, from the folder's
   `__init__.py` docstring, README, or the names of the files in it. Mark
   the package folder (the one the imports start from), and whether the
   layout is `src/<package>/` or `<package>/` at the root.

## Never

- Never open source files one by one to "get a feel". Orientation comes
  from the project files; source is read only when a question needs it.
- Never state a command that no file shows. If none does, write the
  command you would try, marked `not in any file`.

## Stop and ask

- There is no project file at all and no README. Say what you found and
  ask what the code is for.
