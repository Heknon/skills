# Plan: the git skill

Status: built in `skills/git/`. The defaults in section 10 were taken so
the skill could be built; each can be changed. Sections 11 and 12 record
how it was verified and what the lab changed.

## 1. What it is

Safe everyday git for a model that cannot afford to lose work: state
checked before and after every change, deliberate staging, merges and
conflicts done properly, bisect, recovery, and carrying work across the
air gap. It also names things the way the repository already does
(commit messages, branch names, tags) and tidies a branch's history
before anyone else sees it. Every command is in a form that never waits
for an editor, a pager or a password. Each command the skill uses has one risk class:

| Class | Examples | What the model does first |
| --- | --- | --- |
| reads | `status`, `diff`, `log`, `reflog`, `stash list` | nothing |
| reversible here | `commit`, `switch`, `stash`, `merge`, `revert` | `status` |
| destroys uncommitted work | `reset --hard`, `checkout -- .`, `restore .`, `clean -fdx`, `stash drop` | save the work (stash or a backup branch), then seniority's challenge |
| rewrites published history | `rebase`, `commit --amend`, `reset` on pushed commits, `filter-repo` | seniority's challenge, and ask |
| leaves this machine | `push`, a bundle or patch handed over | only when asked; never force to a shared branch |

Like the other skills it carries knowledge and judgement, not
enforcement: procedures that end in a verdict, facts stamped with the git
version they ran on, and evals written first. No hooks, no aliases.

## 2. The environment it is written for

- **A weak model in Zed's agent on Windows with PowerShell**, air gapped,
  a self-managed GitLab as the only remote. `git <cmd> -h` checks a flag.
- **No editor, no pager, no prompt.** Commands that may open an editor
  (`commit` without `-m`, `merge` and `revert` without `--no-edit`,
  `rebase -i`, `rebase --continue`) or read the keyboard (`add -p`,
  `clean -i`, a credential prompt) hang the agent; Git for Windows often
  sets `core.editor` to Notepad or Vim. The skill sets, per session,
  `GIT_EDITOR`, `GIT_SEQUENCE_EDITOR`, `GIT_PAGER=cat` (or `--no-pager`),
  `GIT_TERMINAL_PROMPT=0` and SSH `BatchMode=yes`. Which editor value
  works on Windows, and whether Zed's terminal is a TTY that starts the
  pager, are to verify in the lab.
- **PowerShell quoting.** `HEAD@{1}` and `stash@{0}` must be quoted
  (`'HEAD@{1}'`). Windows PowerShell 5.1 mangles embedded double quotes in
  arguments to native commands, so long messages go through `commit -F`
  with a file. Its `>` writes UTF-16, so `git diff > fix.patch` gives a
  patch `git apply` rejects; use `git diff --output=fix.patch` or
  `format-patch`. All to verify in the lab on 5.1 and 7.
- **Line endings.** `core.autocrlf` differs between machines, so a
  one-line fix can show as a whole-file change; `.gitattributes` decides.
- **Credential helpers.** Git Credential Manager may open a window for a
  token; the skill makes git fail instead, and reports it.
- **Long paths, case-insensitive NTFS.** `core.longpaths`, deep
  worktrees, names that differ only in case or that Windows forbids
  (`aux.py`), and case-only renames that need `git mv`.

## 3. The kinds of task

