# Asking tools about themselves

**What it decides:** which command prints a tool's own documentation in
the terminal, without a pager and without the network.

Run project tools through uv (`core/tool.md`). Versions below are the
lab's (Linux): uv 0.12.19, ruff 0.16.9 (and 0.6.9 where marked), mypy
2.3.1, pyright 1.1.414, ty 0.0.84, git 2.43.0, CPython 3.12.14.

## Pagers wait for a key

In a terminal (a pseudo-terminal, as the lab ran under `script`), these
opened a pager and did not return until killed after 5 seconds (exit
124):

| Blocked | Use instead (returned at once) |
| --- | --- |
| `uv help run` | `uv help --no-pager run` (the long help, 787 lines) or `uv run --help` (the short one, 221 lines) |
| `python -m pydoc json`, `help(len)` | `python/pydoc.md`: `render_doc`, the recipe's `def`, or `TERM=dumb` |
| `python -m pydoc -p 0` | waits at a `server>` prompt; see `python/pydoc.md` |

The same commands piped into another program returned at once, because
the pager is used only when output goes to a terminal. Zed's agent
terminal was not tested; treat it as a terminal.

## uv

| Ask | Command |
| --- | --- |
| version | `uv --version` (`uv 0.12.19 (x86_64-unknown-linux-gnu)`); `uv self version` prints the same |
| a subcommand's options, short | `uv run --help` |
| the long form with `Possible values` | `uv help --no-pager run` |
| where global tools are | `uv tool dir --bin` |
| what is installed | `uv pip list`, `uv pip show <dist>`, `uv pip show --files <dist>` |

## ruff

| Ask | Command | Lab output, ruff 0.16.9 |
| --- | --- | --- |
| version | `uv run --no-sync ruff --version` | `ruff 0.16.9` |
| one rule | `uv run --no-sync ruff rule RUF059` | Markdown: `# unused-unpacked-variable (RUF059)`, what it does, why, an example, options |
| every rule, for searching | `uv run --no-sync ruff rule --all --output-format json` | a JSON list of 970 rules with `code`, `name`, `linter`, `summary`, `preview` |
| one setting | `uv run --no-sync ruff config lint.extend-select` | the description, `Default value: []`, `Type: list[RuleSelector]`, an example |
| the settings in a table | `uv run --no-sync ruff config lint` | the key names, one per line |
| rule prefixes | `uv run --no-sync ruff linter` | ` AIR Airflow`, ` ERA eradicate`, ... |
| what is in effect for a file | `uv run --no-sync ruff check --show-settings <file>` | `Settings path:` and every resolved setting |
| the defaults, ignoring config | add `--isolated` | |

An older ruff rejects what it does not know. ruff 0.6.9:
`ruff rule RUF059` printed `error: invalid value 'RUF059' for '[RULE]'`
and `ruff check --select RUF059 app` printed `error: invalid value
'RUF059' for '--select <RULE_CODE>'`, both exit 2.

## mypy, pyright, ty

| Tool | Version | Help | Explain a rule |
| --- | --- | --- | --- |
| mypy | `mypy --version`: `mypy 2.3.1 (compiled: yes)` | `mypy --help` (320 lines) | none built in; the error code is in brackets on each error line |
| pyright | `pyright --version`: `pyright 1.1.414` | `pyright --help`: `Usage: pyright [options] files...` | none built in |
| ty | `ty --version`: `ty 0.0.84` | `ty --help`, `ty check --help` | `ty explain rule unresolved-import`: `# unresolved-import`, `Default level: error`, what it does |

Each through `uv run --no-sync` when the project has it. The pyright
package from the index carries pyright's JavaScript and a typeshed copy
in its wheel (`pyright/dist/dist/typeshed-fallback`, listed in its
`RECORD`); it needs Node.js to run, which is the linting skill's matter.

## git

| Ask | Command | Lab |
| --- | --- | --- |
| a command's options | `git log -h` | printed `usage: git log [<options>] [<revision-range>] [[--] <path>...]` and returned |
| all commands | `git help -a` | printed the list |
| concept guides | `git help -g` | printed the list (`everyday`, `glossary`, ...) |
| the full manual page | `git help log` | needs a man page viewer; the lab machine had none. Git for Windows opens the HTML page in a browser instead (not run on Windows) |

Use `-h`: it always prints in the terminal.

## Python and PowerShell

| Ask | Command |
| --- | --- |
| a module's documentation | `python/pydoc.md` |
| the language (keywords, formatting, special methods) | `uv run --no-sync python -m pydoc FORMATTING` printed `Format String Syntax`; `-m pydoc topics` lists topic names such as `ASSIGNMENT`, `EXCEPTIONS`, `SPECIALMETHODS`. Soft keywords such as `match` have no page in 3.12.14 (`No Python documentation found for 'match'.`) |
| a PowerShell cmdlet | `Get-Help <cmdlet>`; without `Update-Help`, which needs a network or a copied help folder, it shows only the syntax (not run on Windows) |
| which program a name runs | `Get-Command <name> -All` (not run on Windows) |

There is no `man` on Windows.
