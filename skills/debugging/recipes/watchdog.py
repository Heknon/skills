"""Run a Python script or module; if it is still running after SECONDS,
print the stack of every thread to stderr and stop it.

Works the same on Windows and Linux: it uses
faulthandler.dump_traceback_later, which needs no signals.

Usage (from the project root, so the project imports as it normally does):
    uv run python watchdog.py SECONDS script.py [args...]
    uv run python watchdog.py SECONDS -m package.module [args...]

What you see when it fires:
    Timeout (0:00:10)!
    Thread 0x... (most recent call first):
      File "...", line N in function
    ...
and the exit code is 1. A run that ends in time keeps its own exit code.
Nothing is printed by the watchdog itself when the run ends in time.
"""
import faulthandler
import os
import runpy
import sys


def main():
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    seconds = float(sys.argv[1])
    target = sys.argv[2:]
    # Import the project from the current folder, as `python -m` would.
    sys.path.insert(0, os.getcwd())
    faulthandler.dump_traceback_later(seconds, exit=True)
    if target[0] == "-m":
        sys.argv = target[1:]
        runpy.run_module(target[1], run_name="__main__", alter_sys=True)
    else:
        sys.argv = target
        runpy.run_path(target[0], run_name="__main__")
    faulthandler.cancel_dump_traceback_later()
    return 0


if __name__ == "__main__":
    sys.exit(main())
