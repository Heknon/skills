# Push

**Verdict you produce:** what was pushed and what the remote answered.

```
asked:   <the person's words that asked for the push>
pushed:  <local ref> -> <remote ref>, <commits: git log --oneline @{u}.. before>
remote:  <the "To <url>" block, and any "remote:" lines>
verdict push: <pushed | rejected: <reason> | not pushed: not asked>
```

A push leaves this machine: only when the person asked for it
(invariant 10). The deployment skill owns GitLab itself (protected
branches, merge requests, CI, tokens); this procedure stops at git's
answer.

## Before

1. `git status -sb`: which branch, which upstream, ahead and behind.
2. What will go: `git log --oneline '@{u}..'`, or for a branch with no
   upstream `git log --oneline origin/main..HEAD` (with no upstream,
   `@{u}` fails: `fatal: no upstream configured for branch
   'feature/report'`).
3. Never to the default or a protected branch unless that is exactly
   what was asked.
4. `git push --dry-run -u origin HEAD` shows what would happen:
   `* [new branch] HEAD -> feature/report` / `Would set upstream of
   'feature/report' to 'feature/report' of 'origin'`.

## Commands (lab: 2.43.0)

| Want | Command |
| --- | --- |
| first push of a branch | `git push -u origin HEAD` (`branch 'feature/report' set up to track 'origin/feature/report'.`) |
| later pushes | `git push` |
| a tag | `git push origin v1.4.0` (`* [new tag] v1.11.0 -> v1.11.0` in the lab); never `--tags` unasked |
| a branch you rewrote, yours alone | `git push --force-with-lease --force-if-includes` |
| delete a remote branch | `git push origin --delete <name>`, only when asked |

## Rewritten branches

Never `--force`. `--force-with-lease` alone is not enough: it compares
the remote with your `origin/<branch>`, and a fetch updates that. In the
lab a colleague's commit was fetched, the branch rebased, and
`--force-with-lease` replaced the remote branch, erasing the commit
(`core/integrate.md`). `--force-if-includes` refused it: `! [rejected]
feature/export -> feature/export (remote ref updated since checkout)`.
If it refuses, fetch, merge or rebase the remote's commits in, and ask.

## Reading the answer

| Git says | Means | Do |
| --- | --- | --- |
| `! [rejected] main -> main (non-fast-forward)` / `Updates were rejected because the tip of your current branch is behind` | the remote has commits you lack | `git fetch`, merge them in (`core/integrate.md`), push again; never force |
| `(remote ref updated since checkout)` | lease check failed | as above |
| `! [remote rejected] <ref> (pre-receive hook declined)` with `remote:` lines above | the server refused: protected branch, push rule, size | read the `remote:` lines; the deployment skill owns GitLab's rules (their exact wording on 19.4 is to verify) |
| `fatal: The current branch <b> has no upstream branch.` | first push | `git push -u origin HEAD` |
| `fatal: The upstream branch of your current branch does not match the name of your current branch.` | the branch tracks `origin/main` | `git push -u origin HEAD`; next time create it with `--no-track` |
| `fatal: could not read Username for '<url>': terminal prompts disabled` | no stored credentials, and prompts are off | stop and report; the deployment skill sets up tokens |

## After

`git status -sb` shows `## <branch>...origin/<branch>` with no ahead
count. Quote the `To <url>` block in the answer.
