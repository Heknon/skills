# Python environments on Windows

**What it decides:** which interpreter and which packages run the
project, and how to call that interpreter.

All commands are for PowerShell in the project folder. Inside a
`python -c "..."` command, use only single quotes in the Python code:
PowerShell may strip double quotes inside a double-quoted argument.

**Use uv for every command, whichever tool manages the project.**
`uv run --no-sync <command>` runs in the project's environment without
changing it; `uv pip list` and `uv pip show <package>` inspect it. In a
uv project it uses the project's `.venv`; outside one, it finds a `.venv`
in the folder. For any other environment, point uv at its interpreter:
`uv pip list --python <path to python.exe>`. Never use a bare `python` or
`pip`.

## Which tool manages it

| File in the project | Tool | Interpreter |
| --- | --- | --- |
| `uv.lock`, or `[tool.uv]` in `pyproject.toml` | uv | `.venv\Scripts\python.exe`, or `uv run python` |
| `poetry.lock` | poetry | `poetry env info --path`, then `<that path>\Scripts\python.exe`; or `poetry run python` |
| `environment.yml` | conda | `conda env list`, then `conda run -n <name> python` |
| `Pipfile.lock` | pipenv | `pipenv --py` |
| `requirements*.txt` and a `.venv` or `venv` folder | pip | `.venv\Scripts\python.exe` |
| none of these | unknown | ask, or look at CI files for how it is installed there |

A virtual environment on Windows keeps its interpreter at
`<venv>\Scripts\python.exe` and its packages at `<venv>\Lib\site-packages`.
(On Linux and macOS: `<venv>/bin/python` and `<venv>/lib/pythonX.Y/site-packages`.)

`.python-version` names the Python version uv and pyenv-win use.

## Which Python is `python`

```powershell
Get-Command python -All | Select-Object Source
py -0p
```

The first line lists every `python` on `PATH`, first one wins. A path
under `...\AppData\Local\Microsoft\WindowsApps\` is the Microsoft Store
stub: it opens the Store instead of running Python. `py -0p` lists every
Python the Windows launcher knows, with paths. `$env:VIRTUAL_ENV` is set
when a virtual environment is activated in this terminal.

## Ask the project's interpreter about itself

```powershell
uv python find
uv run --no-sync python -c "import sys; print(sys.executable); print(sys.version)"
uv pip list
uv pip show <package>
uv pip show --files <package>
```

`uv python find` prints the interpreter the project uses. For a poetry or
conda environment, add `--python <its python.exe>` to the `uv pip`
commands, and run code with that `python.exe` directly.

`uv pip list` shows an `Editable project location` column. `uv pip show` prints `Location:` (where it is installed) and, for an editable
install, `Editable project location:` (the repository folder it points
to). No editable line and a `Location` in `site-packages` means a copy:
editing the repository does not change what runs until it is reinstalled.

More probes, such as where a module is imported from, are in
`tools/terminal-probes.md`.

## Never

- Never use a bare `python` or `pip`. Use `uv run --no-sync` and `uv pip`.
- Never install anything to fix a missing import unless asked. Air gapped it
  fails, and it changes the environment you were describing.
