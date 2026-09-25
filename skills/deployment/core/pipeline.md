# Pipeline

**Verdict you produce:** a `.gitlab-ci.yml`, or a change to one, that CI
lint accepts, with the list of jobs each kind of pipeline gets.

```
merge request:  <jobs>
default branch: <jobs>
tag vX.Y.Z:     <jobs>
lint:           <valid: true, and the dry-run job lists for branch and tag>
```

## Start from a recipe

| Project | Recipe |
| --- | --- |
| one Python service, deployed | `recipes/python-service/` |
| a uv workspace with many units | `recipes/monorepo/` |
| a Helm chart project | `recipes/generic-chart/.gitlab-ci.yml` |
| a shared components project | `recipes/ci-components/` |
| a Python library, published | `recipes/ci-components/templates/python-checks.yml` and `python-publish.yml`, included as components |

If shared components exist in the organisation, include them instead of
copying jobs (`core/shared-ci.md`).

## Design rules

1. **One `workflow:rules` block decides which events get a pipeline.**
   Use the one in the recipes: merge request pipelines, branch pipelines
   only when no merge request is open, and tags. It prevents a branch
   pipeline and a merge request pipeline for the same push
   (`gitlab/rules.md`).
2. **Checks first, fast, on every pipeline.** Lint and test run in
   merge requests; nothing else needs to.
3. **Build once, on the default branch or a release tag.** The image job
   tags with `$CI_COMMIT_SHA`, never rebuilds an existing tag, and
   passes the digest to deploy jobs in a dotenv report (`core/images.md`).
4. **One deploy job per environment**, each with `environment:`,
   `resource_group`, `interruptible: false`, and its own namespace. Staging
   deploys automatically from the default branch; production is `when:
   manual` on a protected tag or the default branch (`core/deploy.md`).
5. **`needs` for order, stages for display.** A job with `needs` starts as
   soon as those jobs finish, regardless of stage. Deploy jobs `need` the
   image job, which carries its dotenv variables to them.
6. **Everything not secret is in the file.** Namespaces, release names,
   chart versions and image paths are job `variables`, reviewed with the
   code. Secrets and cluster credentials are CI/CD variables
   (`core/variables.md`).
7. **Images come from the mirror, by variable.** Every `image:` is a
   variable such as `$PYTHON_IMAGE`, set once at the top, so a mirror move
   is one line. An image whose entrypoint is a program, such as
   `alpine/helm`, needs `entrypoint: [""]`.
8. **Interruptible checks, uninterruptible deploys.** `default:
   interruptible: true` with `workflow:auto_cancel:on_new_commit:
   interruptible` cancels stale checks; a deploy that started must finish.

## Steps

1. Read the versions (`SKILL.md`): GitLab decides which keywords exist
   (`gitlab/versions.md`); the runner's executor decides whether image
   builds work (`gitlab/runners.md`).
2. Start from the recipe, or from the current file if you are changing
   one. Change only what the ask needs.
3. For every keyword you write, find it in `gitlab/keywords.md`,
   `gitlab/rules.md` or `gitlab/includes-and-components.md`. A keyword not
   there is checked in the instance's `/help` before use.
4. Lint it (`core/verify.md`), and dry-run it for the default branch and
   a tag. Compare the job lists with the verdict block.
5. List what a person must set: variables, protected tags, allowlists,
   runner tags (`## Needs a person`).

## Never

- Never mix `only`/`except` with `rules` in one job; GitLab rejects it.
  Write new jobs with `rules` only.
- Never name a job `image`, `services`, `stages`, `before_script`,
  `after_script`, `variables`, `cache` or `include`. These are
  keywords, and a top-level `image:` with a job body is rejected with
  `image name should be a string` (seen on 19.4).
- Never use `latest` or a branch name as a deploy tag.
- Never put a secret in `variables:` of the file, even base64 encoded.
- Never use `allow_failure: true` to make a failing check green.
- Never use `when: always` on a deploy job.

## Stop and ask

- The project needs a runner with privileges (Docker-in-Docker) and none
  is tagged for it. Ask which runner tag to use; do not add `privileged`
  anywhere yourself.
- The request would deploy from merge requests to a shared environment.
  Ask whether review apps (one environment per merge request) are wanted
  (`gitlab/environments.md`).
