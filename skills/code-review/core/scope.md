# Scope: get the change, size it, say what is in and out

**Verdict you produce:** the scope block, before any finding.

```
kind:       <Diff | Module | Re-review | Tests | Security>
source:     <branch feature against main | patch <path> | MR !42>
reviewed:   <head hash> against <base: the merge base hash>
size:       <N files, +a -b>   (git diff --shortstat)
read:       <files to read line by line, largest first>
repeated:   <files that received one repeated edit, and the check that showed it>
out:        <files not reviewed, and why>
```

## Steps

1. **Start from a clean tree.** `git status --short` must print nothing
   but untracked files you know (`?? uv.lock`). A review switches
   commits to run the tools on the base (`core/tools.md`), and local
   edits would ride along or block it. If the tree is not clean, ask.
2. **Get the change** with the file in `sources/` for where it lives:
   `git-diff.md` (a branch), `patch-file.md` (a patch or mail),
   `gitlab-mr.md` (a merge request). Each ends with the diff in a file
   outside the repository, and the head checked out or applied.
3. **Size it first**, before reading any hunk:

   ```
   git diff --shortstat origin/main...HEAD
   uv run --no-sync python <skill>\recipes\review_diff.py scope $env:TEMP\review.diff
   ```

   `scope` prints the files with an edit of their own, largest first,
   and the files that received the same edit, with that edit. *lab:* a
   change of 13 files printed `same edit in 12 files (digits read as
   N)` with the four lines of an import renamed, and one file with an
   edit of its own, `src/app/util.py`, where the renamed function also
   gained a default.
4. **Read the commits**: `git log --reverse --format="%h %an %s"
   origin/main..HEAD`. The subjects and bodies say what the author
   meant; they are claims to check against the diff, never evidence
   that it does so (invariant 7). Commit message hygiene is a comment
   only if the repository has a convention (git: `core/name.md`), and
   at most a nit.
5. **Decide what is read line by line.** Every file with its own edit
   is read. A repeated edit is read once, and the group is checked by
   the tool's output (same normalised lines in every file), not by
   trust. Generated files, lock files and vendored code are listed
   under *out* with the reason.
6. **Too much to read?** Say so and list the rest under *out*, file by
   file. Never write that forty files were reviewed when four were
   read. A review of part of a change with the rest named is a
   complete answer; a skim of all of it is not.
7. **Name the kind** (SKILL.md's table). A Module review has no diff:
   its scope is the module's public names (`def` and `class` without a
   leading underscore, and what `__init__.py` imports) and every
   function they reach.

## Windows traps

| Trap | What happens | Do instead |
| --- | --- | --- |
| `git diff > review.diff` in Windows PowerShell 5.1 | the file is UTF-16 (*not run on Windows*); *lab:* `git apply --check` on a UTF-16 patch printed `error: No valid patches in input (allow with "--allow-empty")`, exit 128 | `git diff --output=$env:TEMP\review.diff ...`; `review_diff.py` reads UTF-16 too |
| a patch saved with CRLF line ends | *lab:* `error: patch failed: ... patch does not apply`, exit 1 | `git apply --check --ignore-whitespace` passed on the same file |
| `core.autocrlf` turns one changed line into a whole file | `--stat` shows every line changed | git: `core/clean-up.md`, then `git diff --ignore-cr-at-eol --stat` |
| the diff file written inside the repository | shows as `?? review.diff` and can be committed by accident | write it under `$env:TEMP` |

A UTF-8 file with a byte order mark applied (*lab*).

## Never

- Never start reading hunks before the size is known.
- Never review `main..HEAD` (two dots) with `git diff`: once main has
  moved it shows main's new commits reversed (`sources/git-diff.md`).
- Never leave the scope implicit: the reader must see what was not read.
