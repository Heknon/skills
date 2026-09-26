# A committed secret

**Verdict you produce:** rotate first, then where the secret still is.

```
secret:   <kind, never the value> in <path>, added in <hash> <subject>
pushed:   <yes: git branch -r --contains <hash> lists <branches> | no>
rotate:   <who revokes and replaces it; first, whatever else happens>
now:      <untracked and ignored in <hash> | removed from unpushed history>
still in: <commits, remote branches, clones, merge request refs, CI logs>
verdict secret: <rotate now; history left as is | rewritten locally, not pushed | waiting for the person>
```

## Steps

1. **Rotate first, always.** A pushed secret is in every clone, fork and
   merge request made since, and maybe in CI logs. Removing it from git
   does not un-leak it. Say so before anything else. Never print the
   value, in a command or the answer.
2. **Find where it is.**
   ```
   git log --all --format='%h %s' -- .env
   git branch -r --contains <hash>
   ```
   In the lab: `d300ac7 Add local configuration`, contained in
   `origin/main`.
3. **Stop tracking it**, keeping the local file:
   ```
   git rm --cached -- .env
   ```
   add `.env` to `.gitignore`, commit both. Check `.env` is still on disk.
4. **Say what the new commit does not do.** The key is still in history:
   in the lab, after that commit, `git show HEAD~1:.env` still printed
   it, and `git log --all -S <value>` listed both `d300ac7` (added) and
   the new commit (removed). Search with `-S` locally; never paste the
   value into the answer.
5. **Rewriting history** only when not pushed, or when the person
   decides after hearing the cost: every clone must re-clone or reset,
   open merge requests keep the old commits, the server keeps
   unreachable objects until its own cleanup, and a force push to a
   protected branch is refused (GitLab's behaviour and its cleanup are
   the deployment skill's; to verify on GitLab 19.4).
   - Unpushed and in the last commit: `git rm --cached -- .env`,
     `git commit --amend --no-edit`.
   - Unpushed and older: `reference/rewrite.md` (a plan with a fixup of
     the commit that added it).
   - Whole history, only when asked: `git filter-repo` if the mirror has
     it (`uvx --from git-filter-repo git-filter-repo`, 2.47.0 in the lab;
     git 2.43.0 has no `filter-repo` of its own: `git: 'filter-repo' is
     not a git command.`). In a fresh clone:
     `git filter-repo --invert-paths --path .env`. In the lab it refused
     a clone with history of its own (`Refusing to destructively
     overwrite repo history since this does not look like a fresh
     clone.`, use `--force`), **removed the `origin` remote**, and
     **deleted the working-tree `.env`**: copy the file somewhere safe
     first.
   - `git filter-branch` exists but warns against itself (`WARNING:
     git-filter-branch has a glut of gotchas generating mangled
     history`); do not use it.

## Never

- Never answer "removed" after step 3 alone.
- Never force push a rewritten history unasked (`core/push.md`).