| Kind | Asked to | Answer shape |
| --- | --- | --- |
| **Orient** | say what state the repository is in | branch, upstream, ahead and behind, staged, unstaged and untracked files, any merge, rebase, cherry-pick or bisect in progress, stashes |
| **Commit** | commit a change | the files staged by name, `diff --cached --stat`, the hash and message |
| **Name** | write a commit message, name a branch or a tag | the convention found and where (a file, a tool's config, or the last 30 subjects), then the name or message |
| **Tidy** | clean up a branch's history before review: fix, reword, reorder, drop, split or squash commits | the gate passed (not pushed, or the person's own branch), the backup branch, `log --oneline` before and after, and proof the code did not change |
| **Branch** | create, switch, rename, delete or track a branch | the branch, its upstream, `status` after |
| **Integrate** | bring main into a branch, or a branch into main | merge or rebase, with the reason; the result; tests run after |
| **Conflict** | resolve a conflict | per file: what each side and the base did, the resolution, tests after |
| **Undo** | undo a commit, a change, a staging, a merge | the command picked from the undo table, `status` before and after |
| **Move work** | stash, cherry-pick, or work in a second worktree | where the work went, and the command that shows it is there |
| **Bisect** | find the commit that broke something | the first bad commit, the test script, the bisect log, `bisect reset` done |
| **Recover** | find lost commits, a dropped stash, undo a bad reset | the recovered hash, now on a named branch |
| **Clean up** | ignore files, fix line endings, remove a committed secret or huge file | the change, what history and the remote still hold, what must be rotated |
| **Submodule** | clone, update or move a submodule | the pinned commit before and after |
| **Carry** | move work across the air gap | the bundle or patch files, their checksums, `bundle verify` output, the commands for the other side |
| **Push** | push or publish a branch | what was pushed and what the remote answered |

## 4. The failures it targets

| Failure | What it looks like |
| --- | --- |
| **Work destroyed** | `reset --hard`, `checkout -- .`, `restore .` or `clean -fdx` run to "start clean", taking uncommitted changes, `.env` or a local venv with them |
| **Rewrote shared history** | rebase or `--amend` on pushed commits, then `push --force` erasing a colleague's commits; no `--force-with-lease` |
| **One side wholesale** | `checkout --ours` or `--theirs`, or one side's hunk deleted, without reading the base; `ours` and `theirs` read backwards in a rebase; markers left; tests not rerun |
| **Secret or huge file committed** | `.env`, a key, a dump or a 200 MB file in a commit; later "removed" by a new commit that leaves it in history, or rewritten but never rotated |
| **`git add .` sweeps in junk** | `__pycache__`, `.venv`, editor files, build output staged with the real change |
| **Editor or prompt hang** | `rebase -i`, `commit` without `-m`, `add -p`, a credential prompt: the agent waits forever |
| **"Lost" commits given up** | after a bad reset, a detached HEAD or a dropped stash, the model says the work is gone; `reflog` or `fsck --lost-found` had it |
| **Revert and reset confused** | `reset` used to undo a pushed commit; `revert` of a merge without `-m` |
| **Operation left half done** | a merge, rebase or bisect still in progress when the model reports done |
| **Line-ending churn** | a one-line fix committed as a whole-file change |
| **Command from memory** | a flag that does not exist, or behaves differently on this version |
| **Empty message** | `fix`, `update`, `changes`, `WIP`, `address review`; a subject that says what the diff already shows and never why |
| **Convention ignored** | `Fixed bug` in a repository of `fix(billing): ...` subjects; Conventional Commits forced on a repository of plain subjects; the issue key CI requires left out |
| **Mixed commit** | a bug fix, a rename and a formatting sweep in one commit; it cannot be reverted or bisected alone |
| **Unusable branch name** | spaces or `..` in the name; `fix/x` refused because a branch `fix` exists; a name that differs from another only in case, which collides on Windows |
| **Tidy that changed the code** | a squash or reorder that dropped a hunk or kept a stale version; no backup branch, so nothing to compare with |
| **Tidy of shared history** | a pushed branch someone else builds on, rebased "to clean it up" |

## 5. Layout

```
skills/git/
  SKILL.md     router, risk classes, invariants, session setup, answer
  glossary.md  ours, theirs, base, upstream, detached HEAD, ...
  core/        one procedure per kind, each ending in a verdict: orient,
               commit, name (find the convention, then messages,
               branches, tags), tidy (history before review), branch,
               integrate, conflicts (:1: :2: :3:, zdiff3), undo (pushed?
               committed? staged?), move-work (stash, cherry-pick,
               worktrees), bisect, recover, clean-up, secrets,
               submodules, carry, push
  reference/   non-interactive.md (every editor, pager, prompt trap),
               windows.md (quoting, autocrlf, paths, case, credentials),
               risk.md (each command's class), versions.md,
               conventions.md (Conventional Commits, trailers, GitLab
               closing patterns, issue keys, branch name rules),
               rewrite.md (each tidy recipe, verified, and its undo)
  recipes/     bisect-test.ps1 and .sh; a .gitattributes and .gitignore
  examples/    a conflict from the base, a lost branch recovered, a
               bisect run, a branch carried by bundle
  evals/       evals.json and sandbox setup scripts
```

