# Resolve a conflict

**Verdict you produce:** per file, what the base had, what each side
changed, the resolution, and the tests after.

```
<path>:
  base:   <the lines as they were>
  ours:   <what this side changed, and in which commit>
  theirs: <what the other side changed, and in which commit>
  result: <the lines kept, and why both intents survive>
tests:  <command and summary>
verdict conflict: <resolved and concluded | resolved, operation continues | cannot tell: ask>
```

## Who is ours

| Operation | `:2:` / `--ours` / `<<<<<<<` | `:3:` / `--theirs` / `>>>>>>>` |
| --- | --- | --- |
| `merge X` | the branch you are on | X |
| `rebase X` | X, the branch you rebase onto | your commit being replayed |
| `cherry-pick C`, `revert C` | the branch you are on | C (or its inverse) |
| `stash pop` / `apply` | the branch you are on | the stash |

In a rebase they swap. In the lab (`evals` sandbox rebase-sides) the
branch raised `LATE_FEE = 5` to `7` and main added a comment on the same
line. `git checkout --ours fees.py` took main's line, `git rebase
--continue` then found nothing to commit, **dropped the branch's commit
without a word**, and printed `Successfully rebased`. The test for 7
failed afterwards.

## Steps

1. `git status`: the operation, and the files under `Unmerged paths`
   (`both modified`, `deleted by us`, `deleted by them`).
2. Show the base in the file:
   `git checkout --conflict=zdiff3 <path>`. It rewrites the file with
   three parts and the labels `ours`, `base`, `theirs`:
   ```
   <<<<<<< ours
       return (subtotal - subtotal * discount) * (1 + tax)
   ||||||| base
       return subtotal - subtotal * discount
   =======
       return round(subtotal - subtotal * discount, 2)
   >>>>>>> theirs
   ```
   It overwrites any partial edit to that file; do it first.
3. Read what each side did to the base, and why:
   ```
   git diff :1:pricing.py :2:pricing.py
   git diff :1:pricing.py :3:pricing.py
   git log --oneline --left-right HEAD...MERGE_HEAD -- pricing.py
   ```
   The last lists `<` our commits and `>` theirs that touched the file
   (use `REBASE_HEAD` or `CHERRY_PICK_HEAD` for those operations;
   `git log --merge --oneline` lists both sides during a merge). Read
   those commit messages.
4. Write the result by hand: both intents, not one side. In the lab the
   correct line was `return round((subtotal - subtotal * discount) * (1 +
   tax), 2)`; each side alone failed a test.
5. `git diff --check` must print nothing. Git itself accepts markers: in
   the lab `git add` and `git commit` took a file full of them, and only
   `--check` said `pricing.py:4: leftover conflict marker`.
6. Run the tests.
7. `git add -- <path>`, then conclude:
   - merge: `git commit --no-edit`
   - rebase: `GIT_EDITOR=: git rebase --continue`
   - cherry-pick or revert: `GIT_EDITOR=: git cherry-pick --continue`
     (or `revert`); both called the editor under a terminal in the lab
   - stash pop: the stash is kept (`The stash entry is kept in case you
     need it again.`); after resolving, `git restore --staged <path>` if
     you do not want it staged, then `git stash drop` only when the
     result is checked.
8. `git status`: nothing in progress.

## Whole-file choices

`git checkout --ours <path>` or `--theirs` (then `git add`) only when
one side must win completely and you said why, such as a generated lock
file you will regenerate. Modify/delete conflicts
(`CONFLICT (modify/delete): report.py deleted in HEAD and modified in
feature/report.`, status `DU`): decide whether the file should exist;
`git rm -- <path>` or `git add -- <path>`.

## Stop and ask

- Both sides changed behaviour and no test, message or issue says which
  is right.
- The conflict is in code you cannot run.

## Never

- Never resolve by keeping one side wholesale because it is "ours".
- Never leave the operation in progress; `git merge --abort` or
  `git rebase --abort` is a complete answer if you must stop.
