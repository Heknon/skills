# Worked example: a conflict resolved from the base

Kinds: Orient, Conflict. Copy the order of the steps and the answer's
shape. Outputs are from a lab run of the `both-sides` sandbox on git
2.43.0, with an editor that fails if called.

## The ask

> Finish this merge.

## Steps

1. **Orient** (`core/orient.md`). `git status`:
   ```
   On branch feature/tax
   You have unmerged paths.
     (fix conflicts and run "git commit")
     (use "git merge --abort" to abort the merge)
   ...
   Unmerged paths:
     (use "git add <file>..." to mark resolution)
   	both modified:   pricing.py
   ```
   A merge of main into feature/tax is in progress, one file conflicts.
2. **Show the base** (`core/conflicts.md` step 2).
   `git checkout --conflict=zdiff3 pricing.py`, then read the file:
   ```
   <<<<<<< ours
       return (subtotal - subtotal * discount) * (1 + tax)
   ||||||| base
       return subtotal - subtotal * discount
   =======
       return round(subtotal - subtotal * discount, 2)
   >>>>>>> theirs
   ```
3. **What each side did, and why.** `git diff :1:pricing.py
   :2:pricing.py`: ours added `tax=0` to the signature and multiplied by
   `(1 + tax)`. `git diff :1:pricing.py :3:pricing.py`: theirs wrapped
   the same expression in `round(..., 2)`. `git log --oneline
   --left-right HEAD...MERGE_HEAD -- pricing.py`:
   ```
   > c42ec3f Round order totals to cents
   < e59fbe6 Add a tax rate to the order total
   ```
   Two separate intents; neither side replaces the other. Each side
   brought a test (`tests/test_tax.py`, `tests/test_rounding.py`), so
   taking one side would fail the other's test.
4. **Write both.** The conflict block becomes one line:
   `return round((subtotal - subtotal * discount) * (1 + tax), 2)`.
5. **Check.** `git diff --check` printed nothing (exit 0).
   `uv run --no-project python -m unittest`: `Ran 3 tests` / `OK`.
6. **Conclude.** `git add -- pricing.py`, `git commit --no-edit`:
   `[feature/tax 5a3792d] Merge branch 'main' into feature/tax`.
   `git status`: `nothing to commit, working tree clean`. The editor was
   never called.

## The answer

```
## Result
Finished the merge of main into feature/tax (5a3792d). pricing.py
conflicted on the return line of total(): main (c42ec3f "Round order
totals to cents") rounded the result to cents, feature/tax (e59fbe6
"Add a tax rate to the order total") multiplied it by (1 + tax). Both
are kept: return round((subtotal - subtotal * discount) * (1 + tax), 2).

## State
## feature/tax; nothing to commit, no merge in progress.

## Checked
- git checkout --conflict=zdiff3 pricing.py: read base, ours and theirs.
- git diff --check: no leftover markers.
- uv run --no-project python -m unittest: Ran 3 tests, OK (the rounding
  test from main and the tax test from the branch both pass).

## Not checked
- Whether tax should apply before or after rounding in the business
  rules: this resolution rounds last, as both tests expect. Not pushed.
```
