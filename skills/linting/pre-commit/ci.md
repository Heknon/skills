# pre-commit in CI

**What it decides:** the command a pipeline job runs, and what the job
needs so that it matches a developer's commit. The job itself (image,
rules, cache keys) is the deployment skill's; this file gives it the
commands. Verified on pre-commit 4.6.2 outside GitLab.

## The commands

After the job's `uv sync --locked` (deployment's Python job does it):

```
uv run --no-sync pre-commit run --all-files --show-diff-on-failure
```

On a merge request, only the files it changes:

```
uv run --no-sync pre-commit run --from-ref "$CI_MERGE_REQUEST_DIFF_BASE_SHA" --to-ref "$CI_COMMIT_SHA" --show-diff-on-failure
```

(`CI_MERGE_REQUEST_DIFF_BASE_SHA` is listed by the deployment skill as
set in merge request pipelines only.)

- `--no-sync` is right here: the job has just synced the environment
  from the lock, so the hooks' `uv run --frozen` find it ready.
- pre-commit runs `git diff --name-only <from>..<to>`. Both commits must
  be in the clone. *Lab:* a shallow clone (`--depth 1`) failed with
  `fatal: ambiguous argument 'HEAD~1..HEAD': unknown revision`, and an
  unknown commit with `Invalid revision range`, both exit 3. The job
  needs enough history (a git depth the deployment skill sets).
- `--show-diff-on-failure` prints what fixer hooks would change, then
  `If you are seeing this message in CI, reproduce locally with:
  pre-commit run --all-files`.
- Exit code 1 fails the job for findings or for changed files; 3 for
  pre-commit's own errors.

## What the job needs

| Need | Why |
| --- | --- |
| the same tool versions as developers | hooks run `uv run --frozen <tool>` from the lock; nothing is pinned twice |
| `PRE_COMMIT_HOME` inside the project folder, cached | only for `language: python` or remote hooks, whose environments live there; deployment's cache must be inside the project folder. Local `system` hooks need no cache |
| `PIP_INDEX_URL` for the mirror | only for `language: python` hooks (`pre-commit/offline.md`) |
| no `SKIP` | a job that skips hooks checks less than a commit does |

Duplicating ruff and mypy as their own jobs as well as inside
pre-commit runs the same tool twice; pick one per check. Tests belong
in their own job, not in pre-commit (`pre-commit/catalogue.md`).
