# The step loop

**Verdict you produce, for every step:**

```
step:    <n>. <catalogue name>: <what moved, renamed or extracted>
refs:    <n hits: all edited or explained (core/every-reference.md) | not a rename or move>
checks:  pytest <line>; ruff <line>; mypy <line>; import_all <line>; probe <identical | differs>; names <no line lost | lost: ...>
commit:  <hash> <subject>
verdict step: <green, committed | red, undone: <check and its message> | stopped: <finding>>
```

Edit, find every reference, check, commit. A step that goes red is
undone, then redone smaller or with what was missed, never patched until
it passes.

## Steps

1. **Read the step's file** in `steps/`. Check its preconditions; if one
   fails, the step is the wrong one or needs a smaller step first.
2. **Before editing a name or a path, list its references**
   (`core/every-reference.md`). The list is written before the first
   edit, not after.
3. **Edit** with the editing tool: the definition first, then each hit
   on the list, one by one. Never a replace-all across files: the same
   word can be another thing (in the lab, `AdminClient.get_user` was a
   different method from the `get_user` being renamed).
4. **Search again** for the old name or path. Every remaining hit must
   be on the list as explained.
5. **Run the checks** in `core/checks.md`, all of them, and compare with
   the baseline.
6. **Green: commit the step.** Read `git diff --stat` and `git diff`:
   only this step is in it, no formatting of other lines (linting's
   `core/in-scope.md`). Stage by name and commit, as the git skill's
   `core/commit.md` says, with a subject that names the step:

   ```powershell
   git add -- app/reports/__init__.py app/reports/money.py
   git commit -m "Move money formatting to app.reports.money" -m "Structure only; app.reports re-exports every name."
   ```

   The subject follows the repository's convention (git's
   `core/name.md`); the body says it is structure only.
7. **Red: undo the step.**

   ```powershell
   git stash push --include-untracked -m "red: move clock to app.reports.clock"
   git status          # nothing to commit, working tree clean
   ```

   The failed attempt is kept in the stash to read
   (`git stash show --include-untracked --stat 'stash@{0}'`), and the tree
   is back at the last green commit. Stash the whole tree, never a list
   of paths: after a `git mv`, `git stash push -- <paths>` saved a stash
   and then stopped with `fatal: pathspec ':(,prefix:0)app/reports.py'
   did not match any files`, leaving the changes both in the stash and
   in the tree (lab, git 2.43.0). Untracked files that are not ignored go
   into the stash too; keep the probe in an excluded `.ledger/`.
8. **Read why it went red**, from the first failure (seniority's
   `core/reading-errors.md`). Then redo the step:
   - a reference was missed (a patch target, a string, a script): add it
     to the list and redo the whole step with it;
   - the step was too big: cut it (`core/plan-steps.md`) and do the
     first part;
   - the failure shows the code relied on something the step changes (a
     shared dict, an import order): redo it so that stays true, as in
     `examples/red-step-undone.md`.
   The same step red twice: seniority's loop rules apply; cut it smaller
   or stop and report.
9. **A bug seen on the way**: `core/refactor-or-fix.md`, then continue.

## Check every commit at the end (optional)

When the steps are done, this runs the tests at each commit since
`<base>`, the commit before the first step. It needs the git skill's
session settings (`GIT_SEQUENCE_EDITOR` set to `:`), or it opens an
editor:

```powershell
git rebase --exec "uv run --no-sync pytest -q -p no:cacheprovider" <base>
```

On commits already on top of `<base>` it rewrites nothing (lab: the tip
hash was the same after six green steps). At a red commit it stops with
`warning: execution failed: <command>` and `You can fix the problem, and
then run git rebase --continue`, and `git status` says `interactive
rebase in progress`. Do not fix it there: `git rebase --abort`, then
report which commit was red.

## Never

- Never edit a test's expected value, a conftest, a fixture's data or a
  check's settings to turn a red step green. A patch target or import
  line in a test is a reference and belongs in the step's list from the
  start.
- Never start the next step on a red or uncommitted one.
- Never push. Commits stay local until the person says.
