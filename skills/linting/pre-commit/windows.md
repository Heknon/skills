# pre-commit and the checkers on Windows

**What it decides:** what differs on Windows with PowerShell and Git for
Windows. The lab was Linux: facts below come from pre-commit 4.6.2's
source or from PowerShell 7.4 on Linux, and each says which. None was
run on Windows; say so when you rely on one.

## How the hook runs (read in `install_uninstall.py`, `hook-tmpl`)

- On Windows, `pre-commit install` writes `#!/bin/sh` as the script's
  first line; git runs it with Git for Windows' shell, which the source
  comment describes as bash in POSIX mode. Not run on Windows.
- `INSTALL_PYTHON` is the Python that ran `install`, such as
  `C:\work\shop\.venv\Scripts\python.exe` when installed with
  `uv run --frozen pre-commit install`. The fallbacks are the same as on
  Linux (`pre-commit/install.md`).
- `PRE_COMMIT_HOME` defaults to `~/.cache/pre-commit`, expanded from the
  user's home, so `%USERPROFILE%\.cache\pre-commit` (read in
  `store.py`).

## Writing `entry`, `files` and `args`

| Rule | Why |
| --- | --- |
| forward slashes in `entry` and `args` paths | `entry` goes through `shlex.split`: `scripts\check_issue_key.py` became `scriptscheck_issue_key.py` (*lab*, on any platform) |
| forward slashes in `files`/`exclude` | pre-commit matches paths with `/`; for `[\\/]` in a regex it warns that it normalises slashes, so `/` is enough |
| `uv run --frozen <tool>`, not a path to `.exe` | executables are found on `PATH` with `PATHEXT` (read in `parse_shebang.py`), so `uv` finds `uv.exe` |
| `require_serial: true` for tools that need one process | on Windows a command line is limited to 2\*\*15 - 2048 characters (read in `xargs.py`), so long file lists are split anyway |

## PowerShell forms

Checked in PowerShell 7.4 on Linux; Windows PowerShell 5.1 passes
quotes to programs differently and was not tried.

```powershell
$env:SKIP = "mypy"; git commit -m "Fix rounding"; Remove-Item Env:SKIP
$env:PIP_INDEX_URL = "https://<mirror>/simple"
uv run --no-sync ruff check --config "lint.per-file-ignores = {'tests/**' = ['S101']}" .
Select-String -Path uv.lock -Pattern '^name = "ruff"' -Context 0,1
```

- Pass folders or files to ruff and mypy, not globs. PowerShell on
  Linux expanded `tests/*.py` itself; quoted, `"tests/**/*.py"` reached
  ruff unexpanded and gave `E902 No such file or directory`. On Windows,
  PowerShell does not expand globs for programs (not run here).
- `$LASTEXITCODE` holds a tool's exit code after it runs.

## Line endings

- ruff's `format.line-ending` defaults to `auto`, keeping each file's
  own ending (`ruff/format.md`).
- `pre-commit-hooks` has `mixed-line-ending` (read in its
  `.pre-commit-hooks.yaml`, 6.0.0), `end-of-file-fixer` and
  `trailing-whitespace-fixer`. Whether git converts endings on checkout
  (`core.autocrlf`, `.gitattributes`) is the git skill's.
