# Windows and PowerShell

Every fact below marked `not run on Windows` is written from the plan
and from what git does on Linux; the lab had no Windows machine. What
git itself does with the bytes it receives was checked on Linux.

## Quoting in PowerShell (`not run on Windows`)

| Write | Why |
| --- | --- |
| `'HEAD@{1}'`, `'stash@{0}'`, `'@{u}'` | `{}` is a script block in PowerShell; quote anything with braces |
| `git log --oneline '@{u}..'` | the same |
| `git commit --fixup=':/Reject IBANs'` | `:/` with a space needs quotes anywhere |
| `git reset --soft (git merge-base HEAD origin/main)` | `$( )` and `( )` both run a command; or run `git merge-base` first and paste the hash |
| `git commit -F msg.txt` for a message with quotes | Windows PowerShell 5.1 mangles embedded double quotes in arguments to native programs |
| `$env:GIT_EDITOR = ':'` on its own line | PowerShell has no `VAR=value command` prefix |

## Files PowerShell writes (`not run on Windows`)

- `>` and `Out-File` in Windows PowerShell 5.1 write UTF-16. A patch
  written that way is refused: in the lab a UTF-16 copy of a good patch
  gave `error: No valid patches in input (allow with "--allow-empty")`.
  Use `git diff --output=fix.patch` or `git format-patch -o <dir>`
  (both write bytes git reads back: lab), or pipe into
  `recipes/stage_hunks.py`.
- A commit message file must be UTF-8 without a byte order mark: a BOM
  stays in the subject (lab), UTF-16 is refused (`a NUL byte in commit
  log message not allowed`). PowerShell 5.1's `Set-Content -Encoding
  utf8` writes a BOM; write the file with the editing tool instead.
- A `.gitignore` or `.gitattributes` saved as UTF-16 does not work
  (to verify on Windows); write them with the editing tool.

## Line endings

`core.autocrlf` differs between machines (it may be `true` on Windows,
set by the installer or by hand, `not run on Windows`), so the same file
can look changed on one and not the other. What was checked on Linux (`core/clean-up.md`):

- `git ls-files --eol` shows index and working tree endings.
- A file whose index copy has CRLF is not converted by
  `core.autocrlf=true`; saving it with LF shows every line changed.
- `* text=auto` in `.gitattributes` decides for everyone; renormalising
  is its own commit, only when asked.

Git warns when it will convert: `warning: in the working copy of
'billing.py', LF will be replaced by CRLF the next time Git touches it`
(lab, with `-c core.autocrlf=true`).

## Paths (`not run on Windows`)

- Paths over 260 characters fail unless `core.longpaths` is true; deep
  worktrees (`git worktree add`) hit it first. Propose
  `git config core.longpaths true` for the repository; never write it
  globally unasked.
- Names Windows forbids (`aux.py`, `con`, `nul`, names ending in a dot
  or space, `:` in a name) cannot be checked out there. Rename them in a
  commit made on Linux or with `git mv`.
- Case-insensitive NTFS: `git mv Readme.md README.md` records a
  case-only rename (lab, Linux: `R  Readme.md -> README.md`); renaming in
  Explorer does not. Two files differing only in case cannot both exist
  in a Windows working tree.
- Branch names differing only in case collide with the default
  ("files") ref storage on case-insensitive filesystems, as git's own
  `Documentation/BreakingChanges.adoc` says (2.55.0 source); the
  "reftable" storage avoids it. Never create such a pair.

## Credentials (`not run on Windows`)

Git for Windows usually uses Git Credential Manager
(`git config --get-all credential.helper` shows it), which may open a
window asking for a token. With `GIT_TERMINAL_PROMPT=0` a missing
credential fails at once on the terminal side; whether GCM's window is
suppressed too is to verify. If a push or fetch stops without output,
suspect a window waiting behind the editor. Report it; the deployment
skill owns tokens.

## Editors and pagers under Git for Windows (`not run on Windows`)

The installer sets `core.editor` (often Vim or Notepad) and a pager
(`less`). `GIT_EDITOR=:` and `GIT_PAGER=cat` need no program, because
git handles both values itself (checked in the 2.43.0 and 2.55.0
source), so they should work the same there. A sequence editor that runs
a script (`recipes/todo.py`) goes through Git's own `sh`: write paths
with forward slashes.
