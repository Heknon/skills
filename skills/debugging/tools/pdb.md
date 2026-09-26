# pdb without a keyboard

**What it decides:** which pdb forms end on their own in a terminal
tool, and which wait for the keyboard until the tool gives up.

An agent cannot type at a `(Pdb)` prompt. Whether a prompt waits
depends on stdin: at end of input, pdb quits; with stdin open and
silent, it waits forever. How Zed's terminal tool connects stdin was not
checked (not run in Zed); assume it is open and silent. So only the
forms marked **ends** in the "stdin open" column may be used.

## What the lab showed

Each form ran on 3.12.14, 3.13.15 and 3.14.7 with a time limit of 8 s,
once with stdin at end of input (`< /dev/null`) and once with stdin
open and silent (a pipe nobody writes to). **waits** means the time
limit stopped it.

| Form | stdin at end of input | stdin open, silent |
| --- | --- | --- |
| a script that reaches `breakpoint()` | quits: exit 1 with `bdb.BdbQuit` (3.14: prints `Quitting pdb will kill the process. Quit anyway? [y/n]`, exit 1) | **waits** |
| the same with `PYTHONBREAKPOINT=0` | runs through, exit 0 | **ends**: runs through, exit 0 |
| `python -m pdb script.py` | quits at the first line, exit 0, **the script never ran** | **waits** |
| `python -m pdb -c continue boom.py`, and the script raises | post-mortem prompt, then exit 0: the error's exit code is lost | **waits** |
| `-c "break boom.py:2" -c continue -c "p a, b" -c quit` | ends | **ends**, exit 0 |
| the same without `-c quit` | | **waits** |
| `-c continue -c "p a, b" -c quit`, and the script raises (post-mortem) | | 3.12: **waits** (`quit` restarts the program); 3.13, 3.14: ends |
| the same with `-c quit -c quit` | | **ends** on all three |
| `-c` commands, and the code reaches its own `breakpoint()` | | **waits**: `breakpoint()` starts a new debugger that does not see the `-c` commands |
| commands piped in, one `c` per stop | ends when the input ends; exit 0 | not applicable |
| commands piped in that run out before the program ends | exit 1 (`BdbQuit`) at the next stop | not applicable |
| `pytest --pdb` with a failing test | exit 2 | **waits** |
| `breakpoint()` in code under `pytest` | the test fails with `bdb.BdbQuit` | **waits**; with `PYTHONBREAKPOINT=0`, passes |
| `input()` | `EOFError`, exit 1 | **waits** |
| 3.14 `python -m pdb -p <pid>`, commands piped in, ending without `c` | | detaches at end of input, exit 0; the target keeps running |
| the same with `c` in the commands | | **waits** |

## The forms to use

1. **Before running anything, disable `breakpoint()`** if the code or
   its tests might contain one (search for `breakpoint(` and
   `set_trace`):

   ```powershell
   $env:PYTHONBREAKPOINT = "0"
   uv run python report.py
   Remove-Item Env:PYTHONBREAKPOINT
   ```

2. **Stop at a line, print, and quit**: pdb's own `break` command, a
   condition if the line runs often, and `quit` twice at the end:

   ```powershell
   $env:PYTHONBREAKPOINT = "0"
   uv run python -m pdb -c "break report.py:14, amount < 0" -c continue -c "p row" -c quit -c quit report.py
   ```

   *lab (3.12, 3.13, 3.14, stdin open):*

   ```
   Breakpoint 1 at /home/user/dbg/sb/leftover-breakpoint/report.py:14
   {'date': '2026-03-09', 'customer': 'cobalt', 'amount': '-40.00'}
   ```

   If the break is never hit, the program runs to the end, prints `The
   program finished and will be restarted`, and the `quit` ends it
   (*lab*: exit 0). The second `quit` covers 3.12's restart after a
   post-mortem.
3. **After an exception**, prefer `recipes/locals_on_error.py`: it
   prints the traceback and the local variables of every project frame,
   with no prompt at all. With pdb: `-c continue -c "p <expr>" -c quit
   -c quit`, and remember that `python -m pdb` exits 0 even when the
   script raised.
4. **Piped commands** (*lab: PowerShell 7.4 on Linux*, not run on
   Windows): the pipe ends, so pdb ends:

   ```powershell
   "p row`nc`n" | uv run python report.py
   ```

   Give one `c` for every stop the program will reach; if they run out,
   the run ends with `BdbQuit`. `$null | uv run python report.py` gives
   end of input at once (*lab:* `BdbQuit`, exit 1).

## Commands that print

`p <expr>` a value, `w` the stack (where), `a` the current function's
arguments (*lab:* `a = 1`, `b = 2`), each used in the lab through `-c`.
`-c help` lists every command, among them `pp`, `l`, `display` and
`tbreak`; read `-c "help pp"` before using one not run here.

## Never

- Never run code that may reach `breakpoint()`, `pdb.set_trace()`,
  `input()` or `pytest --pdb` without one of the forms above.
- Never use `c` without a later stop or `quit` in a `-c` sequence.
- Never trust the exit code of a `python -m pdb` run as the script's.
- Never leave `breakpoint()` in the code: it is a probe
  (`core/inspect.md`).
