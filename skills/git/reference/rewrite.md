# Rewrite recipes

Each recipe ran on git 2.43.0 with `GIT_EDITOR` and `GIT_SEQUENCE_EDITOR`
set to a script that records its call and fails, and stdin not a
terminal; none called it. The tidy, reword and autosquash recipes ran
again on 2.55.0. Make the backup branch first (`core/tidy.md`). Commands
are POSIX; in PowerShell set the variable first, then run the command:

```
$env:GIT_SEQUENCE_EDITOR = ':'
git rebase -i --autosquash origin/main
```

| Want | Recipe |
| --- | --- |
| fix the last commit | stage, `git commit --amend --no-edit` |
| reword the last commit | `git commit --amend -m "<subject>" -m "<body>"` |
| fix an older commit | stage, `git commit --fixup=<hash>` (or `--fixup=":/<subject start>"`), then `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash origin/main` |
| reword an older commit | `git commit --allow-empty -m "amend! <old subject>" -m "<new message>"`, then the same autosquash |
| drop, reorder, fold a plain commit | a plan and `recipes/todo.py` as the sequence editor (below) |
| squash the whole branch | `git merge-base HEAD origin/main`, then `git reset --soft <that hash>`, then one `git commit -m` |
| squash the last n | `git reset --soft HEAD~3`, then `git commit -m` |
| split the last commit | `git reset HEAD~1`, then stage and commit by file (`git add -- <path>`) or by hunk (`recipes/stage_hunks.py`) |
| committed on the wrong branch | `git branch <right-branch>`, then on the wrong one `git reset --keep '@{u}'` |
| wrong author on the last commit | `git commit --amend --reset-author --no-edit` |
| continue after a conflict | resolve, `git add`, `GIT_EDITOR=: git rebase --continue` |
| stop and put everything back | `git rebase --abort` |
| undo the whole tidy | `git reset --hard backup/<branch>` |

## What the lab showed

- `git commit --fixup=reword:<hash> -m "..."` is refused on 2.43.0 and
  2.55.0: `fatal: options '-m' and '--fixup:reword' cannot be used
  together`. Without `-m` it opens the editor. Use the `amend!` commit.
- An `amend!` commit's body becomes the whole new message. After
  autosquash the log read `263a800 Validate IBAN checksum before saving`
  where it had read `8febc19 stuff`; the other subjects were unchanged
  and the tree equal to the backup.
- `--fixup` needs a staged change; with nothing staged it said `nothing
  to commit, working tree clean`. `":/Reject IBANs"` names the newest
  commit whose message matches.
- `git rebase --autosquash` without `-i` folds `fixup!` and `amend!`
  commits from 2.44 (release notes) and did on 2.55.0; on 2.43.0 it
  succeeded and left `3c5f605 amend! stuff` in the log untouched. Always
  use `-i` with `GIT_SEQUENCE_EDITOR=:`.
- `git rebase --continue` opens the editor for the commit that stopped,
  even with no terminal: `Please supply the message using either -m or
  -F option.` / `error: could not commit staged changes.` With
  `GIT_EDITOR=:` it finished: `Successfully rebased and updated
  refs/heads/feature/late-fee.`
- `git reset --keep '@{u}'` moved main back to its upstream and kept
  untracked files; with an uncommitted edit to a file the reset would
  change it refused: `error: Entry 'report.py' not uptodate. Cannot
  merge.` Prefer it to `--hard`.
- A failing sequence editor (a refused plan) aborts the rebase with
  nothing changed: `git status -sb` showed the branch as before.

## A plan with todo.py

For moves autosquash cannot express: a plain commit named `fixup` to
fold into an earlier one, a drop, a new order.

1. `git log --reverse --format='pick %h %s' origin/main..` prints the
   current plan. Write it to `plan.txt` (outside the repository, or
   untracked) and edit it:
   ```
   pick 0997302 Add CSV export
   fixup 0ef5242 fixup
   pick 8d8899b Add an optional header row to CSV export
   pick d9faef8 Add export tests
   exec python3 -m unittest -q
   ```
   `fixup` folds into the line above and keeps its message; `fixup -C`
   takes the folded commit's message; `drop` removes; `exec` runs a
   command and stops the rebase if it fails.
2. Run the rebase with the script as sequence editor, paths absolute and
   with forward slashes:
   ```
   GIT_SEQUENCE_EDITOR="uv run --no-project python /abs/skill/recipes/todo.py /abs/plan.txt" git rebase -i origin/main
   ```
   PowerShell (`not run on Windows`):
   ```
   $env:GIT_SEQUENCE_EDITOR = 'uv run --no-project python C:/skills/git/recipes/todo.py C:/work/plan.txt'
   git rebase -i origin/main
   $env:GIT_SEQUENCE_EDITOR = ':'
   ```
3. The script refuses a plan that leaves out or repeats a commit, or
   uses `reword`, `squash`, `edit`, `break` or `fixup -c`; the rebase then
   stops before changing anything. In the lab: `todo.py: 'reword' opens
   an editor or stops; refused`, and `todo.py: plan does not match git's
   todo; missing [...]`.

Git 2.55.0 writes todo lines as `pick 258c426 # Validate IBAN ...`;
2.43.0 as `pick 258c426 Validate IBAN ...`. The script reads only the
verb and the hash, so both work.

## Moving a fixed commit past a later change

A reorder replays each commit on a new parent. It works when the moved
change and the ones it jumps over touch lines apart from each other; in
the lab `SEP = ','` on line 1 moved past a change at lines 8 to 9. When
they touch the same lines the rebase stops with a conflict
(`core/conflicts.md`); then `git rebase --abort` and fold the fix into
the later commit instead.