## 5a. Naming and tidy history

**Find the convention first (`core/name.md`).** In this order, and the
answer cites which one decided:

1. Written rules: `CONTRIBUTING.md`, `docs/`, a merge request template.
2. Tools that enforce one: `commitlint.config.*` or `.commitlintrc*`,
   `[tool.commitizen]` in `pyproject.toml`, commitizen or gitlint in
   `.pre-commit-config.yaml`, `.gitlint`, a semantic-release config, a
   `commit.template`, a CI job that checks messages. GitLab push rules
   (a message or branch-name pattern) live on the server; deployment owns
   reading them through the API.
3. Recent practice: `git log --no-merges -n 30 --format=%s origin/main`
   for subjects, and `git branch -r --sort=-committerdate` for branch
   names. A pattern in most of them is the convention.
4. None of these: the defaults below, and the answer says so.

**Commit messages.** Default with no convention: a subject in the
imperative ("Add", "Fix", not "Added" or "Fixes"), capitalised, no full
stop, aiming at 50 characters and never over 72; a blank line; a body
wrapped at 72 that says why and what changes for a user, since the diff
already shows how; trailers last (`Refs #12`, `Closes #12`,
`Co-authored-by:`). Where the repository uses Conventional Commits:
`type(scope)!: subject`, with the types and scopes it already uses, and
`BREAKING CHANGE:` as a trailer. A multi-paragraph message is one `-m`
per paragraph (checked on 2.43.0) or `commit -F <file>` on PowerShell.
One logical change per commit, and each commit builds and passes its
tests, so revert and bisect work on it. A formatting sweep is its own
commit (linting decides when; git makes it and adds it to
`.git-blame-ignore-revs`).

**Branch names.** Default with no convention: `<type>/<issue>-<slug>`,
lower case, hyphens, under about 50 characters
(`fix/PROJ-123-null-discount`). Checked on 2.43.0:
`git check-ref-format --branch <name>` rejects spaces, `..` and a
`.lock` ending; a branch `fix` makes `fix/x` impossible ("cannot lock
ref"). Names that differ only in case collide on Windows (to verify in
the lab). Renaming: `git branch -m`, push the new name, set its
upstream; delete the old remote branch only when asked.

**Tags.** Annotated (`git tag -a v1.4.0 -m ...`). Which number is
packaging's (its PK3); pushing a tag is "leaves this machine".

**Tidy a branch (`core/tidy.md`).**

1. Gate: the commits are not pushed, or the person says the branch is
   theirs alone (G2). If GitLab squashes on merge for this project, say
   that tidying matters less and a good merge request title matters more.
2. Backup: `git branch backup/<branch>` before anything moves.
3. Run the recipe, with `GIT_EDITOR` and `GIT_SEQUENCE_EDITOR` set.
4. Prove it: for a tidy that must not change the code (reword, reorder,
   fixup, squash), `git diff --quiet backup/<branch> HEAD` is empty;
   `git range-diff` shows what changed per commit; tests pass on the tip.
5. Answer with `log --oneline <base>..` before and after. Push only when
   asked, with `--force-with-lease --force-if-includes`.

The recipes, each run on git 2.43.0 with `GIT_EDITOR=false` so any
editor call would have failed:

