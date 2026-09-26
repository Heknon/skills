# Worked example: a bisect run with untestable commits

Kinds: Orient, Bisect. Outputs are from a lab run of the `bisect`
sandbox on git 2.43.0.

## The ask

> Rounding of half cents is wrong on main: to_cents('0.125') gives
> 0.12, it gave 0.13 at v1.0. Which commit broke it?

## Steps

1. **Orient.** `git status -sb`: `## main`, clean.
2. **The script, outside the repository.** Copied
   `recipes/bisect_test.py` to `../bisect_test.py`; its `check()`
   already tests `to_cents("0.125") == "0.13"` and `IMPORTS` is
   `["shop.money"]`.
3. **Confirm both ends** (`core/bisect.md` step 2).
   `uv run --no-project python ../bisect_test.py` on main printed `bad`,
   exit 1. `git switch --detach v1.0`, the same command printed `good`,
   exit 0. `git switch -` back to main.
4. **Run it.**
   ```
   git bisect start HEAD v1.0
   git bisect run uv run --no-project python ../bisect_test.py
   ```
   The first two commits bisect tried could not import the module:
   ```
   [3c71ca3...] Update changelog (20)
   skip: cannot import shop.money: ModuleNotFoundError("No module named 'shop.fmt'")
   [ea221b9...] Update changelog (21)
   skip: cannot import shop.money: ModuleNotFoundError("No module named 'shop.fmt'")
   ```
   Exit 125 made bisect skip them and try others. It ended:
   ```
   2d373da1a996b1e909214fd77009c0c062e65c89 is the first bad commit
   ...
       Use the context rounding in to_cents
    CHANGELOG.md  | 1 +
    shop/money.py | 4 ++--
   bisect found first bad commit
   ```
5. **The log**, `git bisect log`, for the answer: seven steps, two of
   them `git bisect skip`.
6. **Reset.** `git bisect reset`: `Switched to branch 'main'`.
   `git status -sb`: `## main`.

A script that let the import error exit 1 named `Pad amounts in money
helpers`, the commit that broke the import, not the rounding.

## The answer

```
## Result
The first bad commit is 2d373da "Use the context rounding in to_cents".
It changed shop/money.py (4 lines); to_cents now rounds with
ROUND_HALF_EVEN, so 0.125 becomes 0.12. (Reading its diff to confirm
the cause is the debugging skill's next step.)

## State
## main, clean; bisect reset done, nothing in progress.

## Checked
- ../bisect_test.py: bad on main (exit 1), good at v1.0 (exit 0).
- git bisect run: "2d373da... is the first bad commit".
- git bisect log: 7 steps; 3c71ca3 and ea221b9 skipped because
  shop.money could not be imported there (commits 17 to 23 import
  shop.fmt before it exists).

## Not checked
- Other callers of to_cents; no fix made, since the ask was which commit.
```
