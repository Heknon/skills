# Is the test wrong, or the code?

**Verdict you produce:** one of four, with the evidence.

```
verdict:  <code is wrong | test is wrong | environment is wrong | cannot tell: ask>
because:  <the requirement, docstring, commit, issue or behaviour that decides it>
change:   <the change, in the code or in the test, and why that side>
```

A failing test is a disagreement between two claims about behaviour. Only
one side can change, and changing the test is the easy one, which is why
it is the dangerous one.

## Questions, in order

1. **Is it the environment?** Does the failure name a missing module, a
   path, a network host, a timezone, a locale, an environment variable,
   the order of tests, or does it pass alone and fail with others
   (`core/flaky-and-slow.md`)? Then fix the environment or the isolation,
   not the assertion.
2. **What does the requirement say?** Look for the source of truth, in
   this order: the person's ask, an issue or ticket, a docstring or
   documentation, the function's name and type hints, a commit message
   that introduced the behaviour (`git log -L` on the function), the
   other tests of the same code. Write down which one decides.
3. **Did the test pass before?** `git log` on the test and the code:
   which changed last? A test that passed until a code change points at
   the code; a test that never passed points at either.
4. **Does the expected value make sense on its own?** Compute it by hand
   from the requirement, not from the code's output.

## Verdicts

- **Code is wrong**: fix the code; the test stays exactly as it is. Run
  it: it must now pass, and the rest of the suite must too.
- **Test is wrong**: the test's expectation contradicts the requirement
  you named in question 2. Fix the test, and say which requirement shows
  it was wrong. Then check the new test can fail (`core/write-test.md`,
  step 5).
- **Environment is wrong**: fix the setup, fixture or isolation; say so.
- **Cannot tell**: the requirement is silent and the two sides are both
  plausible. Stop and ask, showing both behaviours.

## Never

- Never copy the code's output into the expected value because "the code
  is the truth". That turns the test into a record of the bug.
- Never add `pytest.skip`, `@pytest.mark.xfail`, a wider tolerance, a
  `try/except`, or delete the assert to reach green, unless the person
  asked for that exact change.
- Never change both the code and the test in one step: then nothing
  shows which one was wrong.
