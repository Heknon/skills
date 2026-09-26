# Glossary

One sentence per term. Use these words and no synonyms.

| Term | Meaning |
| --- | --- |
| working tree | The files on disk as you edit them. |
| index | What the next commit will contain; `git add` copies a file from the working tree into it; also called the staging area. |
| staged | A change copied into the index; `git diff --cached` shows it. |
| untracked | A file git has never been told about; `??` in `git status --short`. |
| ignored | An untracked file matched by `.gitignore`; `!!` in `git status --short --ignored`; a tracked file is never ignored. |
| HEAD | The commit you are on; normally through a branch. |
| detached HEAD | HEAD pointing at a commit instead of a branch; commits made there belong to no branch. |
| branch | A movable name for a commit, in `refs/heads/`. |
| remote-tracking branch | Your copy of a branch on a remote, such as `origin/main`; updated only by `fetch` or `pull`. |
| upstream | The remote-tracking branch a local branch compares with; `@{u}`; shown by `git status -sb` as `...origin/x`. |
| ahead, behind | Commits on your branch and not upstream, and the reverse; `[ahead 1, behind 1]` means the two have diverged. |
| pushed | A commit reachable from any remote-tracking branch (`git branch -r --contains <commit>` lists it). |
| base | The common ancestor of the two sides of a merge; stage 1 of a conflicted file. |
| ours | Stage 2: in a merge, the branch you are on; in a rebase, the branch you are rebasing onto. |
| theirs | Stage 3: in a merge, the branch being merged in; in a rebase, your commit being replayed. |
| conflict markers | The lines `<<<<<<<`, `\|\|\|\|\|\|\|` (zdiff3 only), `=======`, `>>>>>>>` git writes into a conflicted file. |
| operation in progress | A merge, rebase, cherry-pick, revert or bisect that stopped and waits for `--continue`, `--abort` or `reset`. |
| stash | A saved set of uncommitted changes, kept as commits under `refs/stash`; `stash@{0}` is the newest. |
| reflog | The local record of where HEAD and each branch pointed, with `HEAD@{n}` names; never pushed; `gc` expires entries after 90 days, or 30 for commits no branch reaches (defaults in the 2.43.0 source). |
| dangling commit | A commit no branch, tag or reflog reaches, such as a dropped stash; `git fsck --no-reflogs` lists them. |
| fast-forward | Moving a branch forward to a descendant without a merge commit. |
| merge commit | A commit with two parents; parent 1 is the branch you were on. |
| rebase | Replaying commits on a new base, making new commits with new hashes. |
| rewrite | Any command that replaces commits with new ones: rebase, amend, reset to an older commit then commit, filter-repo. |
| backup branch | A branch made at the old tip before a rewrite, such as `backup/feature-x`, to compare with and to undo. |
| fixup commit | A commit titled `fixup! <subject>` that autosquash folds into the commit with that subject, keeping its message. |
| amend commit | A commit titled `amend! <subject>` whose body replaces that commit's message when autosquashed. |
| autosquash | Rebase moving `fixup!` and `amend!` commits after their targets and folding them in. |
| todo list | The list of commands an interactive rebase follows, one line per commit, edited by the sequence editor. |
| sequence editor | The program git runs to edit a rebase todo list: `GIT_SEQUENCE_EDITOR`, then `sequence.editor`, then the editor. |
| trailer | A `Key: value` line at the end of a commit message, such as `Co-authored-by:`; git parses only this form. |
| convention | The repository's rule for messages or names, found in a file, a tool's config, or most of the last 30 subjects. |
| bundle | A file holding commits and refs that `git fetch` and `git clone` read like a remote. |
| prerequisite | A commit a bundle assumes the receiver has; `git bundle verify` lists it as required. |
| worktree | An extra working folder of the same repository, with its own branch checked out. |
| submodule | A repository pinned at one commit inside another; the outer repository records only that commit. |
| bisect | A binary search over history for the first commit where a test fails. |
