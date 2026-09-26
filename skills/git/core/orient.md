# Orient

**Verdict you produce:** the state of the repository, one fact per line,
each from a command you ran.

```
branch:      <name, or "detached at <hash>">
upstream:    <origin/x, ahead n, behind m | none>
staged:      <files, or none>
unstaged:    <files, or none>
untracked:   <files worth naming, or none>
in progress: <merge | rebase | cherry-pick | revert | bisect | none>
stashes:     <count and the newest message, or none>
verdict orient: <safe to change | finish or abort <operation> first | save work first>
```

## Steps

1. `git status` (the long form). It is the only one that says an
   operation is in progress. On 2.43.0 the short form showed a finished
   conflict as a plain `M  discount.py`, while the long form said:
   ```
   All conflicts fixed but you are still merging.
     (use "git commit" to conclude merge)
   ```
   and during a bisect only the long form said `You are currently
   bisecting, started from branch 'main'.`
2. `git status -sb` for the one-line branch summary:
   `## feature/export...origin/feature/export [ahead 1, behind 1]`.
   `## HEAD (no branch)` means detached HEAD, or a rebase or bisect.
   For scripts: `git status --porcelain=v2 --branch` gives
   `# branch.upstream origin/feature/export` and `# branch.ab +1 -1`.
3. The upstream's state is only as new as the last fetch. `git fetch
   origin` is a read of the server that changes only `origin/*`; run it
   when the answer depends on what others pushed.
4. `git stash list`.
5. For an operation in progress, the files git keeps (they exist only
   while it is under way):

   | Path (`git rev-parse --git-path <name>`) | Means | Finish | Abandon |
   | --- | --- | --- | --- |
   | `MERGE_HEAD` | merge | `git commit --no-edit` | `git merge --abort` |
   | `rebase-merge` | rebase | `GIT_EDITOR=: git rebase --continue` | `git rebase --abort` |
   | `rebase-apply` | `am` (or an old-style rebase) | `git am --continue` | `git am --abort` |
   | `CHERRY_PICK_HEAD` | cherry-pick | `GIT_EDITOR=: git cherry-pick --continue` | `git cherry-pick --abort` |
   | `REVERT_HEAD` | revert | `GIT_EDITOR=: git revert --continue` | `git revert --abort` |
   | `BISECT_LOG` | bisect | read the result | `git bisect reset` |

   In PowerShell, set `$env:GIT_EDITOR = ':'` first instead of the
   prefix. `Test-Path (git rev-parse --git-path MERGE_HEAD)` checks one
   (`not run on Windows`).
6. `git rev-parse --is-shallow-repository` and `git worktree list` when
   history or another worktree matters.

## Verdicts

- **Safe to change**: nothing in progress, and every uncommitted change
  is one the task is about.
- **Finish or abort first**: an operation is in progress. If you did not
  start it, say so and ask which. If you started it, finish it.
- **Save work first**: uncommitted changes the task would touch. Stash
  with `--include-untracked` or commit to a backup branch
  (`core/move-work.md`), then go on.

## Never

- Never report done with an operation in progress. Run `git status` as
  the last command and read its second line.
- Never read `--short` alone to decide nothing is under way.