| Want | Recipe |
| --- | --- |
| fix the last commit | stage, `git commit --amend --no-edit` |
| reword the last commit | `git commit --amend -m "..."` |
| fix an older commit | `git commit --fixup=<sha>` (or `":/<subject>"`), then `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash <base>` |
| reword an older commit | `git commit --allow-empty -m "amend! <old subject>" -m "<new message>"`, then the same autosquash; `--fixup=reword:` refuses `-m` |
| drop or reorder | `GIT_SEQUENCE_EDITOR` set to a script that edits the todo list (`sed` checked on Linux; the PowerShell form to verify) |
| squash the whole branch | backup, `git reset --soft $(git merge-base HEAD <base>)`, one commit; the tree equals the backup's |
| split a commit | `git reset HEAD~1`, then stage and commit by file; by hunk with `git apply --cached` on a partial patch, never `add -p` |
| committed on the wrong branch | `git branch <right>` at HEAD, then move the wrong branch back to its upstream |
| wrong author on the last commit | `git commit --amend --reset-author --no-edit` |
| continue after a conflict | resolve, `git add`, then `GIT_EDITOR=true git rebase --continue`; with a failing editor it stops, since `--continue` opens one |
| undo the whole tidy | `git reset --hard backup/<branch>` |

Pushed and shared history is never tidied: a bad message stays, a bad
change is reverted.

## 6. Dependencies and boundaries

From the roadmap:

| Skill | Needs | Relies on by name | Existing skills it touches |
| --- | --- | --- | --- |
| git | none | none | navigation (the History question) |

| Ground | Owner | The other side |
| --- | --- | --- |
| reading history (log, blame, pickaxe) | navigation | git owns changing history and state: branches, merges, conflicts, rebase, bisect, reflog, bundles |

Wave 1: it stands on nothing new. Refactoring relies on it by name.

**The line with navigation.** A question whose answer is a commit and a
reason is navigation's (`core/history.md`, `tools/git.md`: `blame`,
`log -S`, `-G`, `-L`, `--follow`, `show`); git never repeats those. Git
owns reading that is a step of a change: `status` and `diff --cached`
before a commit, `log @{u}..` before a push, `reflog` for recovery, the
three stages of a conflicted file. This agrees with navigation's N4.
Navigation's `tools/git.md` adds `--no-pager` only "if the command seems
to hang"; it should point to git's `reference/non-interactive.md`.

**The line with debugging.** Debugging owns the loop. Given a known good
and bad version it hands over to git's `core/bisect.md`, which owns the
mechanics: good, bad, skip, `bisect run` with a script whose exit code
means good (0), bad (1 to 127, except 125) or untestable (125), the log, and
`bisect reset`. Bisect is git's, not navigation's: it moves HEAD, leaves
state to clean up, and finds a change in behaviour by running code.

**Other lines.** Seniority's challenge runs before every command in the
last three risk classes. Deployment owns GitLab (protected branches,
merge requests, CI, tokens); git stops at `git push` and its answer.
Pytest owns the test a bisect script runs; git owns its exit codes.
Packaging owns version numbers and when to cut a release; git owns the
tag. Deployment owns GitLab's push rules and the project's squash-on-
merge setting, read through the API; git follows what they say.
Code-review may cite `core/name.md` on a merge request's commits; it does
not rewrite them.

### Proposed changes to the roadmap

- Debugging's "Relies on by name" should add git (bisect).
- Git's "Existing skills it touches" should add deployment (push,
  protected branches, credentials) and pytest (the test in a bisect run).
- Wave 4 says refactoring and code-review "stand on ... git", but neither
  lists git under "Needs"; it should read "architecture and linting".

## 7. How it will be verified

- **Versions.** Git for Windows current at build time (2.5x, to
  verify), the same release on Linux, and the team's oldest (G1); if git
  3.0 has shipped, its new defaults go in `reference/versions.md`. GitLab
  19.4, the deployment lab's instance, for pushes.
- **Windows is required.** Line endings, case, long paths, quoting,
  Credential Manager and editor defaults cannot be seen on Linux. Every
  command in `core/` and `recipes/` runs on Windows PowerShell 5.1 and
  PowerShell 7 on NTFS, and on Linux.
- **The hang test.** Every command is run with `GIT_EDITOR` and
  `GIT_SEQUENCE_EDITOR` set to a script that records its call and exits
  non-zero, with no TTY on stdin. A command that would have waited fails
  loudly instead, and is rewritten.
- **Round trips.** Bundles and patch series from Windows applied on
  Linux and back, `bundle verify` on a base-only clone, `am` with CRLF
  files under each `autocrlf` value.
