"""Reproduction of one bug, as a script that answers with its exit code.

Copy this file next to the project (outside it when used with
`git bisect run`, so checking out old commits cannot touch it), rename
it repro_<bug>.py, and change only the three marked parts.

Exit codes, the ones `git bisect run` understands:
    0    the bug is absent: the expected result came back
    1    the bug is present: the wrong result, or the bug's own exception
    125  this version cannot be tested: the code does not import, or it
         failed in a different way than the bug (bisect skips it)

Run it:
    uv run python repro_<bug>.py
    uv run python repro_<bug>.py; $LASTEXITCODE      # PowerShell
"""
import os
import sys
import traceback

# The project is imported from the current folder (run this from the
# project root, as `git bisect run` does). Without this line a script kept
# outside the project cannot import it, and every commit reports 125.
sys.path.insert(0, os.getcwd())

# 1. CHANGE: one line that says what the bug is, as it was reported.
BUG = "to_kg(2.5) returns 1.133; 2.5 lb is 1.134 kg to the gram"

# 2. CHANGE: the exception that IS the bug, or None if the bug is a wrong
#    value. Example: KeyError for "KeyError: 'region' in report.py".
BUG_EXCEPTION = None


def run_case():
    """3. CHANGE: call the code exactly as the failing case does.

    Return (got, expected). Import the project here, not at the top, so a
    version that does not import is reported as 125, not as the bug.
    """
    from units.mass import to_kg

    return to_kg(2.5), 1.134


def main():
    try:
        got, expected = run_case()
    except ImportError as exc:
        print(f"SKIP (125): cannot import: {exc!r}", file=sys.stderr)
        return 125
    except SyntaxError as exc:
        print(f"SKIP (125): syntax error: {exc!r}", file=sys.stderr)
        return 125
    except Exception as exc:
        if BUG_EXCEPTION is not None and isinstance(exc, BUG_EXCEPTION):
            print(f"BAD (1): {BUG}: raised {exc!r}")
            return 1
        traceback.print_exc()
        print(f"SKIP (125): failed differently from the bug: {exc!r}", file=sys.stderr)
        return 125
    if got == expected:
        print(f"GOOD (0): got {got!r}")
        return 0
    print(f"BAD (1): {BUG}: expected {expected!r}, got {got!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
