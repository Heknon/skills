# Recipes

Complete files that ran. Copy them whole; change only what their top
comment says. Python ones run with `uv run --no-project python <file>`
and need nothing installed.

| File | Does | Checked |
| --- | --- | --- |
| `session.sh`, `session.ps1` | the session settings in `SKILL.md` | `.sh` on Linux under a terminal: `merge --continue` finished, `log` and `branch` did not page; `.ps1` not run on Windows |
| `todo.py` | a sequence editor that replaces a rebase's todo list with a plan you wrote, refusing verbs that open an editor and plans that lose a commit | tidy sandbox on 2.43.0 and 2.55.0: three clean commits, tree equal to the backup; a `reword` plan and a stale plan were refused and the rebase left nothing changed |
| `stage_hunks.py` | lists the hunks of one file and stages the ones you name, through `git apply --cached` | mixed-change sandbox: hunk 1 alone gave `1 insertion(+), 1 deletion(-)`; hunk 2 alone `4 insertions(+), 4 deletions(-)`; a wrong number was refused |
| `bisect_test.py` | the `git bisect run` script: 0 good, 1 bad, 125 skip when the module does not import | bisect sandbox: `Use the context rounding in to_cents` found, two commits skipped |
| `bisect-test.sh` | the same around one pytest file | bisect sandbox with pytest 9.1.1: the same commit found |
| `bisect-test.ps1` | the PowerShell form of `bisect-test.sh` | not run on Windows |
| `eol.py` | shows or sets a file's line endings byte for byte | crlf sandbox: `8 CRLF, 0 LF` after, diff back to one line |
| `example.gitattributes` | line endings decided by the repository; copy to the root as `.gitattributes` | `git check-attr -a` gave `eol: lf` for `.py`, `eol: crlf` for `.ps1`, `binary: set` for `.png` |
| `example.gitignore` | local files that never belong in a commit; copy to the root as `.gitignore` | add-all sandbox: everything but the fix ignored; `.env.example` still shown |
