# Worked example: a commit refused by a hook

Kinds: Hook blocked. Outputs from a lab run on pre-commit 4.6.2 with
ruff 0.16.9, hooks as in `recipes/pre-commit-project/`.

## The ask

> I've staged my rounding fix in src/cart/totals.py. Commit it with the
> message 'Fix rounding in cart totals'.

## Steps

1. **Commit as asked, and read the refusal** (`pre-commit/blocked.md`):
   ```
   > git commit -m "Fix rounding in cart totals"
   ruff check...............................................................Failed
   - hook id: ruff-check
   - exit code: 1

   F841 Local variable `debug_before` is assigned to but never used
     --> src/cart/totals.py:10:5
   ...
   ruff format..............................................................Passed
   ```
   Case 1, a finding; nothing was changed on disk.
2. **Read the line.** `debug_before = subtotal` is a leftover from
   debugging, read by nothing. Removing it changes no behaviour
   (`ruff rule F841`: the fix is unsafe only because comments on the
   line would be dropped; there are none).
3. **Fix, re-stage, commit again with the same message**:
   ```
   > git add src/cart/totals.py
   > git commit -m "Fix rounding in cart totals"
   ruff check...............................................................Passed
   ruff format..............................................................Passed
   [main 729b0fb] Fix rounding in cart totals
    1 file changed, 7 insertions(+), 2 deletions(-)
   ```

## The same ask, when the formatter changes files

Staging two hand-formatted modules gave:

```
ruff check...............................................................Failed
E701 Multiple statements on one line (colon)
 --> src/cart/shipping.py:2:22
ruff format..............................................................Failed
- hook id: ruff-format
- files were modified by this hook

2 files reformatted
```

`git status` showed `AM` for both. `git diff` showed formatting only,
and the reformat had split the `if ...: return` line that `E701`
reported. `git add` of both files and one more commit: both hooks
`Passed`.

## The answer (first case)

```
## Result
Committed 729b0fb "Fix rounding in cart totals". The first attempt was
refused by the ruff-check hook: F841, `debug_before = subtotal` in
cart_total() was never used. I removed that line (no behaviour change),
staged the file again and committed. No hooks were skipped.

## Checked
- git commit: ruff check Passed, ruff format Passed.

## Not checked
- The tests; the hooks do not run them. `uv run --no-sync pytest` is the
  next check if you want it.
```
