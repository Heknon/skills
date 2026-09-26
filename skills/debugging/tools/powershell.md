# PowerShell for debugging runs

**What it decides:** how to set a variable for one run, capture both
output streams, read the exit code, run a command N times and give a
run a time limit. Every block ran in PowerShell 7.4.6 on Linux in the
lab; none was run on Windows or in Windows PowerShell 5.1.

## Environment variables

```powershell
$env:PYTHONBREAKPOINT = "0"        # set for this shell and what it starts
uv run python report.py
Remove-Item Env:PYTHONBREAKPOINT   # unset; nothing left behind
```

The variables this skill uses:

| Variable | Effect |
| --- | --- |
| `PYTHONBREAKPOINT=0` | `breakpoint()` does nothing (`tools/pdb.md`) |
| `PYTHONUTF8=1` / `0` | UTF-8 mode on or off (`python/encoding.md`) |
| `PYTHONWARNDEFAULTENCODING=1` | warn at every `open()` without `encoding=` |
| `PYTHONFAULTHANDLER=1` | dump stacks on a crash (`tools/faulthandler.md`) |
| `PYTHONASYNCIODEBUG=1` | asyncio debug mode (`python/async.md`) |
| `PYTHONTRACEMALLOC=25` | trace allocations with 25 frames (`tools/tracemalloc.md`) |
| `PYTHONUNBUFFERED=1` | do not hold stdout in a buffer (`core/reproduce.md`) |
| `PYTHON_COLORS=0` | no colour codes in 3.13+ tracebacks (`python/versions.md`) |

Always remove what you set before the answer; a variable left set
changes every later run in that terminal.

## Exit code

`$LASTEXITCODE` holds the exit code of the last native command:

```powershell
uv run python -m sales data/may.csv; "exit $LASTEXITCODE"
```

*lab:* `exit 1` after the `KeyError`; `exit 3` after `sys.exit(3)`.

## Both streams

| Form | *lab* result |
| --- | --- |
| `uv run python app.py *> run.log` | stdout and stderr in the file, plain text |
| `uv run python app.py > run.log 2>&1` | the same |
| `uv run python app.py 2>&1 \| Select-Object -Last 20` | stderr lines become `ErrorRecord` objects and print wrapped in colour codes (`^[[31;1mKeyError: 'region'^[[0m`) |
| `$PSStyle.OutputRendering = "PlainText"` first | the same lines without colour codes |

The stderr line came out before the stdout line printed earlier by the
same program (*lab*): stdout was buffered. Write probes to stderr
(`tools/probes.md`), or read the two streams separately.

## N runs, a time limit, no keyboard

`recipes/run_n.ps1` runs a command N times, each with an empty stdin
and a time limit, stops a run that overruns together with its child
processes, counts failures, and keeps the first failure's output:

```powershell
.\run_n.ps1 -Times 20 -TimeoutSeconds 60 -- uv run python ..\repro_race.py
```

*lab:*

```
run 1: exit 1
run 2: exit 1
2 of 2 failed
first failure kept in /tmp/run_n-first-failure.txt
```

and `$LASTEXITCODE` was 2, the failure count.

With `-TimeoutSeconds 5` on the deadlock sandbox, each run printed
`timed out after 5 s`, and no `python -m sync` process was left
running. On the leftover-breakpoint sandbox the empty stdin made the
`(Pdb)` prompt end at once (`exit 1`) instead of waiting.

Call it from a PowerShell prompt, as above or as `& <path>\run_n.ps1
...`. *lab:* `pwsh -File run_n.ps1 -Times 1 -- ...` failed with
`Parameter cannot be processed because the parameter name '' is
ambiguous`: under `-File`, the `--` is not taken as the end of the
script's parameters. Whether the execution policy lets a `.ps1` run at
all on the team's Windows machines was not checked (not run on
Windows).

`-Times 1` is a single run with a time limit. For a stack dump at the
limit, run the command under `recipes/watchdog.py` inside it.

## Files and text

`Get-Content` and `Set-Content` change bytes: *lab:* `Get-Content |
Set-Content` dropped a UTF-8 byte order mark and turned `\r\n` into
`\n`. When the bytes may matter, copy and cut files with Python in
binary (`core/shrink.md`), and revert files with git
(`core/prove-the-fix.md`).

## Search for probes

In a git repository, `git grep -n -I --untracked DBG` searches tracked
and new files and skips what `.gitignore` excludes; uv's `.venv` holds
its own `.gitignore` with `*` (*lab*), so it is skipped. Outside git:

```powershell
Get-ChildItem -Recurse -Force -Filter *.py | Where-Object FullName -notmatch "[\\/]\.venv[\\/]" | Select-String -Pattern "DBG" -CaseSensitive
```

*lab:* printed only `sales/report.py:5:` and the probe line. Without the
`.venv` filter and `-CaseSensitive` it found 22 lines, 21 of them in
library files under `.venv` (pygments' lexers); `Select-String` ignores
case by default. On Linux `Get-ChildItem` skipped the dot-folder unless
`-Force` was given; whether Windows hides it was not checked (not run on
Windows), so keep the filter.
