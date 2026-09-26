# Entry points: add or fix a console script

**Verdict you produce:** the line, and the command run from a clean venv.

```
line:     [project.scripts] <command> = "<module>:<function>"
wheel:    entry_points.txt: <command> = <module>:<function>
ran:      <command> <args>  ->  <its output>, exit 0, from a fresh venv outside the checkout
```

## The line

```toml
[project.scripts]
acme-report = "acme_report.cli:main"
```

- The left side is the command. The right side is `module:callable`: an
  import path, a colon, and a function that takes **no arguments**.
- At install time the installer writes a script that does, exactly
  (uv 0.12.19, read from the generated file):
  ```python
  from acme_report.cli import main
  ...
  sys.exit(main())
  ```
  So whatever `main()` returns becomes the exit status: `None` is 0, an
  integer is that code, and any other object is **printed** and exits 1.
- On Windows the command is `acme-report.exe` in `.venv\Scripts\`; on
  Linux `acme-report` in `.venv/bin/` (only Linux was run in the lab).

## What goes wrong

| Line | What happens (lab) | Fix |
| --- | --- | --- |
| `acme = "acme.cli"` (a module, no function) | hatchling builds it; uv refuses to install: `The wheel is invalid: invalid console script: 'acme.cli'` | name the function: `acme.cli:main` |
| `acme = "acme.cli:make_cli"` (a factory that returns a click group) | the script prints `<Group cli>` and exits 1: `sys.exit` got the group | name the function that runs it: `acme.cli:main`, where `main()` calls `make_cli()()` |
| `acme = "acme.cli:main"` where `main(argv)` needs an argument | `TypeError` at start, `missing 1 required positional argument` | give the argument a default (`argv=None`) or point at a wrapper |
| the module is not in the wheel | `ModuleNotFoundError` from the script's `from ... import` line | `core/layout.md`: the wheel has no package |

A click command or group object itself (`@click.command() def main`) is a
correct target: calling it parses `sys.argv` and runs.

## Steps

1. Read the line in `pyproject.toml`, and what was really installed: the
   wheel's `entry_points.txt` (`inspect_dist.py` prints it under `entry
   points:`), or the generated script (on Linux `.venv/bin/acme` is text;
   on Windows `.venv\Scripts\acme.exe` is a launcher, not run on Windows).
2. Open the named function. Does it take no arguments, and does it run
   the program rather than build and return it?
3. Change the line, not the function, unless the function is wrong for
   every caller. Tests that call a factory keep working.
4. **Reinstall before you run it.** Scripts are written at install time.
   `uv run acme ...` notices the changed `pyproject.toml` and rebuilds
   the project (lab: `Built acme-tools`, then `hello`); a venv made from a
   wheel needs the new wheel.
5. `core/verify.md`: build, install the wheel in a fresh venv, run the
   command from outside the checkout.

## Other entry points

`[project.entry-points."<group>"]` declares plugins for another package,
such as `[project.entry-points.pytest11] budget = "pytest_budget.plugin"`
(a module is right here: the group decides what the target must be). The
navigation skill owns finding who reads a group; packaging owns declaring
it.

## Never

- Never add `if __name__ == "__main__":` to make a console script work:
  the installed script imports the module, so that block never runs.
- Never test a console script only with `uv run python -m ...`: that is a
  different path from the installed command.
