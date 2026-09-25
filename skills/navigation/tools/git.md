# git for navigation

**What it decides:** the git command for a history question. All of them
only read; none changes the repository.

| Question | Command |
| --- | --- |
| is there history here | `git rev-parse --is-inside-work-tree`, then `git log --oneline -5` |
| who last changed lines 40 to 60 | `git blame -L 40,60 -- app/billing.py` |
| when did this exact text appear or disappear | `git log -S "retry_limit = 3" --oneline -- app/` |
| when did a line matching a pattern change | `git log -G "retry_limit\s*=" --oneline -- app/` |
| every change to lines 40 to 60 | `git log -L 40,60:app/billing.py` |
| every change to a top-level function | `git log -L :charge:app/billing.py` |
| history of a file across renames | `git log --follow --oneline -- app/billing.py` |
| what one commit changed | `git show --stat <commit>`, then `git show <commit> -- <path>` |
| what changed between two points | `git diff <old>..<new> -- <path>` |
| which commits touched a folder recently | `git log --since="2 weeks ago" --oneline -- app/billing/` |

## Notes

- `git log -L :<name>:<file>` finds a function only when its `def` starts
  at the beginning of a line. For a method inside a class it fails with
  `no match`. Use the line range form, `-L <start>,<end>:<file>`, with the
  method's lines from reading the file.
- `-S` counts occurrences, so it finds the commits where the text was
  added or removed, not every commit that touched a line containing it.
  `-G` finds every commit whose diff has a matching line.
- A shallow clone (`git rev-parse --is-shallow-repository` prints `true`)
  may not have the commit you need. Say so, and use Sourcegraph's
  `commit_search` or `diff_search` if it is available.
- Output longer than a screen may open a pager in some terminals. Add
  `--no-pager` right after `git` if the command seems to hang:
  `git --no-pager log ...`.

## Why a change was made

Only from the commit message, and from the pull request or issue it names.
If neither says, the answer is `not recorded`.
