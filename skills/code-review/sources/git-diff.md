# A branch: git diff against the merge base

Every command ran on git 2.43.0 in the lab; PowerShell forms of
variables and paths are *not run on Windows*.

## Get it

```powershell
git status --short                          # clean before you start
git fetch origin                            # reads: changes only origin/*
git switch feature                          # the branch under review
git merge-base origin/main HEAD             # the base the diff starts from
git diff --shortstat origin/main...HEAD
git diff --output=$env:TEMP\review.diff origin/main...HEAD
```

Take the target branch from the person or the MR; `origin/main` stands
for it. A branch that exists only on the remote: `git switch feature`
creates the local one from `origin/feature` when the name is unique.

## Two dots and three dots

| Form | Compares | *lab*, main moved on after the branch |
| --- | --- | --- |
| `git diff origin/main...HEAD` | the merge base with HEAD: the branch's own change | 3 files, the change only |
| `git diff origin/main..HEAD` | the tip of main with HEAD | 4 files: main's new `extra.py` shown as deleted |
| `git log origin/main..HEAD` | commits on the branch, not on main | the branch's commits (two dots are right for `log`) |

## Read it

| Need | Command |
| --- | --- |
| files and their status (A, M, D, R) | `git diff --name-status origin/main...HEAD` |
| the whole function around each hunk | `git diff -W origin/main...HEAD -- <path>` |
| one commit | `git show --stat <hash>`, then `git show <hash> -- <path>` |
| the commits, oldest first | `git log --reverse --format="%h %an %s" origin/main..HEAD` |
| a file as it was on the base | `git show <merge-base>:<path>` |
| a name on main's tip, without switching | `git grep -n -w <name> origin/main -- src` |
| whether it merges cleanly | `git merge-tree --write-tree origin/main HEAD` |

`git merge-tree --write-tree` changes nothing: it printed a tree hash and
exited 0 when the merge was clean, and exited 1 with `CONFLICT (content):
Merge conflict in <path>` when not (*lab*). A conflict is not a finding
about the code, but the verdict cannot be `approve` for a change that
does not merge: say so under *Checked*.

## Callers added on main after the branch

The branch's checkout does not contain callers that main gained since
the merge base; they break at merge time, not in the branch's tests.
Search main's tip too: `git grep -n -w get_book origin/main -- src
tests` (*lab*: each hit printed with the ref first, as
`main:src/library/api.py:19:        book = get_book(book_id)`).

## Your own uncommitted work

`git diff --output=$env:TEMP\review.diff HEAD` holds staged and unstaged
changes against the last commit. New files appear only after
`git add -N <path>` (intent to add).
