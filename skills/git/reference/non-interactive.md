# Nothing waits: editors, pagers, prompts

An agent cannot type into an editor, page through output or answer a
password prompt. A command that waits for one hangs the task. Every fact
here was run on git 2.43.0 on Linux: once with stdin not a terminal, and
once under a pseudo-terminal, since Zed's terminal may be one (`not run
on Windows`).

## The session settings

| Variable | Value | Why (lab) |
| --- | --- | --- |
| `GIT_EDITOR` | `:` | git treats `:` as "no editor" without running anything (`editor.c`: `if (strcmp(editor, ":"))`); with `PATH` empty, `GIT_EDITOR=:` still finished a rebase while `GIT_EDITOR=true` failed |
| `GIT_SEQUENCE_EDITOR` | `:` | the rebase todo list is taken as it is; used with `--autosquash` |
| `GIT_PAGER` | `cat` | git starts no pager for `cat` (`pager.c`: `!strcmp(pager, "cat")`) |
| `GIT_TERMINAL_PROMPT` | `0` | a missing password fails at once: `fatal: could not read Username for '<url>': terminal prompts disabled` |
| `GIT_MERGE_AUTOEDIT` | `no` | `git merge` without `--no-edit` stops asking for a message on a terminal (lab) |
| `GIT_SSH_COMMAND` | `ssh -o BatchMode=yes` | ssh fails instead of asking for a passphrase or a host key (not run: no ssh client in the lab) |

PowerShell: `recipes/session.ps1` (`not run on Windows`); POSIX:
`. recipes/session.sh`. The environment variables win over
configuration: with `GIT_EDITOR` set, `git -c core.editor=: ...` still
called the `GIT_EDITOR` program. For one command in POSIX shells:
`GIT_EDITOR=: git rebase --continue`; in PowerShell set `$env:GIT_EDITOR
= ':'` on the line before.

## Commands that open an editor

| Command | Opens the editor | Non-interactive form |
| --- | --- | --- |
| `git commit` (no `-m`, `-F`) | always | `git commit -m "..." [-m "..."]` or `-F msg.txt` |
| `git commit --amend` | always | `--no-edit`, or `-m` |
| `git commit --fixup=reword:<c>` | always; `-m` refused | an `amend!` commit (`reference/rewrite.md`) |
| `git merge` | only on a terminal (stdin and stdout) | `--no-edit` |
| `git merge --continue` | always | `git commit --no-edit` |
| `git revert` | only when stdin is a terminal | `--no-edit` |
| `git revert --continue`, `git cherry-pick --continue` | on a terminal | `GIT_EDITOR=:` first |
| `git rebase --continue` | always, when it must commit a resolution | `GIT_EDITOR=:` first |
| `git rebase -i` | always (the todo list) | `GIT_SEQUENCE_EDITOR=:` or `recipes/todo.py` |
| `reword`, `squash`, `edit`, `fixup -c` in a todo | always | `amend!` commits, `fixup -C` |
| `git tag -a <t>` | always | `-m "..."` |
| `git notes add` | always | `-m "..."` |
| `git branch --edit-description` | always | leave it out |

With the failing editor the lab saw: `error: There was a problem with
the editor '<editor>'.` and `Please supply the message using either -m or
-F option.` On a terminal git first prints `hint: Waiting for your editor
to close the file...`: if you see that line, the command is waiting.
With `GIT_EDITOR=:`, `git commit` without `-m` stops with `Aborting
commit due to empty commit message.` and `git tag -a v9` with `fatal: no
tag message?`.

## Commands that read the keyboard

| Command | With stdin not a terminal (lab) | On a terminal held open (lab) | Use instead |
| --- | --- | --- | --- |
| `git add -p` | prints the prompt, stages nothing, exits 0 | still waiting after 4 s | `recipes/stage_hunks.py` |
| `git clean -i` | `What now> Bye.`, removes nothing | still waiting after 4 s | `git clean -n`, then `-f` with paths |
| a credential prompt | `could not read Username ...: No such device or address` | `Username for '<url>':` and waits | `GIT_TERMINAL_PROMPT=0` |

`git stash drop` and `git clean -f` ask nothing: they act at once.

## Pagers

Under a terminal these started the pager in the lab: `log`, `diff`,
`show`, `branch`, `tag`, `config --list`, `reflog`, `blame`, `grep`,
`help -a`. `status` did not. With stdout not a terminal no command
paged. `GIT_PAGER=cat`, `git --no-pager <cmd>` or `git -P <cmd>` each
stopped it.

## Help

`git <cmd> -h` prints the options and exits 129. `git help <cmd>` and
`git <cmd> --help` open a manual page (on the lab's minimal Linux, no
viewer was installed); Git for Windows opens a browser by default (`not
run on Windows`). Use `-h`.

## The hang test this skill passed

Every command in `core/`, `recipes/` and `examples/` was run with
`GIT_EDITOR` and `GIT_SEQUENCE_EDITOR` set to a script that records its
call and exits 1, and stdin from `/dev/null`. Commands that need an
editor variable carry it (`GIT_EDITOR=: git rebase --continue`).
