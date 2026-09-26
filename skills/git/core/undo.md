# Undo

**Verdict you produce:** the command picked from the table, with the
three answers that picked it, and `git status` before and after.

```
pushed?     <yes: git branch -r --contains <hash> lists <branch> | no>
committed?  <yes | no>
staged?     <yes | no>
command:    <the command>
verdict undo: <undone | reverted in a new commit | stopped: <why>>
```

## Three questions

1. **Is it pushed?** `git branch -r --contains <hash>` prints a remote
   branch: yes. Then only `revert` (a new commit that undoes it). Never
   `reset`, `--amend` or rebase on it (invariant 3).
2. **Is it committed?** `git log --oneline -5`.
3. **Is it staged?** `git status`.

## The table (lab: 2.43.0)

| Situation | Command | Class |
| --- | --- | --- |
| staged a file by mistake | `git restore --staged <path>` | reversible |
| last commit, not pushed, keep the changes staged | `git reset --soft HEAD~1` | reversible |
| last commit, not pushed, keep the changes unstaged | `git reset HEAD~1` (`Unstaged changes after reset:`) | reversible |
| last commit's message or content, not pushed | `core/commit.md`, Amending | rewrite, local |
| commits on the wrong branch, not pushed | `reference/rewrite.md`, wrong branch | rewrite, local |
| a pushed commit | `git revert --no-edit <hash>` | reversible |
| a pushed merge commit | `git revert -m 1 --no-edit <merge hash>` | reversible |
| a file's uncommitted edits | save first, then `git restore <path>` | destroys |
| a deleted tracked file | `git restore <path>` | reversible |
| a file as it was in an older commit | `git restore --source=<hash> <path>` | destroys the current edits |
| an operation in progress | `git merge --abort`, `git rebase --abort`, `git cherry-pick --abort`, `git revert --abort`, `git bisect reset` | reversible |
| a merge or revert that left changes staged and no operation | `git reset --merge` | destroys those staged changes |
| everything since the last commit | stash with `--include-untracked`, then decide | reversible |

`--abort` with nothing in progress only complains: `fatal: There is no
merge to abort (MERGE_HEAD missing).`, `fatal: No rebase in progress?`,
`error: no cherry-pick or revert in progress`.

## Reverting a merge

`git revert <merge>` without `-m` fails: `error: commit 9ddf3e8... is a
merge but no -m option was given.` `-m 1` keeps parent 1, the branch
that received the merge (`git log -1 --format=%p <merge>` lists the
parents, first one first). In the lab `git revert -m 1 --no-edit
9ddf3e8` undid the merged branch's two commits, kept the later
`Add currency to receipt lines`, and the failing test passed again. The
message it writes: `Revert "Merge branch 'feature/fast-tax'"` / `This
reverts commit 9ddf3e8..., reversing changes made to eb6b296...`.

Merging that branch again later brings nothing back: in the lab it said
`Already up to date.` To restore the change, revert the revert
(`git revert --no-edit <revert hash>`; 2.43.0 titled it `Reapply "Merge
branch 'feature/fast-tax'"`).

## Why --no-edit

`git revert` opens the editor only when stdin is a terminal (source:
`sequencer.c`, `isatty(0)`). With no terminal it committed; under a
terminal the editor was called and failed, and the revert **left its
changes staged with no revert in progress**: `git revert --abort` said
`no cherry-pick or revert in progress`, and `git reset --merge` cleaned
it. Always pass `--no-edit`.

## Reset on pushed commits

`git reset --hard <older>` then `git push` is rejected: `! [rejected]
main -> main (non-fast-forward)`. Forcing it past that erases the commits
for everyone who fetched. That is never an undo.
