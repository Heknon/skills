# Versions

Check first: `git --version`. The skill was run on **git 2.43.0**
(Linux, the lab's installed git) and, for the rows marked, on **2.55.0**
built from the kernel.org release tarball (the newest release on
2026-09-26; git 3.0 had not shipped). Git for Windows was not run.

## What differs

| Behaviour | 2.43.0 | 2.55.0 | Source |
| --- | --- | --- | --- |
| `git rebase --autosquash` without `-i` | ignored: `amend!` commit stayed | folds `fixup!` and `amend!` | lab; release notes 2.44.0 |
| rebase todo line | `pick 258c426 Validate IBAN ...` | `pick 258c426 # Validate IBAN ...` | lab |
| `--fixup=reword:<c>` with `-m` | refused | refused | lab |
| `--force-if-includes` | works | works | lab |
| `git stash show --include-untracked` | works | works | lab |
| `merge.conflictStyle=zdiff3`, `--conflict=zdiff3` | works | works | lab (plan: from 2.35) |
| `GIT_EDITOR=:` handled inside git | yes | yes | `editor.c` in both sources |
| `GIT_PAGER=cat` handled inside git | yes | yes | `pager.c` in both sources |

Everything else in this skill ran on 2.43.0; the tidy, reword, rebase
continue, stash and push-lease recipes also ran on 2.55.0 with the same
result.

## Older than 2.43

Not run. Orient reads `git --version`; on an older git, check each
feature this skill uses before relying on it, with `git <cmd> -h`: `git switch` and `git restore`, `--conflict=zdiff3`,
`--force-if-includes`, `git stash push --include-untracked` with
`show --include-untracked`, `git commit --trailer`, `--fixup=amend:`.

## Git 3.0 (planned, not released)

`Documentation/BreakingChanges.adoc` in the 2.55.0 source plans for 3.0:
new repositories use SHA-256 and the "reftable" ref storage, and the
default branch of a new repository is `main`. A SHA-1 bundle does not go
into a SHA-256 repository: on 2.55.0, `git bundle verify` in one made
with `--object-format=sha256` said `fatal: missing mapping of 5074d14...
to sha256`. `git bundle verify` names the bundle's algorithm (`The
bundle uses this hash algorithm: sha1`). Recheck this file when 3.0
ships.
