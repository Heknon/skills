# Tool: asking a command-line tool about itself

**Verdict you produce:** the tool's own output line that answers the
question, with the tool's version and the path of the binary that
printed it.

```
tool:     <name> <version> at <path>   (<command that showed the path>)
asked:    <command>
answered: <the line it printed>
```

What a checker's rule or error *means* for the code is the linting
skill's; this procedure only gets the tool's own words, from the right
binary.

## The binary that runs is the one to ask

The project's tools are installed in its environment and run with
`uv run`. A `ruff`, `mypy` or `git` found first on `PATH` may be another
install and another version. Lab (eval `wrong-ruff`): ruff 0.6.9 was first
on `PATH`, the project had ruff 0.16.9.

```
> ruff rule RUF059
error: invalid value 'RUF059' for '[RULE]'

For more information, try '--help'.
> uv run --no-sync ruff rule RUF059
# unused-unpacked-variable (RUF059)

Derived from the **Ruff-specific rules** linter.
```

The bare command's answer was wrong for this project.

## Steps

1. **Find what the project runs.** Tools listed in `pyproject.toml`
   (`[dependency-groups]`, `[project.optional-dependencies]`) run as
   `uv run --no-sync <tool>`. Ask which file that is:

   ```powershell
   uv run --no-sync python -c "import shutil; print(shutil.which('ruff'))"
   uv run --no-sync ruff --version
   ```

   *Lab*: `/home/user/od-lab/wrong-ruff/.venv/bin/ruff` and `ruff 0.16.9`
   (Windows: `.venv\Scripts\ruff.exe`).

2. **Find what a bare command would run**, when the person or a script
   uses one: `Get-Command ruff -All` lists every `ruff` on `PATH`, first
   one wins (PowerShell; not run on Windows). Global tools that uv
   installs live in the folder `uv tool dir --bin` prints (*lab*:
   `/root/.local/bin`). Say when the two differ.

3. **Ask the tool**, with the command from `tools/cli-help.md` that does
   not open a pager. Prefer the form that prints one thing (`ruff rule
   <code>`, `ruff config <key>`) over a whole help page.

4. **For a setting's effect, ask the tool what it resolved**, not the
   config file: `uv run --no-sync ruff check --show-settings <file>` printed
   `Settings path: ".../wrong-ruff/pyproject.toml"` and, under
   `linter.rules.enabled`, `unused-unpacked-variable (RUF059),`. So RUF059
   was already on in ruff 0.16.9 without being selected: its default
   rule set had 413 rules (`--show-settings --isolated`), and `ruff check`
   reported ``RUF059 Unpacked variable `last` is never used`` (*lab*).

5. **Report** the line, the version and the path. When the bare command
   and the project's disagree, give both.

## Verdicts for tools

A tool's account of itself is the "help" kind of evidence: the verdict is
`confirmed from help only (<tool> <version> at <path>)`. When you also ran
the tool and saw the behaviour (a `ruff check` finding, an exit code), add
that run under `Evidence:`. When the help has no such flag or rule:
`not found (<tool> <version>: <commands tried>)`.

## Never

- Never ask a bare `ruff`, `mypy`, `pyright`, `ty` or `pytest` about a
  project that runs them through uv.
- Never quote a flag from memory; print the help of the binary that runs
  and quote it.
- Never reinstall or remove the tool on `PATH` to make the answers agree;
  say which is which.
