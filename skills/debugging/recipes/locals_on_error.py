"""Run a Python script or module; if it raises, print the traceback and
then the local variables of every frame in the project's own code,
for every exception in a chain or an ExceptionGroup.

A post-mortem that needs no keyboard: nothing waits for input, so it is
safe in a terminal tool. Values are shortened to one line each.

Usage (from the project root):
    uv run python locals_on_error.py script.py [args...]
    uv run python locals_on_error.py -m package.module [args...]

Frames from the standard library, site-packages and this file are
skipped: only files under the current folder are shown. The exit code is
1 when the target raised, otherwise the target's own.
"""
import os
import reprlib
import runpy
import sys
import traceback

short = reprlib.Repr()
short.maxstring = 120
short.maxother = 120
short.maxlist = short.maxdict = short.maxtuple = short.maxset = 10


def in_project(filename):
    if filename.startswith("<"):  # <frozen runpy>, <string>
        return False
    path = os.path.abspath(filename)
    root = os.getcwd() + os.sep
    return (
        path.startswith(root)
        and path != os.path.abspath(__file__)
        and os.sep + ".venv" + os.sep not in path
        and os.sep + "site-packages" + os.sep not in path
    )


def print_locals(exc, seen=None):
    """Locals for exc, for the exceptions it was chained from (first), and
    for each exception inside an ExceptionGroup."""
    seen = set() if seen is None else seen
    if exc is None or id(exc) in seen:
        return
    seen.add(id(exc))
    print_locals(exc.__cause__ or exc.__context__, seen)
    print(f"\nLocals for {type(exc).__name__}: {short.repr(str(exc))}", file=sys.stderr)
    tb = exc.__traceback__
    while tb is not None:
        frame = tb.tb_frame
        code = frame.f_code
        if in_project(code.co_filename) and code.co_name != "<module>":
            where = f"{os.path.relpath(code.co_filename)}:{tb.tb_lineno} in {code.co_name}"
            print(f"  {where}", file=sys.stderr)
            for name, value in frame.f_locals.items():
                print(f"    {name} = {short.repr(value)}", file=sys.stderr)
        tb = tb.tb_next
    for inner in getattr(exc, "exceptions", ()):
        print_locals(inner, seen)


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    target = sys.argv[1:]
    sys.path.insert(0, os.getcwd())
    try:
        if target[0] == "-m":
            sys.argv = target[1:]
            runpy.run_module(target[1], run_name="__main__", alter_sys=True)
        else:
            sys.argv = target
            runpy.run_path(target[0], run_name="__main__")
    except SystemExit:
        raise
    except BaseException as exc:
        traceback.print_exc()
        print_locals(exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
