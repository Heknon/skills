# Worked example: a red step undone

Kind: Step (split module), step 4 of 6. Outputs from a lab run on
Python 3.12.14, pytest 9.1.1, ruff 0.16.9, mypy 2.3.1, git 2.43.0,
commands run in PowerShell 7.5 on Linux.

## Where the work stood

Splitting `app/reports.py` (`steps/split-module.md`). Three steps were
green and committed:

```
7245155 Move orders and totals to app.reports.orders
1682c7f Move money formatting to app.reports.money
0451629 Turn app.reports into a package
```

Step 4 moves `now()` and `stamp_header()` to `app/reports/clock.py`.
The reference list for it was made from the module alone: the two
definitions, the call inside `stamp_header`, the `__all__` entry and the
re-export in `__init__.py`. The search over the whole repository
(`core/every-reference.md` step 2) was skipped.

## The step goes red

```
All checks passed!                                   (ruff)
FAILED tests/test_reports.py::test_stamp_header_uses_clock - AssertionError: ...
FAILED tests/test_reports.py::test_render_text - AssertionError: assert 'Dail...
2 failed, 3 passed in 0.05s
E             - X - generated 2026-03-02 09:30 UTC
E             + X - generated 2026-09-26 06:31 UTC
```

The real time came through: the patch did not reach `stamp_header`.

## Undo, do not patch forward

The tempting fixes are all patching forward: a `now` in `__init__.py`
that `clock.py` calls back into (a circular import), or changing the
tests' expected header to the real time. Instead, the step is undone:

```powershell
git stash push --include-untracked -m "red: move the clock to app.reports.clock"
git status --porcelain          # nothing: clean at 7245155
git stash show --include-untracked --stat 'stash@{0}'
```

```
 app/reports/__init__.py | 13 +------------
 app/reports/clock.py    | 11 +++++++++++
 2 files changed, 12 insertions(+), 12 deletions(-)
```

(`uv.lock`, untracked in this sandbox, went into the stash on the first
try; it was added to `.git/info/exclude` and the step stashed again.)

## Read why, then redo

The first failure says the header used the real clock, so the test's
patch replaced a name `stamp_header` no longer reads. `stamp_header`
now looks up `now` in `app.reports.clock`; `mock.patch("app.reports.now")`
replaces the name in `app.reports` only (pytest's `core/mocking.md`:
patch where the name is used). The skipped search shows the two patch
targets:

```powershell
git grep -n -w -I now -- '*.py'
```

```
app/reports/__init__.py:19:    "now",
app/reports/__init__.py:32:def now() -> datetime:
app/reports/__init__.py:33:    return datetime.now(timezone.utc)
app/reports/__init__.py:37:    return f"{title} - generated {now():%Y-%m-%d %H:%M} UTC"
tests/test_reports.py:31:    with mock.patch("app.reports.now", return_value=FIXED):
tests/test_reports.py:36:    with mock.patch("app.reports.now", return_value=FIXED):
```

(run at `7245155`, before the step).

Both go on the list: they are references to the moved name, not
expectations. The redo is the same step with them: `git stash pop`
brings the attempt back, the two targets become
`mock.patch("app.reports.clock.now", ...)`, and every check runs:

```
5 passed in 0.04s
All checks passed!
Success: no issues found in 9 source files
import_all: 8 ok, 0 failed, 0 skipped
```

Public names since the start lost only names `app.reports` had
imported (`Decimal`, `ROUND_HALF_UP`, `dataclass`, `datetime`, `field`,
`timezone`) and gained the new submodules. Commit:
`4ee7d44 Move the clock and header to app.reports.clock`, with the body
"Structure only. The tests patch now() where stamp_header uses it."

## What to take from it

- A red step is information: here it named a missed reference. The
  answer to it is the reference on the list and the step done again
  whole, not a change to what the tests check.
- The reference list comes from a search of the whole repository
  before the edit (`core/every-reference.md`), never from the module
  being changed: here six lines, two of them in the tests.
- Other teams' tests that patch `app.reports.now` would miss the same
  way; that goes under *Not checked* in the answer, because a shim
  cannot keep a patch working.
