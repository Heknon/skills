# Running hooks by hand

**What it decides:** which files and hooks a run covers, and what its
output and exit code mean. Verified on pre-commit 4.6.2.

## Choosing files and hooks

| Command | Runs |
| --- | --- |
| `uv run --frozen pre-commit run` | the `pre-commit` stage's hooks on the **staged** files, as a commit would |
| `... run --all-files` | on every tracked file; do this once after any config change |
| `... run --files src/a.py src/b.py` | on those files |
| `... run ruff-check --all-files` | one hook, by `id` |
| `... run --from-ref HEAD~1 --to-ref HEAD` | on the files changed between the two refs (*lab:* only the files of the last commit) |
| `... run --hook-stage manual --all-files` | hooks with `stages: [manual]` (or any other stage) |
| `... run --hook-stage commit-msg --commit-msg-filename msg.txt` | a `commit-msg` hook against a message file, without committing |

Useful flags: `--show-diff-on-failure` (prints `git diff` of what hooks
changed), `--fail-fast`, `--verbose` (output of passing hooks too).
`PRE_COMMIT_NO_CONCURRENCY=1` makes every hook run as one process (read
in `lang_base.py`).

`pre-commit run` without `--all-files` refuses while the config itself
has unstaged changes: `[ERROR] Your pre-commit configuration is
unstaged.` / `` `git add .pre-commit-config.yaml` to fix this.``

## Skipping by id

```powershell
$env:SKIP = "mypy"; git commit -m "..."; Remove-Item Env:SKIP
```

`SKIP` takes ids separated by commas (`SKIP=ruff-check,mypy`); a skipped
hook prints `Skipped`, and the others still run (*lab*, PowerShell 7.4
and sh). Skipping is for the person to ask for, by name
(`pre-commit/blocked.md`).

## Reading the output

| Line | Means |
| --- | --- |
| `ruff check....Passed` | ran, exit 0, changed nothing |
| `ruff check....Failed` with `- exit code: 1` | the tool reported findings; they follow |
| `ruff format....Failed` with `- files were modified by this hook` | the tool changed files; the commit is refused even if the tool exited 0 |
| `mypy....(no files to check)Skipped` | no staged file matched `files`/`types` |
| `mypy....Skipped` | skipped by `SKIP` |
| ``No hook with id `no-such-hook` in stage `pre-commit` `` | a wrong id, or the hook has another stage (exit 1) |
| `An unexpected error has occurred: ...` then `Check the log at .../pre-commit.log` | pre-commit itself failed (exit 3): a broken `entry`, an unreachable repository |

Exit code: 0 when all passed or were skipped, 1 when a hook failed or
changed files, 3 for an unexpected error (*lab*).

## Unstaged changes

On a run over staged files, pre-commit stashes the unstaged part first:

```
[WARNING] Unstaged files detected.
[INFO] Stashing unstaged files to /root/.cache/pre-commit/patch1790399498-26660.
```

and restores it at the end. When a hook changed a file that also had
unstaged changes, it could not restore both:

```
[WARNING] Stashed changes conflicted with hook auto-fixes... Rolling back fixes...
[INFO] Restored changes from ...
```

The formatter's fix is thrown away, the commit fails, and the next try
fails the same way. What to do is in `pre-commit/blocked.md`.

## Which files a pre-push hook gets

Read in `hook_impl.py`, seen in the lab: pushing a branch the remote
already has checks the files changed between the remote's commit and
the pushed one (the lab's second push gave the hook one file). Pushing a
branch whose history reaches a root commit the remote lacks runs with
`--all-files`.
