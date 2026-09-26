# Re-review: match the earlier findings to the fix

**Verdict you produce:** each earlier finding marked, the new findings
from the fix only, and a new verdict.

```
earlier:   review of "Waive late fees with a coupon until it expires" (b8d59a9)
fix:       rebased; range-diff: that commit unchanged (= 44dca5f), one new commit d33909f, +16 -3
[1 blocker] fixed: src/library/fees.py:17 takes now in UTC; fee_after_coupon(150, "SPRING") -> 150, no TypeError
[2 minor]   fixed: tests/test_fees.py:18 test_expired_coupon_waives_nothing
new:       none
verdict re-review: <all fixed, no new findings | open: <numbers> | new: <count>>
```

## Steps

1. **Read the earlier review**: its findings, and the head it reviewed
   (the `reviewed:` line under *Checked*). No hash recorded: find the
   commit by its subject and date in `git log`, and say so.
2. **Get the fix on its own.** If the branch only gained commits:
   `git diff <reviewed head>..HEAD` and `git log <reviewed
   head>..HEAD`. If it was rebased or squashed, that diff also holds
   main's changes; first run

   ```
   git range-diff <reviewed base>..<reviewed head> origin/main..HEAD
   ```

   *lab, git 2.43.0:* after a rebase it printed
   `1:  b8d59a9 = 1:  44dca5f Waive late fees ...` (unchanged) and
   `-:  ------- > 2:  d33909f Compare coupon expiry in UTC ...` (new).
   When a fix was squashed into the reviewed commit it printed `1: <old>
   ! 1: <new>` and a diff of the two patches, each line prefixed twice
   (`-+` a line of the old patch, `++` a line of the new one). Read the
   new commits with `git show`, and a changed one from the range-diff.
3. **Run the tools and tests on the new head** (`core/tools.md`).
4. **Mark each earlier finding**, with the line or test that shows it:

   | Mark | When |
   | --- | --- |
   | fixed | the scenario no longer happens: run it again if it was run before |
   | not fixed | the line is unchanged, or the scenario still happens |
   | disputed | the author replied with a reason; weigh it with evidence, once (seniority: `core/pushback.md`) |
   | moot | the code it was about is gone |

   A finding is fixed when its scenario is gone, not when the line
   changed.
5. **Review the fix diff with the checklists** (`core/checklist.md`),
   and read the callers of anything whose contract the fix changed
   (`core/callers.md`). A fix is new code: the lines next to the fixed
   one change too, and a fix that adds a parameter changes a contract
   (*lab*: the coupon fix added `now: datetime | None = None`; `defs`
   listed it, and its only callers were the tests).
6. **Do not raise fixed findings again**, and do not review untouched
   code again unless the fix changed what it relies on.
7. **New verdict** (`core/verdict.md`) from the open earlier findings
   and the new ones together.

## Never

- Never mark a finding fixed from the commit message.
- Never add findings about lines the first review saw and the fix did
  not touch, unless the first review missed a blocker; then say so
  plainly, as a new finding.
