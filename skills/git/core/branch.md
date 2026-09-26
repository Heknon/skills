# Branch

**Verdict you produce:** the branch, its upstream, and the state after.

```
branch:   <name> at <hash> <subject>
upstream: <origin/name | none yet: set on first push>
verdict branch: <created | switched | renamed | deleted | tracking set | stopped: <why>>
```

Names follow `core/name.md`; check each with
`git check-ref-format --branch <name>`.

## Commands (lab: 2.43.0)

| Want | Command | Notes |
| --- | --- | --- |
| new branch from the latest main | `git fetch origin`, then `git switch -c <name> --no-track origin/main` | without `--no-track` the branch tracks `origin/main`: `branch 'feat/PROJ-50-x' set up to track 'origin/main'.`, and `git push` then fails with `The upstream branch of your current branch does not match the name of your current branch.` |
| new branch here | `git switch -c <name>` | no upstream until the first push |
| switch | `git switch <name>` | refuses when a local change would be overwritten: `error: Your local changes to the following files would be overwritten by checkout:` |
| a remote branch, locally | `git switch <name>` when only `origin/<name>` exists | `branch 'fix/PROJ-7-null-total' set up to track 'origin/fix/PROJ-7-null-total'.` |
| set the upstream | first push: `git push -u origin <name>` | `branch '<name>' set up to track 'origin/<name>'.` |
| rename | `git branch -m <old> <new>` | the upstream is kept: after renaming, `git status -sb` still showed `...origin/<old name>` until `git push -u origin <new>` |
| delete, merged | `git branch -d <name>` | refuses if not merged: `error: the branch 'fix' is not fully merged.` |
| delete, not merged | `git branch -D <name>` | destroys the only name for its commits: ask. It prints the hash (`Deleted branch fix (was 644489a).`); put that in the answer |
| delete on the remote | `git push origin --delete <name>` | leaves this machine: only when asked |
| which are merged | `git branch --merged main`, `git branch --no-merged main` | |
| where is a branch checked out | `git worktree list` | `git switch` refuses a branch another worktree has: `fatal: 'feature/report' is already used by worktree at '<path>'` |

## Carrying uncommitted changes

`git switch main` with uncommitted edits that do not clash succeeds and
**carries them along** (lab: `M	pricing.py` printed, then `Switched to
branch 'main'`). If the ask was a clean start, that is not one: stash
first (`core/move-work.md`).

## Detached HEAD

`git status` says `HEAD detached at <hash>`. Commits made there belong
to no branch; switching away warned:

```
Warning: you are leaving 1 commit behind, not connected to
any of your branches:
  ba1ec68 detached work
```

Keep them: `git branch rescue/<name> <hash>` (or `'HEAD@{1}'` right after
switching away), before anything else.

## Renaming a pushed branch

`git branch -m <old> <new>`, `git push -u origin <new>`. The old name
stays on the remote; delete it (`git push origin --delete <old>`) only
when asked, since a merge request or a colleague may use it.
