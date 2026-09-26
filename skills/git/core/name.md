# Name: messages, branches, tags

**Verdict you produce:** the convention, where it was found, and the name
or message that follows it.

```
convention: <Conventional Commits | plain imperative + "Refs PROJ-n" | ... | none found>
found in:   <file and line | tool config | "18 of the last 30 subjects" | defaults>
result:     <the message, branch or tag name>
verdict name: <follows the convention | defaults used: no convention found>
```

## Find the convention, in this order

Stop at the first that decides, and cite it.

1. **Written rules.** `CONTRIBUTING.md`, `docs/`, a merge request
   template (`.gitlab/merge_request_templates/`).
2. **A tool that enforces one.** Any of: `commitlint.config.*`,
   `.commitlintrc*`, `[tool.commitizen]` in `pyproject.toml`, `commitizen`
   or `gitlint` in `.pre-commit-config.yaml`, `.gitlint`, a
   semantic-release config, a CI job that checks messages, a
   `commit-msg` hook (`core/commit.md`, Hooks), a `commit.template`
   (`git config --get commit.template`). GitLab push rules live on the
   server; the deployment skill reads them through the API.
3. **Recent practice.**
   ```
   git log --no-merges -n 30 --format=%s origin/main
   git log --no-merges -n 30 --format=%B origin/main       # bodies and trailers
   git branch -r --sort=-committerdate --format='%(refname:short)'
   git tag -l --sort=-v:refname
   ```
   A pattern in most of them is the convention. To count Conventional
   types and scopes (POSIX shell; in PowerShell read the list):
   `git log --no-merges -n 30 --format=%s origin/main | sed -E 's/^([a-z]+)(\(([^)]*)\))?!?:.*/\1 \3/' | sort | uniq -c`.
4. **Nothing found**: the defaults in `reference/conventions.md`, and the
   answer says `defaults used: no convention found`.

## Commit messages

- Subject: what the commit does, in the form the convention uses. By
  default imperative ("Add", "Fix", not "Added", "Fixes"), capitalised,
  no full stop, aim at 50 characters and never over 72.
- Body: why, and what changes for a user; the diff already shows how.
  Never `fix`, `update`, `changes`, `WIP`, `address review`.
- Trailers and references last, copied in the repository's exact form.
  In the lab a repository ended messages with `Refs PROJ-302`, which is
  not a git trailer (`%(trailers)` printed nothing), and
  `git commit --trailer "Refs: PROJ-311"` added `Refs: PROJ-311` as a
  separate paragraph. Match the form: a last `-m "Refs PROJ-311"`.
- The issue key usually sits in the branch name
  (`git branch --show-current` printed `fix/PROJ-311-vat-rounding`).
- Conventional Commits only where the repository uses them or a tool
  enforces them; the types and scopes it already uses; a breaking change
  as `type(scope)!:` and a `BREAKING CHANGE:` trailer.

## Branch names

1. Pattern from `git branch -r`; default `<type>/<issue>-<slug>`, lower
   case, hyphens, under about 50 characters
   (`fix/PROJ-42-discount-on-renewals`).
2. Check it: `git check-ref-format --branch <name>` prints the name and
   exits 0, or exits 128 with `fatal: '<name>' is not a valid branch
   name` (lab: spaces, `..`, a `.lock` ending, a leading `-`).
3. A branch `fix` makes every `fix/...` impossible:
   ```
   fatal: cannot lock ref 'refs/heads/fix/PROJ-42-...': 'refs/heads/fix' exists; cannot create 'refs/heads/fix/PROJ-42-...'
   ```
   `git log --oneline main..fix` shows whether `fix` holds unmerged work.
   Ask before renaming or deleting it; renaming it into the pattern
   (`git branch -m fix fix/login-timeout`) worked in the lab.
4. Names that differ only in case collide on Windows and macOS with the
   default ref storage; git's own `BreakingChanges.adoc` (2.55.0) says
   so. Never create one (`reference/windows.md`).

## Tags

Annotated, with a message: `git tag -a v1.4.0 -m "Release 1.4.0"`
(`git cat-file -t v1.4.0` prints `tag`; a tag without `-a` prints
`commit`). `git tag -a v9` with no `-m` opens the editor. Which number
is the packaging skill's decision. A monorepo that releases members one
by one tags each as `<member>-v<version>`, such as `api-v0.5.0`
(`reference/conventions.md`). Pushing a tag leaves this machine
(`core/push.md`).
