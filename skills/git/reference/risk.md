# Risk classes

Look up a command before running it. The class decides what you do
first. Seniority's challenge (`core/challenge.md` in that skill) runs
before every command in the last three classes.

| Class | First |
| --- | --- |
| **reads** | nothing |
| **reversible here** | `git status` |
| **destroys uncommitted work** | save it (stash `--include-untracked` or a backup branch), say where, then the challenge |
| **rewrites history** | not pushed, or the person's own branch said by them; backup branch; the challenge; ask when pushed |
| **leaves this machine** | only when asked; never force to a shared branch |

## Commands

| Command | Class |
| --- | --- |
| `status`, `diff`, `log`, `show`, `reflog`, `stash list`, `stash show`, `branch` (list), `tag -l`, `ls-files`, `check-ref-format`, `check-ignore`, `rev-parse`, `merge-base`, `range-diff`, `bundle verify`, `bundle list-heads`, `fsck`, `worktree list`, `submodule status` | reads |
| `fetch` | reads (changes only `origin/*`) |
| `add`, `restore --staged`, `commit`, `switch`, `switch -c`, `branch <new>`, `branch -m`, `stash push`, `stash apply`, `merge`, `revert`, `cherry-pick`, `tag -a`, `worktree add`, `bisect`, `bundle create`, `format-patch`, `am`, `submodule update` | reversible here |
| `reset --soft`, `reset` (mixed) on an unpushed commit | reversible here (the reflog keeps the old tip) |
| `reset --keep` | reversible here; refuses to overwrite local edits |
| `reset --hard`, `restore <path>`, `restore .`, `checkout -- <path>`, `clean -f`, `stash drop`, `stash clear`, `stash pop` after a failed check, `worktree remove --force`, `reset --merge` with staged changes | destroys uncommitted work |
| `branch -D`, `branch -d` | destroys a name; the commits stay in the reflog; say the hash |
| `commit --amend`, `rebase`, `rebase -i`, `reset` to an older commit of a pushed branch, `filter-repo`, `filter-branch` | rewrites history |
| `push`, `push -u`, `push origin <tag>`, `push --delete`, a bundle or patch handed over | leaves this machine |
| `push --force-with-lease --force-if-includes` | rewrites history and leaves this machine |
| `push --force` | never |
| `clean -x`, `clean -X` | destroys ignored files (`.env`, `.venv`): never unasked |
| `gc`, `prune`, `reflog expire` | destroys what recovery needs: never while something is missing |
| `config --global`, `config --system` | changes every repository: propose, never write unasked |