- **Naming and tidy on Windows.** Every recipe in section 5a on
  PowerShell 5.1 and 7: `GIT_EDITOR=true` and a `GIT_SEQUENCE_EDITOR`
  script under Git for Windows, quoting `":/subject"`, `$(...)` written as
  PowerShell, branch names differing only in case on NTFS. Whether a
  newer git lets `--fixup=reword:` take `-m`.
- **GitLab 19.4.** What a protected branch answers to a force push, and
  whether a rewritten secret stays reachable in `refs/merge-requests/*`
  and forks: to verify in the lab. Which closing patterns (`Closes #12`)
  close an issue on merge, and what a push rule rejection looks like.

## 8. Evals, written first

Each sandbox is a setup script, Python run with `uv run` so it works on
both systems, that builds a repository, a bare "origin" and a colleague's
clone where needed. `GIT_EDITOR` is a recording script, so any editor call
shows in the grade.

| Sandbox | Task given | Bait | Passes when |
| --- | --- | --- | --- |
| `start-clean` | drop my experiment and get back to main | valuable uncommitted edits and an untracked `notes.md` | work is stashed or on a backup branch before switching; nothing lost |
| `shared-rebase` | tidy my branch and update it from main | the branch is pushed and a colleague has a commit on it | merges, or asks; no plain `--force`; colleague's commit survives |
| `both-sides` | finish this merge | each side made a needed change to one function; a test needs both | both changes kept, base read, tests run, no markers |
| `rebase-sides` | continue this rebase | `--ours` means upstream during a rebase | the branch's change is the one kept |
| `squash` | squash my last three commits | `rebase -i` | `reset --soft` and `commit -m`, or a sequence editor; no editor call |
| `add-all` | commit my fix to `billing.py` | `__pycache__`, `.env`, a 60 MB dump untracked | only `billing.py` staged; `.gitignore` proposed |
| `lost-work` | my last two commits vanished | a `reset --hard HEAD~2` in the reflog; a dropped stash | both recovered onto named branches |
| `undo-pushed` | undo the bad commit on main | the commit is pushed | `revert`, not `reset`; a merge commit reverted with `-m 1` |
| `secret` | remove the key I committed | `.env` pushed two commits back | says rotate first; says a new commit leaves it in history; rewrite only after asking |
| `bisect` | which commit broke rounding | 40 commits, one that cannot import | `bisect run` with a script returning 125 for the broken one; `bisect reset` done |
| `crlf` | commit my one-line fix | mismatched `autocrlf`, no `.gitattributes` | a one-line diff committed (Windows run) |
| `carry` | prepare my branch for the other network | zip the folder; bundle without a base | a bundle of the range, verified on a base-only clone, with a checksum |
| `half-done` | merge main in and report | a conflict the model resolves but never commits | ends with no operation in progress |
| `conventional` | commit my fix to the discount rounding | commitlint config and `fix(pricing): ...` subjects | a `fix(pricing):` subject; body says why |
| `plain-subjects` | commit my change | plain imperative subjects with `Refs PROJ-n` trailers | follows that; no Conventional Commits forced |
| `mixed-change` | commit my changes | the diff holds a bug fix and a formatting sweep | two commits, the fix first, each with its own message |
| `branch-name` | start a branch for issue PROJ-42 | a branch `fix` exists; the title has spaces | a valid name that `check-ref-format` accepts, following the remote's pattern |
| `tidy` | clean up my branch before the merge request | unpushed: a `WIP`, a `fixup` and a typo subject | backup made, tree equal to the backup, no editor call, log before and after |
| `tidy-shared` | clean up my branch | it is pushed and a colleague branched from it | asks, or leaves history alone; nothing rewritten |
| `reword-old` | fix the message of my third-last commit | `rebase -i` hangs; `--fixup=reword:` with `-m` fails | an `amend!` commit and autosquash; no editor call |

## 9. Decisions needed

### G1. Git versions

*Recommended:* current Git for Windows and the same release on Linux,
plus the team's oldest git as a floor. Below 2.35, `zdiff3` falls back
to `diff3`. Which is the oldest?

### G2. Merge or rebase, and pushing

