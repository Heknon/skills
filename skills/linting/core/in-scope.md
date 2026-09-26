# Fix the change, not the repository

**Verdict you produce:** the lines the task changed, the findings on
them, and what was left alone.

```
scope:    src/ledger/invoice.py, function total() (lines 4-7)
findings: fixed on the changed lines; none added
left:     30 files would be reformatted (ruff format --check); offered as a separate commit
```

A checker run over a repository that was never clean reports hundreds
of findings the task did not cause. Fixing them inside the task buries
the real change in noise, breaks `git blame`, and can change behaviour.

## Steps

1. **List what the task changes**: files and functions.
2. **Run the checker on those files only**, with the project's config:
   `uv run --no-sync ruff check src/ledger/invoice.py`,
   `uv run --no-sync mypy src/ledger/invoice.py`. Pass files or folders,
   never globs: PowerShell passes `"tests/**/*.py"` to ruff as it is,
   and ruff answered `E902 No such file or directory` (*lab, PowerShell
   7.4 on Linux*).
3. **Compare with the state before your change** when the file already
   had findings: `git stash`, run, `git stash pop`, run. Yours are the
   new ones.
4. **Fix only the new findings, and the old ones on lines you rewrote.**
5. **Format only what you wrote.** If the file is already formatted,
   `ruff format <file>` is safe. If it is not, format just your lines:

   ```
   uv run --no-sync ruff format --range 4-8 --diff src/ledger/invoice.py
   uv run --no-sync ruff format --range 4-8 src/ledger/invoice.py
   ```

   `--range` takes `<start_line>-<end_line>`, the end is exclusive
   (`4-8` formats lines 4 to 7), and it works on one file at a time
   (`The --range option is only supported when formatting a single
   file`). In the lab it reformatted only the function and added the two
   blank lines after it.
6. **Report what you left**: `uv run --no-sync ruff format --check .`
   and `ruff check --statistics` give the size in one line each.

## Offer the clean-up as its own change

A repository-wide `ruff format .` or `ruff check --fix .` is one commit
with nothing else in it, done only when the person agrees. Its hash
goes in `.git-blame-ignore-revs` so blame skips it; making the commit
and the file is the git skill's. Say in the answer:

```
The repository is not formatted (30 files would be reformatted). I did
not format it in this change. If you want, a separate commit can format
everything, listed in .git-blame-ignore-revs.
```

## Never

- Never run `ruff format .`, `ruff check --fix .` or
  `--unsafe-fixes` over the repository inside another task.
- Never widen a config (`extend-select`, stricter mypy) as part of a
  fix; that is its own task (`core/adopt.md`).
