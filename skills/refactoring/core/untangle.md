# Untangle a mixed change

**Verdict you produce:** the change split into commits that each hold
one kind, structure first, each checked.

```
read:      <each hunk of the diff: structure | behaviour, and why>
evidence:  <for each behaviour hunk: an input, the output before, the output after>
saved:     stash@{0} "<message>" (the whole mixed change)
commits:   <hash> <structure subject>; <hash> <behaviour subject | not committed: asked>
proof:     git diff --quiet 'stash@{0}' -- <files> -> exit 0 (nothing of the change lost)
verdict untangle: <split into n commits | structure committed, behaviour waits for the person>
```

"I refactored it, please commit" often covers a rename plus a small
change of behaviour that looked like tidying. Tests passing does not
tell them apart: in the lab, a rename of `_calc` came with a switch from
`round()` to truncation, and the 3 tests passed on both versions, while
`late_fee(999.99, 35)` gave 5.0 before and 4.99 after.

## Steps

1. **Read the whole diff**, hunk by hunk: `git diff`, and
   `git diff --stat` for its size. Mark each hunk structure (rename,
   move, extraction with the same statements) or behaviour (any changed
   operator, constant, condition, call, default, rounding, exception,
   order). A hunk with both is behaviour.
2. **Show each behaviour hunk with an input** where old and new differ:
   run the old code (`git stash`, run, `git stash pop`) and the new, on
   the same call. No input found after trying edge values: say it looks
   like structure and why, but keep it apart anyway if unsure.
3. **Save the whole change** before splitting it:

   ```powershell
   git stash push -m "mixed: rename and rounding" -- billing/fees.py
   ```

   The file is back at the last commit, and the stash holds the mixed
   version.
4. **Make the structure-only version by editing**: apply only the
   structure hunks (the rename) to the clean file. Run the checks and the
   probe: identical to the last commit. Commit it
   (`core/step-loop.md`).
5. **Bring back the mixed version on top** and see what is left:

   ```powershell
   git restore --source='stash@{0}' -- billing/fees.py
   git diff          # only the behaviour hunks now
   git diff --quiet 'stash@{0}' -- billing/fees.py   # exit 0: the file equals the stashed version
   ```

   In the lab, the diff after this was the one line
   `-    return round(amount * DAILY_RATE * days, 2)` /
   `+    return int(amount * DAILY_RATE * days * 100) / 100`.
6. **The behaviour part** is the person's call: commit it on its own,
   with a subject that says what changes ("Truncate late fees to the
   cent instead of rounding") and the input from step 2 in the body; or
   leave it uncommitted and ask. Tests for it come from the pytest and
   debugging skills, not from this one.
7. **Drop the stash** only when the tree or the commits hold everything
   it had (`git diff --quiet 'stash@{0}' -- <files>` exit 0, or the last
   commit contains it), then `git stash drop`. Braces are quoted in
   PowerShell (git's `reference/windows.md`).

With more files, do steps 3 to 5 with every file of the change. When
the two kinds sit in different hunks of one file, the git skill's
`recipes/stage_hunks.py` can stage the structure hunks instead of step
4's editing.

## Never

- Never commit a mixed change as "refactor", even when the tests pass.
- Never drop the stash before its content is committed or confirmed
  in the tree.
- Never split by guessing from the diff alone: show each behaviour hunk
  with an input.
