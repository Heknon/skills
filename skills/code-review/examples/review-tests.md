# Worked example: review the tests of a change

Kind: Tests. The outputs are from a lab run on the library service
(pytest 9.1.1, Python 3.12.14, git 2.43.0).

## The ask

> The `notices` branch adds overdue e-mails with a test. Is the test
> good enough?

## Steps

1. **The changed behaviour** (`core/review-tests.md`, step 1). One new
   module, `src/library/notices.py`: `send_overdue_notice(loan, today,
   mailer)` sends one e-mail to `loan.reader_email`, subject `"<title>
   is overdue"`, body with the due date and the number of days late.
2. **The tests that call it**:

   ```
   uv run --no-sync pytest --co -q -k overdue -p no:cacheprovider
   tests/test_notices.py::test_overdue_notice_is_sent
   1/4 tests collected (3 deselected) in 0.31s
   ```

3. **Read it** (`checklists/tests.md`). It builds a `Mock()` mailer,
   calls the function, and asserts `mailer.send.called`. The recipient,
   the subject, the date and the day count are never checked: TST1,
   the test only checks that the mock was called.
4. **Show it cannot fail** (step 4). `git status --short` printed
   nothing first. Then two breaks, one at a time:

   ```
   days = 0 instead of (today - loan.due).days
   uv run --no-sync pytest -q -p no:cacheprovider tests/test_notices.py   -> 1 passed in 0.01s
   the recipient "nobody@example.com" instead of loan.reader_email
   uv run --no-sync pytest -q -p no:cacheprovider tests/test_notices.py   -> 1 passed in 0.01s
   git restore src/library/notices.py
   git status --short                                                     -> (nothing)
   ```

5. **What a test that can fail looks like**, checked outside the
   repository (a file in a temporary folder, deleted after):

   ```
   mailer.send.assert_called_once_with(
       "ann@example.com", "Dune is overdue", "Dune was due on 01 March 2026, 10 days ago."
   )
   ```

   It passed on the branch, and with `days = 0` it failed:
   `AssertionError: expected call not found.` with `Actual: send(...,
   'Dune was due on 01 March 2026, 0 days ago.')`. It goes in the
   answer as text; the review does not add it (CR4).
6. **Rank**: a notice with a wrong day count or recipient is a wrong
   e-mail to a reader, not lost data or money: the test gap is minor
   (`checklists/tests.md`, TST1). Tools: ruff `All checks passed!`,
   mypy `Success`, pytest `4 passed`.

## The answer

```
## Verdict
approve with comments: the code is right as far as it was run; its only test cannot fail on the content (1 minor)

## Findings
[1 minor] tests/test_notices.py:11  TST1  the test asserts only that send was called
  when: the day count or the recipient breaks -> the test still passes (shown: days = 0 and a wrong recipient each gave 1 passed)
  evidence: ran pytest on tests/test_notices.py with each break, then git restore; git status clean
  suggest: mailer.send.assert_called_once_with("ann@example.com", "Dune is overdue",
           "Dune was due on 01 March 2026, 10 days ago.") - checked: fails on days = 0
seen before this change (not in the verdict):
  none

## Checked
- reviewed: notices against main, 2 files added
- uv run --no-sync ruff check .: All checks passed!
- uv run --no-sync mypy: Success: no issues found in 9 source files
- uv run --no-sync pytest -q: 4 passed
- breaks: days = 0 -> 1 passed; wrong recipient -> 1 passed; restored, git status clean
- a stronger assertion, in a temporary folder outside the repository: passed on the branch, failed on days = 0; folder deleted

## Not reviewed
- the date format on a machine with another locale: %B was checked only in the lab's C locale
```
