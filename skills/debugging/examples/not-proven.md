# Worked example: a fix and a test that proved nothing

Kinds: Fix (checking someone else's). Outputs are from a lab run on
Python 3.12.14, pytest 9.1.1 and git 2.43.0 in a copy of the
`not-proven` sandbox.

## The ask

> I fixed BUG-88 in the last commit and added a test. Can you confirm
> it's fixed so I can close the ticket?

BUG-88: "A line of 1 x 2.675 is invoiced as 2.67 ... it must be 2.68."

## Steps

1. **Read what the commit changed** (`git show HEAD -- billing/total.py`):

   ```
   -    return round(quantity * unit_price, 2)
   +    amount = Decimal(quantity * unit_price)
   +    return float(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
   ```

   and a test, `line_total(1, 10.005) == 10.01`.
2. **Run the tests**: `2 passed in 0.01s`. This shows the tests pass,
   not that the bug is gone.
3. **Revert only the fix and run them again** (`core/prove-the-fix.md`):

   ```
   $ git restore --source=HEAD~1 -- billing/total.py
   $ uv run pytest -q
   2 passed in 0.01s
   $ git restore -- billing/total.py
   ```

   The new test passes without the fix: it cannot tell fixed from broken.
   (`round(10.005, 2)` already gives `10.01`.)
4. **Run the ticket's own case** with the fix in place:

   ```
   $ uv run python -c "from billing.total import line_total; print(line_total(1, 2.675))"
   2.67
   ```

   The bug is still there. Why, in one probe:

   ```
   $ uv run python -c "from decimal import Decimal; print(Decimal(2.675)); print(Decimal(str(2.675)))"
   2.67499999999999982236431605997495353221893310546875
   2.675
   ```

   `Decimal(quantity * unit_price)` is built from the float, which is
   already just below 2.675, so rounding half up still goes down.
5. **Write the test from the ticket first**, and see it fail:

   ```python
   def test_bug_88_half_cent_rounds_up():
       assert line_total(1, 2.675) == 2.68
   ```

   `FAILED tests/test_total.py::test_bug_88_half_cent_rounds_up - assert 2.67 == ...`
6. **Fix**: `amount = Decimal(str(quantity)) * Decimal(str(unit_price))`.
7. **Prove**: with the fix, `3 passed`; with it stashed (the commit's
   version), `1 failed, 2 passed`; with the version before the commit,
   `1 failed, 2 passed`. Restored: `3 passed`.

## The answer

```
## Cause
The commit builds the Decimal from the float product
(Decimal(quantity * unit_price)). 2.675 as a float is
2.67499999999999982236..., so ROUND_HALF_UP still gives 2.67. The added
test (10.005 -> 10.01) passes with or without the commit, so it could
not show this.

## Reproduction
uv run python -c "from billing.total import line_total; print(line_total(1, 2.675))"
-> 2.67 with the commit in place.

## Fix
billing/total.py: Decimal(str(quantity)) * Decimal(str(unit_price)).
Added tests/test_total.py::test_bug_88_half_cent_rounds_up (the ticket's
case).

## Proof
With the fix: 3 passed. Without it (the commit's version): 1 failed,
assert 2.67 == 2.68. Before the commit: the same failure. Restored:
3 passed.

## Result
The ticket was not fixed by the last commit; it is fixed now, uncommitted.

## Checked
The runs above.

## Not checked
Other amounts than 2.675 and 10.005; quantities that are not whole.

## Done when
The ticket's case gives 2.68: observed at step 7.

## Not done
Closing the ticket and committing: yours to do.

## Unverified
none

## Decided for you
Kept test_line_total_rounds_half_up although it cannot fail; it is
harmless, and removing it was not asked.
```
