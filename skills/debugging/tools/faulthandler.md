# faulthandler

**What it decides:** how to get every thread's Python stack from a
process that crashed or stopped moving. Standard library; checked on
3.12.14, 3.13.15 and 3.14.7 (Linux) and in CPython 3.12.14's source for
Windows.

## Turn it on for crashes

| Form | Effect |
| --- | --- |
| `uv run python -X faulthandler app.py` | dump on a fatal error: segfault, abort, bus error, illegal instruction, floating-point exception |
| `$env:PYTHONFAULTHANDLER = "1"` | the same, for every Python started from this shell |
| `uv run python -X dev app.py` | development mode: faulthandler on, asyncio debug on, more warnings (*lab:* `faulthandler.is_enabled()` was `True`) |
| `faulthandler.enable()` in code | the same, from that point |

*lab:* a segfault with it on printed `Fatal Python error: Segmentation
fault` and the frames (`core/crash.md`); with it off, only the shell's
`Segmentation fault` and exit 139.

## Dump after a time limit

```python
import faulthandler, sys
faulthandler.dump_traceback_later(10, exit=True, file=sys.stderr)
```

After 10 s it prints `Timeout (0:00:10)!` and every thread's stack; with
`exit=True` it then ends the process with exit code 1. It needs no
signal, so it is the way on Windows too. `recipes/watchdog.py` wraps a
script or module in it without editing the code. `repeat=True` dumps
every 10 s instead of once (*lab:* three dumps of a busy loop, one a
second). `faulthandler.cancel_dump_traceback_later()` stops it.

## Dump on demand from outside (Linux only)

| Form | *lab* result |
| --- | --- |
| started with `-X faulthandler`, then `kill -ABRT <pid>` | dump of all threads, then the process ends (`Fatal Python error: Aborted`) |
| `timeout 3 python -X faulthandler app.py` (SIGTERM) | **no dump**: SIGTERM is not one of the signals it handles |
| `faulthandler.register(signal.SIGUSR1)` in the code, then `kill -USR1 <pid>` | a dump, and the process keeps running |

On Windows (*read in source*, `Include/internal/pycore_faulthandler.h`,
not run on Windows): `faulthandler.register` does not exist, "because
only SIGSEGV, SIGABRT and SIGILL can be handled by the process". Use
`dump_traceback_later`, or on 3.14 attach with `python -m pdb -p`
(`tools/pdb.md`).

## Reading a dump

```
Timeout (0:00:02)!
Thread 0x00007f9c11cfd6c0 (most recent call first):
  File "deadlock.py", line 18 in audit
  File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/threading.py", line 1012 in run
  ...
Thread 0x00007f9c13325740 (most recent call first):
  File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/threading.py", line 1169 in _wait_for_tstate_lock
  File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/threading.py", line 1149 in join
  File "deadlock.py", line 26 in <module>
  ...
```

(*lab*, 3.12.14; `...` marks lines cut from this copy, among them the
second worker thread.)

- **Most recent call first**: the top frame is where the thread is now,
  the opposite order of a traceback.
- One block per thread. After a crash or a signal, `Current thread`
  marks the thread that received it (*lab:* the main thread, in a
  `SIGUSR1` dump); a timeout dump marks none. 3.14 adds the thread's
  name: `Thread 0x... [audit]`.
- No source lines and no variable values: open the file at each line.
- A dump shows Python frames only. A thread waiting in native code shows
  its last Python frame (the `with lock:` line, `time.sleep(...)`).
- For asyncio it shows the loop, not the tasks (`python/async.md`).

## Never

- Never use `exit=True` in code that stays; the watchdog is a probe.
- Never expect a dump from a plain kill or a terminal tool's time limit.
