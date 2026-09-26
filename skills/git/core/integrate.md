# Integrate: merge or rebase

**Verdict you produce:** how the branch was brought up to date, why that
way, and the tests after.

```
method:  <merge | rebase> because <pushed | not pushed | the person's own branch, said by them>
result:  <merge commit hash | new tip hash>; git status -sb: <line>
tests:   <command and summary>
verdict integrate: <integrated | conflict: see conflicts | stopped: <why>>
```

## Decide

1. `git fetch origin`, then `git status -sb`.
2. Is the branch pushed? `git branch -r --contains <oldest commit of the
   branch>`.
   - **Pushed**: merge. Rebasing rewrites commits others may have.
   - **Not pushed**, or the person says the branch is theirs alone:
     rebase is allowed and gives a straight history; merge is still fine.
3. If the upstream has commits you lack (`behind`), bring those in first:
   `git merge --no-edit origin/<branch>`. A colleague may have pushed to
   your branch.

## Merge

```
git merge --no-edit origin/main
```

`--no-edit` is required. On 2.43.0 `git merge` opens the editor for the
merge message only when stdin and stdout are a terminal (source:
`default_edit_option` in `builtin/merge.c`); in the lab it merged
silently with no terminal and, under a terminal, called the editor and
stopped: `Not committing merge; use 'git commit' to complete the merge.`
Zed's terminal may be one (`not run on Windows`). `GIT_MERGE_AUTOEDIT=no`
also stops it.

A conflict: `core/conflicts.md`. Finish with `git commit --no-edit`.
`git merge --continue` opens the editor even with no terminal (lab:
`Please supply the message using either -m or -F option.`).

## Rebase

Only after step 2 allows it:

```
git branch backup/<branch>
git rebase origin/main
```

A conflict stops it: resolve (`core/conflicts.md`, where ours and
theirs swap), `git add`, then `GIT_EDITOR=: git rebase --continue`.
`git rebase --abort` puts everything back.

## After

- Run the tests. A merge with no conflict can still break the code.
- `git status`: nothing in progress, and the ahead and behind you expect.
- `git log --oneline --graph -10`.

## The trap this avoids

In the lab (`evals` sandbox shared-rebase), the person's branch was
pushed and a colleague had pushed `Quote CSV fields that contain commas`
to it; the person had fetched. `git rebase origin/main` then `git push
--force-with-lease` **succeeded** and replaced the remote branch, and the
colleague's commit was gone from it: `+ 641f5d6...b782a4a feature/export
-> feature/export (forced update)`. The lease passed because the fetch
had updated `origin/feature/export`. With `--force-if-includes` added,
the same push was rejected: `! [rejected] feature/export ->
feature/export (remote ref updated since checkout)`. Merging kept both.
