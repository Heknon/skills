# A patch file or a mailed patch

Every git command ran on git 2.43.0 in the lab.

## Read it as text first

A patch is text: open it and read the header (who, what, why) and the
file list before running anything. `review_diff.py scope <patch>`
sizes it; `review_diff.py defs <patch>` needs the base's blobs, so run
it inside the repository on the branch the patch is for.

## Check that it applies, without applying it

```
git switch main
git apply --check -v $env:TEMP\change.patch
git apply --stat $env:TEMP\change.patch
```

| Output (*lab*) | Means |
| --- | --- |
| `Checking patch src/library/api.py...` and exit 0 | applies cleanly |
| `error: patch failed: src/library/books.py:20` / `error: src/library/books.py: patch does not apply`, exit 1 | the base differs, or the patch is already applied |
| exit 0 from `git apply --check --reverse <patch>` | it is already applied here |
| `error: No valid patches in input (allow with "--allow-empty")`, exit 128 | not a patch as git reads it: UTF-16 (PowerShell 5.1 `>`), or no `diff --git` lines |

A CRLF copy of a good patch failed; `--ignore-whitespace` applied it
(*lab*). A UTF-8 byte order mark did not matter.

## Apply it on a throwaway branch to run the tools

The tools and tests must run on the change (`core/tools.md`). Apply it
where nothing can be lost, and remove it after:

```
git status --short                                   # clean
git switch -c review/change main
git apply --index $env:TEMP\change.patch   # or: git am <patch> for a format-patch mail
git commit -m "review: change.patch"
# ... run the tools and tests, review ...
git switch main
git branch -D review/change             # prints "Deleted branch review/change (was <hash>)."
```

*lab:* a patch that added a new module left no file behind after
`git switch main`. `git am` took a `git format-patch` mail (its first
line `From <hash> Mon Sep 17 00:00:00 2001`) and made the commit with
the author and subject from the mail. `git branch -D` destroys only the
branch name; say its hash (git: `reference/risk.md`).

## Never

- Never apply a patch on the person's branch to review it.
- Never edit a patch that does not apply; say it does not, and against
  which base it was checked.
