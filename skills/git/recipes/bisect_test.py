"""A test script for `git bisect run`. Copy it OUTSIDE the repository
(bisect checks out old commits, which may delete or change files inside
it), edit IMPORTS and check(), then from the repository's top folder:

    git bisect start <bad> <good>
    git bisect run uv run --no-project python ../bisect_test.py
    git bisect log
    git bisect reset

Exit codes, which git reads (source: builtin/bisect.c, 2.43.0):
    0        good: the behaviour is right at this commit
    1        bad: the behaviour is wrong
    125      skip: this commit cannot be tested (does not import, does not build)
    128+     aborts the whole bisect; never use

The lab's sandbox had seven commits that could not import the module;
a script that exited 1 for them made bisect blame the wrong commit.
"""
import os
import sys

sys.path.insert(0, os.getcwd())  # the checked-out code, not this script's folder

IMPORTS = ["shop.money"]  # what must import for the commit to be testable


def check():
    """Return True when the behaviour is right. Edit this."""
    from shop.money import to_cents
    return str(to_cents("0.125")) == "0.13"


def main():
    for name in IMPORTS:
        try:
            __import__(name)
        except Exception as exc:  # any failure to import: untestable
            print(f"skip: cannot import {name}: {exc!r}")
            sys.exit(125)
    try:
        ok = check()
    except Exception as exc:  # the behaviour raised: bad
        print(f"bad: {exc!r}")
        sys.exit(1)
    print("good" if ok else "bad")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
