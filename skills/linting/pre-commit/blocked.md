# A commit refused by a hook

**Verdict you produce:** the hook id, what it reported, what you
changed, and the commit that then passed.

```
refused:  ruff-check: F841 Local variable `debug_before` is assigned to but never used (src/cart/totals.py:10)
changed:  removed the leftover line; git add src/cart/totals.py
commit:   729b0fb "Fix rounding in cart totals"; ruff check Passed, ruff format Passed
```

A hook that fails is a finding like any other (`core/read-finding.md`).
The person asked for a commit of working, checked code; getting past the
hook does not give them that.

## Read which of three cases it is

### 1. The tool reported findings (`- exit code: 1`)

Nothing changed on disk. Read the findings, fix them in the staged
files (`core/decide.md`), `git add` the files, commit again with the
same message.

### 2. The hook changed files (`- files were modified by this hook`)

A formatter or fixer rewrote files in the working tree; the staged
version is still the old one, so `git status` shows `AM` or `MM`.

1. Read the change: `git diff` (formatting only, in the lab).
2. `git add` those files.
3. Commit once more. *Lab:* two newly formatted files, then `Passed`
   for both hooks and one commit.

Other hooks may have failed in the same run on the old content (the lab
had `E701` from ruff check, which the formatter's rewrite removed). Read
them all, and run the commit again only after staging.

### 3. The fix was rolled back

```
[WARNING] Unstaged files detected.
...
ruff format....Failed
- files were modified by this hook
[WARNING] Stashed changes conflicted with hook auto-fixes... Rolling back fixes...
```

The file has staged and unstaged changes (`MM` in `git status`), the
hook's fix touched lines near the unstaged ones, and pre-commit threw
the fix away. Every retry fails the same way.

1. Read the unstaged part: `git diff <file>`.
2. Format the file in the working tree:
   `uv run --no-sync ruff format <file>`.
3. If the unstaged edit belongs in this commit, `git add <file>` and
   commit (*lab:* passed). If it does not, stop and ask: separating the
   two needs an interactive `git add -p`. *Lab:* `git stash push
   --keep-index`, commit, `git stash pop` ended in a merge conflict on
   the formatted lines.

## Never, unless the person asked for exactly this

- `git commit --no-verify` or `-n`: skips every hook.
- `SKIP=<id>` for the failing hook, or for all of them.
- Undoing a formatter's change by hand to make the file look as before;
  the hook will change it again.
- Committing again without staging: the same refusal, a loop.
- Editing `.pre-commit-config.yaml` to drop or weaken the failing hook.

If a hook is itself broken (it fails on correct code, or pre-commit
reports `An unexpected error has occurred`), say so, show the output,
and fix the hook as a config task (`pre-commit/config.md`); if the
person then asks to commit past it, `SKIP=<that id>` is the narrowest
way, and the answer says it was skipped.
