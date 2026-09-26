# Prove the fix

**Verdict you produce:** two runs of the same reproduction, one with the
fix and one without, and the working tree restored.

```
with fix:     <command> -> <result, such as "exit 0, dune 12.00" or "0 of 20 failed">
fix reverted: <same command> -> <result, such as "exit 1, dune 37.50" or "20 of 20 failed">
restored:     <how: git restore, git stash pop; git status --short shows only the intended changes>
verdict:      proven | not proven: <why>
```

A reproduction that passes after the fix proves nothing on its own: it
may have passed before too. Only the pair proves the fix: the same
command fails without it and passes with it.

## Steps

1. **Run the reproduction with the fix.** It must pass. For an
   intermittent bug, run it as many times as it took to fail before, and
   more (`core/intermittent.md`): "0 of 20" against "20 of 20".
2. **Revert only the fix**, not the reproduction or a new test:

   | The fix is | Revert with | Restore with |
   | --- | --- | --- |
   | uncommitted | `git stash push -- <file>` | `git stash pop` |
   | the last commit | `git restore --source=HEAD~1 -- <file>` | `git restore -- <file>` |
   | not in git | a copy of the file made before the fix | copy it back |

   *lab (git 2.43.0):* both forms changed only the named file; `git
   status --short` showed ` M billing/total.py` while reverted and nothing
   for it after restoring. Prefer these to `git show HEAD~1:<file>`
   piped into a file: *lab (PowerShell 7.4 on Linux)*, `| Set-Content`
   turned `\r\n` into `\n`; Windows PowerShell 5.1 was not run
   (`tools/powershell.md`).
3. **Run the same reproduction again.** It must fail with the original
   symptom: the same message or wrong value, not a new error.
4. **Restore** and run once more: it passes. `git status --short` shows
   the fix and the new test, nothing else.
5. **Run the rest**: the project's tests, or the command the person uses.
   A fix that breaks something else is not done.

## When the proof fails

| Seen | Meaning | Next |
| --- | --- | --- |
| passes with the fix **and** without it | the reproduction never showed the bug | make it show the reported case, then start again |
| fails with the fix **and** without it | the fix does not fix it | back to the hypothesis loop, with this as an observation |
| without the fix it fails differently | the revert was wrong, or the fix changed more than the cause | revert exactly the fix; compare `git diff` |

*lab (not-proven):* a "fix" for BUG-88 came with a test for
`line_total(1, 10.005) == 10.01`. With the fix reverted the test still
passed (`2 passed`): `round(10.005, 2)` already gives `10.01`. The
ticket's own case, `line_total(1, 2.675)`, gave `2.67` **with** the fix:
`Decimal(2.675)` is built from the float, which is already below 2.675.
A test of the ticket's case failed with the "fix" and passed only after
`Decimal(str(...))`.

## Keep the reproduction

- **A test suite exists:** the reproduction becomes a test, written with
  pytest's `core/write-test.md`, and the test is part of the proof: it
  fails with the fix reverted. Say so under seniority's *Decided for
  you*.
- **No suite:** report the reproduction command in the answer; do not
  add a test framework or a script to the project unasked.

## Never

- Never say "fixed" from a run with the fix alone.
- Never prove a fix with a different command from the one that
  reproduced the bug.
- Never leave the tree reverted, or a stash behind (`git stash list` is
  empty of your entries at the end).
- Never let a new test pass with the fix reverted.
