# Review the tests

**Verdict you produce:** per test, whether it can fail and what it
misses, and the changed behaviour that no test checks.

```
tests/test_notices.py::test_overdue_notice_is_sent   cannot fail for content: asserts only mailer.send.called
broken on purpose: days = 0 -> 1 passed; wrong recipient -> 1 passed; restored, git status clean
untested:  send_overdue_notice: the recipient, the subject, the date and the number of days
verdict tests: <every changed behaviour has a test that can fail | gaps: <list>>
```

Whether a test can fail is the pytest skill's rule (invariant 2,
`core/write-test.md`: step 5 and "Signs a test cannot fail"). This file
applies it in a review, without writing the tests.

## Steps

1. **List the changed behaviour**: `review_diff.py defs` for changed
   contracts, and each new function, branch and error path in the diff.
2. **Map each to a test**: search the tests for the name
   (`uv run --no-sync pytest --co -q -k <name>`), and read the tests the
   diff adds or changes. Write `untested` where none calls it.
3. **Read each new or changed test** with `checklists/tests.md`: does it
   assert on something it set up itself, a mock's return value, the
   default only, a fake that cannot express the bug?
4. **Show a doubtful test cannot fail.** Only with a clean tree
   (`git status --short` empty of tracked changes):
   - break the code the test claims to check, in the smallest way
     (return 0, flip the condition);
   - run that test file;
   - put the file back with `git restore <path>` (git: that command
     destroys uncommitted work in the file, which here is only your
     break) and check `git status --short` is clean again.
   *lab:* with the day count set to 0, and again with the wrong
   recipient, the notice test still gave `1 passed`; after `git
   restore`, `git status --short` printed nothing.
5. **Say what a good test would check**, as text: the inputs and the
   expected values from the requirement, not from the code's output.
   The review does not write the test (CR4).

## Ranking

A test that cannot fail is minor on its own; it is major when it is the
only test of behaviour that moves money or data (`checklists/tests.md`,
TST1). Missing tests for changed behaviour: `checklists/tests.md`,
TST2.

## Never

- Never leave the code broken: the last step of every break is
  `git restore` and a clean `git status`.
- Never count a test as covering a function because it imports it.
