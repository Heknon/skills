# Crash

**Verdict you produce:** how the process ended, the dump, and the frame
it names.

```
exit:   <the exit code, and what it means: signal, Windows exception code, os._exit, killed>
dump:   <the faulthandler lines, copied: "Fatal Python error: Segmentation fault" and the frames>
frame:  <the last project frame in the dump, and the native call it made>
cause:  <the value passed to native code, or the resource that ran out>
```

A crash is a process that ended without a Python traceback. Either
native code failed (a C extension, `ctypes`), something outside killed
it (memory limit, a signal), or code called `os._exit`. Python's own
exceptions never look like this.

## Steps

1. **Read the exit code** right after the run (`$LASTEXITCODE`):

   | Exit code | Meaning |
   | --- | --- |
   | 1 | an uncaught Python exception, `sys.exit(1)`, or a `faulthandler` timeout with `exit=True`; a traceback or dump should be above |
   | 139 (Linux shell), -11 (Python's `subprocess`) | segmentation fault: invalid memory access in native code (*lab*) |
   | 134, -6 | abort, as from `os.abort()` (*lab*) |
   | 137, -9 | killed, often by a memory limit (the out-of-memory killer, a container limit); deployment's `kubernetes/debugging.md` for pods |
   | 124 | the Linux `timeout` command stopped it: a hang (`core/hang.md`) |
   | `0xC0000005` (3221225477) | Windows access violation, the Windows segfault: CPython's own test suite expects this code (read in `Lib/test/test_faulthandler.py`, 3.12.14; not run on Windows) |
   | 0 with work missing | not a crash: a thread died or a future's exception was never read (`python/threads.md`) |

2. **Run it again with the fault handler on**, printing to stderr:

   ```powershell
   uv run python -X faulthandler -m app
   ```

   or `$env:PYTHONFAULTHANDLER = "1"`. *lab (3.12.14):*

   ```
   Fatal Python error: Segmentation fault

   Current thread 0x00007fa04260c740 (most recent call first):
     File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/ctypes/__init__.py", line 528 in string_at
     File "/home/user/dbg/crash/segv.py", line 5 in read_header
     File "/home/user/dbg/crash/segv.py", line 9 in <module>
   ```

   The dump lists frames most recent first, the opposite of a traceback.
   3.14 adds the thread's name and a `Current thread's C stack trace`
   (`python/versions.md`).
3. **Find the last project frame** in the dump and the native call it
   made (here `read_header` calling `ctypes.string_at`). Print, to
   stderr, the values it passed just before the call; stdout printed
   before a crash is lost when it goes to a file or pipe
   (`core/reproduce.md`).
4. **Check what the native function expects** (its documentation or
   source, the offline-docs skill): a pointer, a length, a buffer that
   must stay alive, one thread at a time.
5. **Fix the value or the call**, and prove it with the same command
   (`core/prove-the-fix.md`).

## Windows

Not run on Windows; read in CPython 3.12.14's source:

- `faulthandler` catches Windows exceptions and prints
  `Windows fatal exception: access violation` (or `stack overflow`,
  `int divide by zero`, others) before the frames
  (`Modules/faulthandler.c`).
- A fault inside a function called **through ctypes** is caught by
  ctypes on Windows and raised as a Python error, `OSError: exception:
  access violation reading 0x...`, instead of crashing
  (`Modules/_ctypes/callproc.c`). So `ctypes.string_at(0)`, which
  crashed the Linux lab, is expected to raise on Windows; a real crash
  there comes from native code not called through ctypes.
- `faulthandler.register` does not exist on Windows, and there is no
  `SIGABRT` to send from outside: use `watchdog.py` for hangs.

## Never

- Never retry a crash hoping for a traceback: turn the fault handler on.
- Never wrap native code in `try/except` to "catch" a segfault; Python
  cannot catch it on Linux.
- Never read an exit code of 0 as success when the output is short.