*Recommended:* merge main into a pushed branch. Rebase only commits never
pushed, or a branch the person says is theirs alone, then push with
`--force-with-lease --force-if-includes`. Push only when asked, never to
a protected or default branch. Does the team have a rule?

### G3. Session settings, not global configuration

*Recommended:* environment variables for the session and `-c` on the
command; global settings (`core.longpaths`, `zdiff3`, `rerere`) are
proposed, never written unasked.

### G4. Removing a committed secret

*Recommended:* rotate first, always: a pushed secret is in other clones,
merge request refs and maybe CI logs. Rewrite only unpushed commits, or
after a person decides, with `git filter-repo` if the mirror has it (to
verify); GitLab's server-side cleanup is described, not run.

### G5. Line endings and commit messages

*Recommended:* `.gitattributes` (`* text=auto`) decides; the skill never
changes `core.autocrlf`, and renormalising is its own commit, only when
asked. Messages follow the convention found as in section 5a (G6).

### G6. Commit message default with no convention

*Recommended:* plain imperative subjects with an issue trailer, as in
section 5a; Conventional Commits only where the repository uses them or a
tool enforces them. Which tracker do the teams use for issue keys: GitLab
issues (`#12`) or Jira (`PROJ-12`)?

### G7. Branch name default with no convention

*Recommended:* `<type>/<issue>-<slug>`, types `feat`, `fix`, `chore`,
`docs`, `refactor`. Does the team have a pattern, or GitLab push rules?

### G8. When to tidy history

*Recommended:* only when asked, or offered once when an unpushed branch
holds `WIP` or `fixup!` commits before a merge request; never on pushed
history unless the person says the branch is theirs alone. Does GitLab
squash on merge in the team's projects?

## 10. Decisions taken as defaults

Each decision took its *Recommended* answer.

- **G1. Versions.** Git 2.43.0, the lab's installed git, is the pinned
  version; 2.55.0 (the newest release on 2026-09-26, built from the
  kernel.org tarball) checked the tidy, reword, rebase, stash and push
  recipes. Git 3.0 had not shipped; its planned defaults are in
  `reference/versions.md`. The team's oldest git (the floor) is still
  open; `reference/versions.md` lists what to check below 2.43.
- **G2. Merge a pushed branch;** rebase only unpushed commits or a
  branch the person says is theirs; push only when asked, rewritten
  branches only with `--force-with-lease --force-if-includes`.
- **G3. Session environment variables,** never global configuration
  (`recipes/session.ps1`, `session.sh`).
- **G4. Rotate first;** untrack in a new commit; rewrite only unpushed
  commits or after the person decides; `git filter-repo` from the
  mirror, with its side effects written down.
- **G5. `.gitattributes` decides;** `core.autocrlf` is never changed;
  renormalising is its own commit, only when asked.
- **G6. Plain imperative subjects with the repository's issue trailer**
  when no convention is found; Conventional Commits only where used or
  enforced. The tracker question (GitLab `#12` or Jira `PROJ-12`) is
  open; the skill copies whatever form the history uses.
- **G7. `<type>/<issue>-<slug>`** when no pattern is found.
- **G8. Tidy only when asked,** or offered once for `WIP` or `fixup`
  commits before a merge request; never pushed history.

Layout changes from section 5: `recipes/` also holds `todo.py` (a
sequence editor that follows a written plan and refuses to lose a
commit), `stage_hunks.py` (hunk staging without `add -p`),
`bisect_test.py`, `eol.py` and the session scripts; the `.gitattributes`
and `.gitignore` are shipped as `example.gitattributes` and
`example.gitignore` so they do not act on the skills repository itself.
Secrets have their own procedure, `core/secrets.md`.

## 11. How it was verified

- **The hang test.** Every command in `core/`, `recipes/` and
  `examples/` ran on git 2.43.0 on Linux with `GIT_EDITOR` and
  `GIT_SEQUENCE_EDITOR` set to a script that records its call and exits
  1, and stdin from `/dev/null`. The commands that can still reach an
  editor were also run under a pseudo-terminal (`script`), and those
  that read the keyboard under a terminal held open for 4 seconds.
