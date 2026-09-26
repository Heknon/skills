# Characterization tests

**Verdict you produce:** tests that pass on the code as it is, fail when
it is broken, and record its oddities on purpose.

```
tests:      <node ids>
inputs:     <what each covers: branches, boundaries, the empty case>
oddities:   <each pinned value that looks wrong, with its comment>
fails when: <each deliberate break, the failing node, then restored>
verdict pin: <pinned | not pinned: <what could not be reached, and the seam it needs>>
```

A characterization test does not say what the code should do. It says
what it does now, so a refactoring can prove it still does. Writing the
test beside the other tests, named `test_characterize_*`, keeps it
visible; the pytest skill owns how to write tests in general
(`skills/pytest/core/write-test.md`), and this file adds only what is
different: the expected value comes from the code.

## Steps

1. **Find what the code reads besides its arguments**: the clock, files,
   the environment, the network, random numbers, module globals. Each
   needs a seam before a test can fix it (`legacy/seams.md`). Add the
   smallest seam first, as its own step, and show the program's output is
   unchanged by it.
2. **Choose inputs** that go through every branch you will touch: each
   `if` both ways, each boundary (a threshold's value, one below, one
   above), the empty input, and the input that gives the odd result.
3. **Get the real output**: run the code on each input and copy what it
   prints or returns. Never write the expected value from reading the
   code. In the lab, an expected list written from reading
   `build_report` had two lines in the wrong order; the code sorts by
   total, not by days:

   ```
   E         At index 2 diff: 'Globex        2      710.00 EUR   10 days' != 'Umbrella      1       99.99 EUR    3 days'
   ```

   To print a value for a fixed date without a test yet:

   ```powershell
   uv run --no-sync python -c "import datetime, billing.report as r; r._today = lambda: datetime.date(2026, 3, 2); print(repr(r.build_report('data/invoices.csv').splitlines()))"
   ```

   `pytest -vv` (without `-q`, which cancels one `v`) shows the full
   diff of a failing assert; lines marked `+` are the left side of the
   `==`, the code's value when written `assert actual == expected`.
4. **Pin oddities with a comment** that names them as findings, so a
   later fix changes that line on purpose (`core/refactor-or-fix.md`):

   ```python
   # Finding: GBP with no rate is added as EUR at 1:1. Pinned as it is today.
   "Umbrella      1       99.99 EUR    3 days",
   ```

5. **Make it fail.** Break the code in two or three ways that the
   refactoring could plausibly break it (a condition, a filter, a
   conversion), run the tests, see them fail, restore. In the lab, four
   breaks of `build_report` each failed the three characterization tests
   (`2 failed, 1 passed` each), while a test asserting only that the text
   starts with `Overdue on` and contains `EUR` passed all of them.
6. **Commit the tests on their own**, before the first refactoring step.

## Breaking and restoring quickly

Python reuses a `.pyc` file when the source has the same size and the
same modification second. In the lab, a break that changed `60` to `61`
and a restore within the same second left the old bytecode in use: the
restored code failed three runs in a row until the file was touched.
Before a break-and-restore loop, set `$env:PYTHONDONTWRITEBYTECODE = "1"`
and delete the package's `__pycache__` folders (they are rebuilt), or
make each break change the line's length.

## Signs a characterization test cannot fail

- It asserts on something it set up itself, or on a mock.
- It asserts that the output contains a word, not what the output is.
- Its inputs never reach the branch the refactoring changes.
- It passed with the code broken in step 5.

## Never

- Never fix an oddity while pinning it.
- Never pin through a mock of the code under test.
- Never leave a characterization test that reads the real clock or a
  shared file.
