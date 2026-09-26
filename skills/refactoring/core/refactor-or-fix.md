# A bug found during a refactoring

**Verdict you produce:** the finding, where it stays until it is
handled, and the commit that keeps it out of the refactoring.

```
finding:  <path:line: what is wrong, and the requirement it breaks>
evidence: <an input, today's output, the output a fix would give>
pinned:   <test or probe line that records today's behaviour, with a comment naming the finding | not pinned: <why>>
handled:  <reported, not fixed | fixed in its own commit <hash>, after the refactoring, as asked>
verdict finding: <reported | fixed separately | stopped: the step cannot keep the bug>
```

A refactoring commit that also fixes a bug cannot be reviewed: when a
test changes, nobody can tell which half caused it, and a revert of the
refactoring takes the fix away too. So the step keeps the bug exactly as
it is, and the bug becomes a finding.

## Steps

1. **Stop editing** when you see it. Finish or undo the current step
   first; do not fold the fix into it.
2. **Write the evidence.** An input, what the code returns now, and what
   the requirement (a comment, a docstring, the ask, a spec) says it
   should return. In the lab, a checkout said "10 items or more: 5% off"
   and checked `items > 10`: ten items at 5.00 cost 50.00.
3. **Work out what a fix would change**, by running it, not by
   reasoning. In the lab, `>=` made ten items cost 52.40, not less:
   the discount took the subtotal under 50.00, so shipping of 4.90 was
   added. A fix can move money in either direction; that is for the
   person to decide.
4. **Pin today's behaviour** if the refactoring's steps touch that code:
   a characterization test or a probe line for the input, with a comment
   that names the finding, so a later fix changes that line on purpose:

   ```python
   def test_characterize_ten_items_get_no_bulk_discount():
       # Pinned as it is today. Finding: the price list says "10 items or more",
       # the code gives the discount from 11. A fix changes this test on purpose.
       assert order_total([{"price": "5.00", "qty": 10}], {}) == Decimal("50.00")
   ```

   In the lab this test passed on the code, failed with `>=`
   (`assert Decimal('52.40') == Decimal('50.00')`), and kept passing
   after the discount lines were extracted into their own function.
5. **Carry on with the refactoring.** The extraction commit keeps
   `items > BULK_THRESHOLD`; its body says so.
6. **Report the finding** under *Findings*, with the evidence. If the
   person asked for the fix too, or asks now, fix it after the
   refactoring, in its own commit, through the debugging skill's
   `core/loop.md` and `core/prove-the-fix.md`: the pinned test is changed
   on purpose in that commit, and it failed before the fix.

## When the step cannot keep the bug

Sometimes the bug is in the very structure being changed (two copies of
a rule that disagree, and the step merges them). Then merging is a
behaviour change: stop the step, report both behaviours with inputs, and
ask which one is right. Do not pick one inside a refactoring.

## Never

- Never fix a bug in a refactoring commit, however small or obvious.
- Never describe an extraction or a move as fixing anything.
- Never change a characterization test to the fixed value in the
  refactoring; that is the fix's commit.
