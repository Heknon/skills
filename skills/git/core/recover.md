# Recover lost work

**Verdict you produce:** each recovered commit, now on a named branch or
back in the stash list, and how it was found.

```
lost:      <what the person said is gone>
found:     <hash> <subject> via <reflog entry | fsck dangling commit>
now at:    <branch name | stash@{0}>
verdict recover: <recovered | not found: <what was searched>>
```

Nothing is lost until both the reflog and `fsck` say so (invariant 7).
Recover onto a **new** branch; never move the current branch to find
out.

## Where lost work hides (lab: 2.43.0)

| Lost by | Look in | Recover |
| --- | --- | --- |
| `reset --hard`, a rebase, an amend | `git reflog` | `git branch recover/<name> <hash>` |
| switching away from a detached HEAD | the warning's hash, or `git reflog` | `git branch recover/<name> <hash>` |
| `git branch -D` | the hash it printed, or `git reflog` | `git branch <name> <hash>` |
| `git stash drop` or `clear` | the hash it printed, or `git fsck --no-reflogs` | `git stash branch recover/<name> <hash>` then commit, or `git stash store -m "<msg>" <hash>` |
| a file never committed nor stashed | nowhere in git | say so |

## Steps

1. `git reflog -n 20`, or with subjects:
   `git log -g --format='%h %gd %gs | %s' -n 20`. In the lab:
   ```
   41556d9 HEAD@{0}: reset: moving to HEAD
   41556d9 HEAD@{1}: commit: Bump version to 1.4.1
   84373ec HEAD@{2}: reset: moving to HEAD~2
   83dc5a4 HEAD@{3}: commit: Add payment terms footer to invoice PDF
   3ba73fc HEAD@{4}: commit: Add company header to invoice PDF
   ```
   The lost tip is the entry just before the `reset: moving to HEAD~2`
   line: `83dc5a4`, not `HEAD@{1}` (a later commit and a stash had moved
   HEAD since; `reset: moving to HEAD` is what `git stash` writes).
   Quote `'HEAD@{3}'` in PowerShell, or use the hash.
2. `git branch recover/invoice-pdf 83dc5a4`, then
   `git log --oneline main..recover/invoice-pdf` showed both commits.
3. For a dropped stash, the reflog has nothing (the stash reflog lost
   the entry). `git fsck --no-reflogs` lists commits nothing reaches:
   ```
   dangling commit 83dc5a4...
   dangling commit a1e2bc1...
   ```
   Identify each: `git log -1 --format='%h %ci %p | %s' <hash>`. A stash
   has two or three parents and a subject `On <branch>: <message>` or
   `WIP on <branch>: ...`; the lab's read `a1e2bc1 ... 41556d9 7b08a55 |
   On main: late payment email draft`. `git stash show --stat <hash>`
   shows its files.
4. Put it somewhere safe:
   - `git stash branch recover/email-draft a1e2bc1` made the branch at
     the stash's base and applied it, staged. **Commit it there**; in
     the lab, switching away without committing carried the staged file
     onto main.
   - or `git stash store -m "late payment email draft (recovered)"
     a1e2bc1`, which put it back as `stash@{0}`.
5. `git status`, and the log of each recovered branch, in the answer.

## Time limits

`git gc` removes unreachable commits once their reflog entries expire:
by default after 30 days for commits no branch reaches, 90 for others
(`builtin/reflog.c`, 2.43.0), and prunes unreachable objects older than
two weeks (`prune_expire = "2.weeks.ago"` in `builtin/gc.c`). Recover
first; never run `gc` or `prune` while something is missing.
