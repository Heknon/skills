# Move work: stash, cherry-pick, worktrees

**Verdict you produce:** where the work went, and the command that shows
it is there.

```
moved:  <what> to <stash@{n} "message" | branch <name> at <hash> | worktree <path> on <branch>>
shown:  <git stash list line | git log line | git worktree list line>
verdict move-work: <moved | stopped: <why>>
```

## Stash (lab: 2.43.0)

| Want | Command |
| --- | --- |
| save everything, untracked too | `git stash push --include-untracked -m "<what and why>"` |
| save some paths | `git stash push -m "<msg>" -- <path> ...` |
| keep the staged part in place | `git stash push --keep-index -m "<msg>"` |
| list | `git stash list` |
| see what one holds | `git stash show --include-untracked --stat 'stash@{0}'` |
| bring back and keep the stash | `git stash apply 'stash@{0}'` |
| bring back and remove it | `git stash pop` (kept if it conflicts) |
| onto a new branch | `git stash branch <name> 'stash@{0}'` |
| delete | `git stash drop 'stash@{0}'`: destroys; only when its content is safe elsewhere |

- Quote `'stash@{0}'` in PowerShell, where `{}` is a script block
  (`reference/windows.md`).
- Without `--include-untracked` a new file stays in the working tree.
  Ignored files (`.env`) are stashed only with `--all` (lab: `.env` left
  the folder until `git stash pop`); leave them out.
- In the lab `git stash push --include-untracked -m "experiment/cache:
  bulk tiers and load-test notes"` saved `pricing.py` and `notes.md`
  (`2 files changed, 13 insertions(+)`), left the ignored `.env`, and
  `git switch main` then gave a clean status.
- `git stash drop` asks nothing and prints `Dropped refs/stash@{0}
  (4ca9539...)`; that hash is how to get it back (`core/recover.md`).

## Cherry-pick

`git cherry-pick -x <hash>` copies one commit onto the current branch;
`-x` adds `(cherry picked from commit <hash>)` to the message, which
tells readers where it came from. A range: `git cherry-pick A..B` (A
excluded). A conflict: `core/conflicts.md`, then
`GIT_EDITOR=: git cherry-pick --continue`.

## Worktrees

A second folder for another branch, without stashing:

```
git worktree add ../hotfix -b fix/PROJ-9-typo --no-track origin/main
git worktree list
git worktree remove ../hotfix
```

- A branch can be checked out in one worktree only: `fatal:
  'feature/report' is already used by worktree at '<path>'`.
- `git worktree remove` refuses a folder with changes: `fatal:
  '../hotfix' contains modified or untracked files, use --force to
  delete it`. `--force` destroys them.
- The branch outlives the worktree; delete it separately if asked.
- Deep worktree paths on Windows: `reference/windows.md`.
