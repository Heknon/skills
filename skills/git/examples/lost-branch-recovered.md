# Worked example: lost commits and a dropped stash recovered

Kinds: Orient, Recover. Outputs are from a lab run of the `lost-work`
sandbox on git 2.43.0.

## The ask

> My last two commits vanished (the PDF header and footer), and I think
> I dropped a stash with a draft email. Get them back.

## Steps

1. **Orient.** `git log --oneline` shows only `41556d9 Bump version to
   1.4.1` and `84373ec Add invoice PDF renderer`; `git stash list` is
   empty; `git status` is clean. Nothing in progress.
2. **The reflog** (`core/recover.md` step 1):
   `git log -g --format='%h %gd %gs' -n 8`
   ```
   41556d9 HEAD@{0} reset: moving to HEAD
   41556d9 HEAD@{1} commit: Bump version to 1.4.1
   84373ec HEAD@{2} reset: moving to HEAD~2
   83dc5a4 HEAD@{3} commit: Add payment terms footer to invoice PDF
   3ba73fc HEAD@{4} commit: Add company header to invoice PDF
   ```
   The reset threw away `3ba73fc` and `83dc5a4`. The tip to recover is
   `83dc5a4`, the entry just before the reset. `HEAD@{1}` is a later
   commit, not the lost one.
3. **A branch for them:** `git branch recover/invoice-pdf 83dc5a4`.
   `git log --oneline main..recover/invoice-pdf`:
   ```
   83dc5a4 Add payment terms footer to invoice PDF
   3ba73fc Add company header to invoice PDF
   ```
4. **The stash is not in the reflog.** `git fsck --no-reflogs`:
   ```
   dangling commit 83dc5a4bc57c0738f00985587f4f24e69a29df73
   dangling commit a1e2bc132e7d0b78e0f23aadccc3d7ffb1dbc4dc
   ```
   `git log -1 --format='%h %p | %s' a1e2bc1` gave `a1e2bc1 41556d9
   7b08a55 | On main: late payment email draft`: two parents and a stash
   subject. `git stash show --stat a1e2bc1`: `invoice/email.py | 2 ++`.
5. **A branch for the stash, committed:**
   `git stash branch recover/email-draft a1e2bc1` switched to the new
   branch with `invoice/email.py` staged; then
   `git commit -m "Draft the late payment email" -m "Recovered from a
   dropped stash (a1e2bc1)."` made `c4c2a37`. Without that commit the
   staged file would have followed `git switch main`.
6. `git switch main`; `git status -sb`: `## main`.
   `git log --oneline --all --graph`:
   ```
   * c4c2a37 Draft the late payment email
   * 41556d9 Bump version to 1.4.1
   | * 83dc5a4 Add payment terms footer to invoice PDF
   | * 3ba73fc Add company header to invoice PDF
   |/
   * 84373ec Add invoice PDF renderer
   ```

## The answer

```
## Result
Both are back, on new branches; main is unchanged.
- recover/invoice-pdf at 83dc5a4: "Add company header to invoice PDF"
  (3ba73fc) and "Add payment terms footer to invoice PDF" (83dc5a4).
  A `reset --hard HEAD~2` had removed them (reflog HEAD@{2}).
- recover/email-draft at c4c2a37: the dropped stash "late payment email
  draft" (a1e2bc1, found by git fsck), committed as "Draft the late
  payment email".
To put the PDF commits back on main: git merge recover/invoice-pdf
(they sit on 84373ec, before "Bump version to 1.4.1").

## State
## main, clean, nothing in progress.

## Checked
- git log -g: the reset at HEAD@{2}, the lost tip 83dc5a4 at HEAD@{3}.
- git fsck --no-reflogs: dangling a1e2bc1 "On main: late payment email draft".
- git log --oneline --all --graph: both branches as above.

## Not checked
- Whether the header and footer still apply on top of "Bump version to
  1.4.1"; not merged, since you did not ask for it.
```
