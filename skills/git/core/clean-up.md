# Clean up: ignore, untrack, line endings, huge files

**Verdict you produce:** the change, and what history and the remote
still hold.

```
change:   <.gitignore lines | untracked paths | line endings of <paths> | ...>
history:  <still holds <path> in <n> commits | nothing to remove>
verdict clean-up: <done | proposed, waits for the person | stopped: <why>>
```

Secrets have their own procedure: `core/secrets.md`.

## Ignore files

1. `git status --short --untracked-files=all` lists every untracked file.
2. Add patterns to `.gitignore` (`recipes/example.gitignore` is a
   starting set; keep only what applies). Commit it on its own.
3. Check: `git check-ignore -v <path>` prints the rule that matched
   (`.gitignore:3:.env	.env`), or exits 1 when nothing ignores it.
   `git status --short --ignored` shows `!!` for ignored files.
4. A pattern like `.env.*` with `!.env.example` keeps the example
   tracked (lab: `.env.local` hidden, `.env.example` shown as `??`).

## Stop tracking a file that is committed

`.gitignore` does not affect a tracked file: `git check-ignore -v .env`
exited 1 for the tracked `.env` in the lab, and only `--no-index`
showed the rule. Untrack it, keeping it on disk:

```
git rm --cached -- .env
git rm -r --cached -- __pycache__ .venv
git commit -m "Stop tracking local files" -m "They are generated or hold local settings; .gitignore now covers them."
```

`git status` then shows `D  .env` staged and the files still on disk.
The old commits still hold them: a secret is `core/secrets.md`, a huge
file is below.

## Line endings

A one-line change that shows as a whole-file change is line endings:

1. `git diff --stat` shows every line changed; `git diff
   --ignore-cr-at-eol --stat` shows the real change (lab: 8 lines against
   1).
2. `git ls-files --eol <path>` shows the index and the working tree:
   `i/crlf  w/lf  attr/  billing.py` means the repository holds CRLF and
   your editor saved LF.
3. Put the file back the way the repository holds it, then stage:
   `uv run --no-project python <skill>/recipes/eol.py crlf billing.py`
   (lab: `billing.py: 8 CRLF, 0 LF`, then `git diff --stat` showed
   `1 insertion(+), 1 deletion(-)`).
4. `core.autocrlf` does not fix this. With `-c core.autocrlf=true` the
   lab repository still staged all 8 lines: a file whose index copy has
   CRLF is not converted. Never change `core.autocrlf`.
5. The lasting fix is `.gitattributes` (`recipes/example.gitattributes`)
   and a renormalising commit, only when asked, on a clean tree:
   ```
   git add .gitattributes
   git add --renormalize .
   git commit -m "Normalise line endings" -m "Adds .gitattributes; every text file is now stored with LF."
   ```
   `--renormalize` also stages any other modified tracked file (lab), so
   run it with nothing else changed. The commit touches every CRLF file;
   add it to `.git-blame-ignore-revs` (`reference/conventions.md`).

## A huge file

1. Find the biggest objects in all history:
   ```
   git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectsize) %(objectname) %(rest)'
   ```
   and sort by the second column (POSIX: `| awk '$1=="blob"' | sort -k2
   -n -r | head`). The lab found `blob 62914509 83ccc52... dump.sql`.
2. Not pushed: remove it from the commit that added it (`reference/
   rewrite.md`: amend if last, otherwise a plan that drops or fixes that
   commit), keep the file on disk, ignore it.
3. Pushed: stop tracking it in a new commit and say that history and
   every clone still hold it. Removing it from history is a rewrite of
   shared history, the same decision as `core/secrets.md` step 5.

## Never

- Never `git clean -fdx` to tidy up: `-x` removes ignored files too
  (`git clean -n -dx` listed `.env` and `notes.md` in the lab). Use
  `git clean -n` first, and `-f` without `-x` only when asked.
