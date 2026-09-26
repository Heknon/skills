# Commit

**Verdict you produce:** the commit, and proof that it holds exactly what
was meant.

```
staged:  <each path by name>
diff:    <git diff --cached --stat summary line>
commit:  <hash> <subject>
verdict commit: <committed | split into <n> commits | stopped: <why>>
```

## Steps

1. `git status`. Name every file in it. Decide which belong to this
   change. Junk (`__pycache__/`, `.venv/`, `.env`, dumps, build output,
   editor files) never does: propose a `.gitignore` for it
   (`core/clean-up.md`), in its own commit.
2. Read the change: `git diff -- <path>`. If `--stat` shows far more
   lines than you changed, it is line endings (`core/clean-up.md`); fix
   that before staging.
3. One logical change per commit. A fix and a formatting sweep, or a fix
   and a rename, are two commits, the fix first, so each can be reverted
   and bisected alone. Split by file with `git add -- <path>`; split
   inside a file with `recipes/stage_hunks.py` (never `add -p`, which
   waits for keys):
   ```
   uv run --no-project python <skill>/recipes/stage_hunks.py list billing.py
   uv run --no-project python <skill>/recipes/stage_hunks.py stage billing.py 1
   ```
4. Stage by name: `git add -- billing.py`. Deletions: `git rm -- <path>`;
   renames: `git mv <old> <new>`.
5. Check the index: `git diff --cached --stat`, then `git diff --cached`
   if in doubt. In the lab the fix alone showed
   `billing.py | 2 +-` / `1 file changed, 1 insertion(+), 1 deletion(-)`.
6. To test what is staged and nothing else:
   `git stash push --keep-index -m "check staged"`, run the tests,
   `git stash pop`. On 2.43.0 the pop merged back cleanly
   (`Auto-merging billing.py`).
7. Write the message (`core/name.md`) and commit with `-m`, one `-m` per
   paragraph:
   ```
   git commit -m "Charge no late fee on day 30" -m "The contract says fees start after 30 days; day 30 was charged."
   ```
   For a longer message, write it to a file with your editing tool and
   `git commit -F msg.txt` (`reference/windows.md` on encodings).
8. `git show --stat --format=%s HEAD` and `git status`.

## Amending

Only for the last commit, and only if it is not pushed
(`git branch -r --contains HEAD` prints nothing):

| Want | Command |
| --- | --- |
| add a forgotten file | `git add -- <path>`, then `git commit --amend --no-edit` |
| new message | `git commit --amend -m "<subject>" -m "<body>"` |
| your name and email on it | `git commit --amend --reset-author --no-edit` |

`git commit --amend` with neither `--no-edit` nor `-m` opens the editor
(lab: `Please supply the message using either -m or -F option.`).

## Hooks

A `commit-msg` or `pre-commit` hook that rejects the commit is the
repository's rule: read its message and fix the commit. The hooks folder
is `git config --get core.hooksPath`, or `.git/hooks`
(`git rev-parse --git-path hooks` prints the one in use). Never pass
`--no-verify` unless the person asks for it.

With `core.hooksPath` set, `pre-commit install` refuses (``Cowardly
refusing to install hooks with `core.hooksPath` set.``) and hints `git
config --unset-all core.hooksPath`, which would switch off what the
hooks path runs. Do not unset it unasked. Call pre-commit from the
existing hook instead: the last line of that folder's `pre-commit`
script becomes `exec uv run --frozen pre-commit run`. *lab* (git
2.43.0, pre-commit 4.6.2): the existing hook printed its line, then the
ruff hook failed the commit on an unused import. The details are the
linting skill's: `skills/linting/pre-commit/install.md`.

## Never

- Never `git add .`, `git add -A` or `git commit -a` without reading
  `git status` first; in the lab, `git add --dry-run .` would have added
  `.env`, `.venv/pyvenv.cfg`, `__pycache__/...pyc` and a 60 MB
  `dump.sql`.
- Never commit with markers in a file: `git diff --check` finds them
  (`leftover conflict marker`); git itself commits them without a word.