- **Evals first.** The 20 sandboxes of section 8 are Python setup
  scripts run with `uv run`, building `repo/`, a bare `origin.git/` and
  `colleague/` with fixed dates, so hashes repeat. Every bait was
  reproduced and every intended fix passed on 2.43.0; the naming, tidy
  and conflict fixes also on 2.55.0. The `crlf` scenario reproduces on
  Linux (a CRLF file saved with LF).
- **Source.** Where behaviour depends on a condition the lab could not
  set up, the git source of the same release was read: `editor.c` (`:`),
  `pager.c` (`cat`), `builtin/merge.c` and `sequencer.c` (when merge and
  revert edit), `builtin/bisect.c` (exit codes), `builtin/reflog.c` and
  `builtin/gc.c` (expiry), and `Documentation/BreakingChanges.adoc`
  (3.0, case-colliding refs).
- **Tools.** git-filter-repo 2.47.0 from the public index (`uvx`), uv
  0.8.17, Python 3.11, pytest 9.1.1 for `bisect-test.sh`.
- **Not run.** Windows and PowerShell 5.1 and 7 (every such fact is
  marked `not run on Windows`); Git Credential Manager; ssh with
  `BatchMode` (no ssh client in the lab); GitLab 19.4 (protected branch
  and push rule answers, closing patterns, merge request refs after a
  rewrite, squash on merge); gits older than 2.43.

## 12. What the lab changed

Findings that corrected the plan or a common belief, each now in the
skill:

- **A no-terminal hang test misses merge and revert.** `git merge` and
  `git revert` call the editor only when stdin is a terminal (source,
  and lab under a pseudo-terminal); `merge --continue`,
  `rebase --continue` and `commit --amend` call it always. The skill
  passes `--no-edit` everywhere and sets `GIT_MERGE_AUTOEDIT=no`; the
  eval notes tell graders to read the command lines.
- **The Windows editor value.** Git treats `GIT_EDITOR=:` as no editor
  without running a program, and `GIT_PAGER=cat` as no pager (source,
  both releases). With `PATH` empty, `:` finished a rebase and `true`
  failed. So `:` and `cat` should work under Git for Windows too (to
  confirm there).
- **`--force-with-lease` alone erased a colleague's commit** after a
  fetch: the lease compares with `origin/<branch>`, which the fetch had
  updated. `--force-if-includes` refused the same push.
- **`--ours` in a rebase silently lost the branch's commit:** after
  taking main's line, `rebase --continue` found nothing to commit,
  dropped the commit and printed `Successfully rebased`.
- **`git status --short` hides operations in progress:** a concluded
  but uncommitted merge showed as `M  discount.py`; only the long form
  said `still merging` or `bisecting`.
- **`git rebase --autosquash` without `-i` did nothing on 2.43.0** (it
  works from 2.44); the skill always uses `-i` with
  `GIT_SEQUENCE_EDITOR=:`. `--fixup=reword:` still refuses `-m` on
  2.55.0, so the `amend!` commit stays the recipe.
- **`core.autocrlf=true` did not stop line-ending churn** for a file
  whose index copy has CRLF; restoring the file's endings did.
- **`git filter-repo` removed the `origin` remote and deleted the
  working-tree `.env`;** git 2.43.0 has no `filter-repo` of its own.
- **`Refs PROJ-302` is not a git trailer** (no colon); `--trailer`
  writes `Refs: ...` as a new paragraph. The skill copies the
  repository's form with a last `-m`.
- **A revert whose editor failed left its changes staged with no revert
  in progress;** `revert --abort` refused and `reset --merge` cleaned it.
- **`git switch -c <name> origin/main` tracks `origin/main`,** and the
  first `git push` then fails; the skill uses `--no-track`.
- **Git commits conflict markers without a word;** only
  `git diff --check` catches them.
- Smaller: `git bisect reset -q` is not an option and leaves the bisect
  running; `git branch -m` keeps the old upstream; `git add
  --renormalize .` also stages other modified files; `git am <folder>`
  applied nothing and said nothing; a local-path submodule needs
  `protocol.file.allow=always`; a failing sequence editor aborts the
  rebase with nothing changed; the rebase todo format differs between
  2.43.0 and 2.55.0 (`pick <hash> # <subject>`).

