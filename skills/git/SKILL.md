---
name: git
description: Safe everyday git for work that must not be lost. Say what state a repository is in, commit exactly the files meant, write commit messages and branch and tag names the way the repository already does, tidy a branch's unpushed history before review (squash, fixup, reword, reorder, split), create, rename and track branches, merge or rebase main in, resolve conflicts from the base, undo a commit, a staging, a merge or a pushed change, stash, cherry-pick and use worktrees, bisect a regression, recover lost commits and dropped stashes, stop tracking junk, fix line-ending churn, handle a committed secret or huge file, update submodules, carry work across the air gap with bundles or patches, and push. Every command is in a form that never waits for an editor, pager or password. Verified on git 2.43.0, with newer behaviour checked on 2.55.0.
---

# Git

This skill knows how git behaves when changing a repository, and every
command, option, message and default in it was run on git 2.43.0 (and,
where it says so, 2.55.0). Nothing is written from memory: check a flag
with `git <command> -h`, never `--help` (it opens a manual or a browser).

Reading history to answer a question (blame, `log -S`, `log -L`, who and
why) is the navigation skill's; this skill reads only as a step of a
change.

## First, every session

```
git --version
$env:GIT_EDITOR = ':'            # ':' is handled inside git: no program runs
$env:GIT_SEQUENCE_EDITOR = ':'
$env:GIT_PAGER = 'cat'           # 'cat' is handled inside git: no pager
$env:GIT_TERMINAL_PROMPT = '0'   # fail instead of asking for a password
$env:GIT_MERGE_AUTOEDIT = 'no'
$env:GIT_SSH_COMMAND = 'ssh -o BatchMode=yes'
```

Why each one, and the POSIX form: `reference/non-interactive.md`. The
values `:` and `cat` were checked in git's source and on Linux; under Git
for Windows they are `not run on Windows`. Never write global
configuration unasked; propose it. `reference/versions.md` says what
differs by version.

## The kinds of task

| Kind | You were asked to | Load |
| --- | --- | --- |
| **Orient** | say what state the repository is in | `core/orient.md` |
| **Commit** | commit a change | `core/commit.md`, `core/name.md` |
| **Name** | write a commit message, name a branch or a tag | `core/name.md`, `reference/conventions.md` |
| **Tidy** | clean up a branch's history before review | `core/tidy.md`, `reference/rewrite.md` |
| **Branch** | create, switch, rename, delete or track a branch | `core/branch.md` |
| **Integrate** | bring main into a branch, or a branch into main | `core/integrate.md` |
| **Conflict** | resolve a conflict in a merge, rebase, cherry-pick, revert or stash | `core/conflicts.md` |
| **Undo** | undo a commit, a change, a staging, a merge | `core/undo.md` |
| **Move work** | stash, cherry-pick, or work in a second worktree | `core/move-work.md` |
| **Bisect** | find the commit that broke something | `core/bisect.md` |
| **Recover** | find lost commits, a dropped stash, undo a bad reset | `core/recover.md` |
| **Clean up** | ignore files, stop tracking junk, fix line endings, a huge file | `core/clean-up.md` |
| **Secret** | a key, token or password was committed | `core/secrets.md` |
| **Submodule** | clone, update or move a submodule | `core/submodules.md` |
| **Carry** | move work across the air gap | `core/carry.md` |
| **Push** | push or publish a branch or tag | `core/push.md` |

Most tasks start with **Orient**. Before any command outside the reads
class, look up its class in `reference/risk.md`.

## Where the facts are

| Folder | Holds |
| --- | --- |
| `core/` | the procedures above, each ending in a verdict |
| `reference/` | `non-interactive.md` (every editor, pager and prompt trap), `risk.md` (each command's class), `rewrite.md` (each tidy recipe and its undo), `conventions.md` (messages, trailers, branch and tag names), `windows.md` (quoting, line endings, paths, case, credentials), `versions.md` |
| `recipes/` | `session.ps1` and `session.sh` (the settings above), `todo.py` (a sequence editor that follows a plan you wrote), `stage_hunks.py` (stage some hunks without `add -p`), `bisect_test.py` with `bisect-test.ps1` and `.sh`, `eol.py`, `example.gitattributes` and `example.gitignore` |
| `examples/` | a conflict resolved from the base, a lost branch recovered, a bisect run, a branch carried by bundle |

`glossary.md` fixes the words.

## Invariants

1. **Status before and after.** Run `git status` before any change and
   after it. The short form hides a merge, rebase, cherry-pick or bisect
   in progress; read the long form when anything is under way.
2. **Save before you destroy.** Before a command that destroys
   uncommitted work (`reset --hard`, `restore .`, `checkout -- .`,
   `clean`, `stash drop`), stash with `--include-untracked` or commit to
   a backup branch, and say where it went. Never `clean -x` unasked: it
   deletes ignored files such as `.env` and `.venv`.
3. **Pushed history is not rewritten.** A commit on a remote branch is
   undone with `revert`, never `reset`, `--amend` or `rebase`, unless the
   person says the branch is theirs alone. Then push only with
   `--force-with-lease --force-if-includes`. Never plain `--force`.
4. **Stage by name.** `git add -- <path>`, then `git diff --cached
   --stat`. Never `git add .` or `-A` without reading `git status` first.
5. **Nothing waits.** Every command here is in a form that cannot open
   an editor, a pager or a prompt. Never `add -p`, `clean -i`,
   `rebase -i` without a sequence editor, `commit` without `-m` or `-F`,
   or `--help`.
6. **A conflict is resolved from the base.** Read what each side changed
   from the base before writing the result. `ours` and `theirs` swap in a
   rebase. Search for markers and run the tests before `git add`.
7. **Nothing is lost until the reflog says so.** Before saying work is
   gone, read `git reflog` and `git fsck --no-reflogs`.
8. **Finish what you start.** No merge, rebase, cherry-pick, revert or
   bisect is left in progress when you answer (`core/orient.md`).
9. **Follow the repository's names.** Commit messages, branch and tag
   names follow the convention found (`core/name.md`); say where it was
   found.
10. **Nothing leaves this machine unasked.** Push, a bundle handed over,
    a tag pushed: only when the person asked for that action.

## What you say when you finish

End with these headings, each with `none` when empty. If another skill
is loaded, its headings come first and these after.

```
## Result
<what changed: branches, commits (hash and subject), files; where saved work is>

## State
<git status -sb after, and "nothing in progress", or what is and why>

## Checked
<each command that proves the result, with the line of output that shows it>

## Not checked
<what could only be seen on the server, another clone, or Windows>
```

The `evals/` folder is for people testing this skill. Never open it
while doing a task.
