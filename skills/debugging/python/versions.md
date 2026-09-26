# What a debugger sees change: 3.12, 3.13, 3.14

Check first: `uv run python -VV`. Every row was run in the lab on
3.12.14, 3.13.15 and 3.14.7 (Linux, uv-installed interpreters), except
where a row says otherwise.

| Topic | 3.12 | 3.13 | 3.14 |
| --- | --- | --- | --- |
| markers under a failing call | `^^^^` under the whole expression | `~~~~^^^^`: `~` for the callee, `^` for the arguments | as 3.13 |
| a statement over several lines, in a frame | shown on one line | `...<2 lines>...` in place of the middle lines | as 3.13 |
| a frame whose whole line failed | markers shown | no marker line (*lab:* `log = open(...)` had none) | as 3.13 |
| coloured tracebacks | never | on a terminal; `PYTHON_COLORS=1` forces escape codes even into a pipe, and wins over `NO_COLOR` (*lab*); `PYTHON_COLORS=0` turns them off | as 3.13 |
| `100 // 0` message | `integer division or modulo by zero` | `integer division or modulo by zero` | `division by zero` |
| JSON with a trailing comma | `Expecting property name enclosed in double quotes` | `Illegal trailing comma before end of object` | as 3.13 |
| `a, b = [1, 2, 3]` | `too many values to unpack (expected 2)` | as 3.12 | `... (expected 2, got 3)` |
| `[1].index(2)` | `2 is not in list` | as 3.12 | `list.index(x): x not in list` |
| a circular import between two top-level scripts | `... from partially initialized module 'a' (most likely due to a circular import)` | `... from 'a' (consider renaming '.../a.py' if it has the same name as a library you intended to import)`; inside a package, all three say circular | as 3.13 |
| a local file shadows a standard library module | `module 'json' has no attribute 'loads'` | adds `(consider renaming '.../json.py' since it has the same name as the standard library module named 'json' ...)` | as 3.13 |
| `breakpoint()` stops at | the line **after** it (`bp.py(5)`) | the `breakpoint()` line itself (`bp.py(4)`) | as 3.13 |
| end of input at a `(Pdb)` prompt from `breakpoint()` | `bdb.BdbQuit` traceback, exit 1 | same | prints `Quitting pdb will kill the process. Quit anyway? [y/n]`, then exit 1 |
| `quit` in post-mortem under `python -m pdb` | restarts the program (`Post mortem debugger finished. The ... will be restarted`) and waits at its first line | exits | exits |
| attach pdb to a running process | no | no | `python -m pdb -p <pid>` (*lab*, Linux) |
| list asyncio tasks of a running process | no | no | `python -m asyncio ps <pid>`, `pstree <pid>` (*lab*, Linux) |
| `faulthandler` dump | `Thread 0x...` | `Thread 0x...` | `Thread 0x... [name]`, and `Current thread's C stack trace` after a fatal error |
| main thread waiting in `join`, in a dump | `_wait_for_tstate_lock` then `join` | `join` | `join` |

The traceback text itself (the `Traceback (most recent call last):`
header, `File ... line ... in ...`, the chain lines, the exception
group borders) is the same on all three (*lab*).

## 3.15: UTF-8 by default

Checked on 3.15.0rc2, a release candidate, with a CP1252 locale: UTF-8
mode was on by default (`sys.flags.utf8_mode` 1, and `open()` without
`encoding` read UTF-8 correctly), and `PYTHONUTF8=0` brought back the
`UnicodeDecodeError`. On 3.12 to 3.14 it is off unless set
(`python/encoding.md`). Code that must run on both still passes
`encoding=` explicitly.

## Not covered

3.11 and older, and free-threaded builds (`3.14t`), were not run.
