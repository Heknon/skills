# Tidy a branch before review

**Verdict you produce:** the gate, the backup, the log before and after,
and proof the code did not change.

```
gate:    <unpushed: git branch -r --contains <oldest> is empty | the person's own branch, said by them>
backup:  backup/<branch> at <hash>
before:  <git log --oneline <base>.. >
after:   <git log --oneline <base>.. >
proof:   git diff --quiet backup/<branch> HEAD -> exit 0; tests: <summary>
verdict tidy: <tidied | not tidied: history is shared | stopped: <why>>
```

## When

Only when asked, or offered once when an unpushed branch holds `WIP`,
`fixup` or typo subjects before a merge request. If the project squashes
on merge (a GitLab setting the deployment skill reads), say that a clear
merge request title matters more than the commits.

## Steps

1. **Gate.** Find the base (`origin/main` or the branch's target) and
   list the commits: `git log --oneline origin/main..HEAD`. For the
   oldest, `git branch -r --contains <hash>` must print nothing. If it
   prints a branch, the history is shared: stop. In the lab it printed
   `origin/feature/export` and `origin/feature/export-pdf`, a colleague's
   branch built on these commits; rewriting would strand it. Tidy pushed
   commits only when the person says the branch is theirs alone.
2. **Clean tree.** `git status` shows nothing to commit; stash otherwise.
3. **Backup.** `git branch backup/<branch>`. A slash in the branch name
   is fine (`backup/feature/report` was accepted), unless a branch
   `backup` exists.
4. **Run the recipe** from `reference/rewrite.md`. The editor variables
   are set on every one; none opens an editor.
5. **Prove it.** For reword, reorder, fixup and squash the code must not
   change:
   ```
   git diff --quiet backup/<branch> HEAD     # exit 0: same tree
   git range-diff origin/main backup/<branch> HEAD
   ```
   `range-diff` pairs old and new commits: `1: 0997302 ! 1: 48d3ffe Add
   CSV export` (changed), `3: 72843d9 < -: ------- fixup` (folded away).
   Run the tests on the tip. For drop or split, the diff against the
   backup is exactly what you meant to drop.
6. **Answer** with both logs. Push only when asked, and a rewritten
   branch that was pushed only with `--force-with-lease
   --force-if-includes` (`core/push.md`).
7. Keep the backup branch until the person has seen the result; delete
   it (`git branch -D backup/<branch>`) only when they say.

## Undo the whole tidy

`git reset --hard backup/<branch>`, with a clean working tree.

## Never

- Never tidy history someone else has, even "only a message": a bad
  message on a pushed commit stays; a bad change is reverted.
- Never `git rebase -i` without `GIT_SEQUENCE_EDITOR` set to `:` or a
  plan script; never the verbs `reword`, `squash`, `edit`, `break`.
