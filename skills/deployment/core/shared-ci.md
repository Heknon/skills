# Shared CI

**Verdict you produce:** the mechanism for sharing, the files, and how
consumers pin a version.

```
mechanism: <component | include:project with extends | include:local>
project:   <group/project holding the shared files>
units:     <each component or file: its inputs and the jobs it adds>
version:   <how consumers pin: @X.Y.Z, ref: vX.Y.Z>
tested by: <the project's own pipeline, which includes each unit from $CI_COMMIT_SHA>
```

## Choose the mechanism

Answer in order; the first yes decides.

1. **Is the configuration used only inside one repository** (several
   child pipelines in a monorepo, several jobs alike)? **`include:local`**
   files and hidden jobs with `extends` or `!reference`. No versioning
   needed: it moves with the commit.
2. **Is GitLab 17.0 or later?** (`gitlab/versions.md`) **CI/CD
   components**: one project, a `templates/` folder, `spec:inputs` per
   component, releases by semantic version tag. Recipe:
   `recipes/ci-components/`.
3. **Older GitLab:** **`include:project` with `ref:` a tag**, files of
   hidden jobs, consumers `extends` them and set variables. `spec:inputs`
   is generally available from 17.0; an older instance may have it as a
   beta, so check its `/help/ci/inputs/_index.md` before using inputs.

## Rules for components

1. **Inputs, not variables, for anything the consumer chooses.** Inputs
   are typed, checked at pipeline creation, have defaults, and cannot be
   overridden by a stray project variable. Variables stay for secrets and
   values only known at run time.
2. **Every job name carries an input** (`"$[[ inputs.job-prefix ]]-test"`)
   so the component can be included twice, such as once per monorepo unit.
   Two jobs with the same name merge silently into one.
3. **No global keywords** in a component: no top-level `variables`,
   `default`, `workflow` or `stages`. They would change the consumer's
   pipeline. Put `stage` as an input and set it on each job.
4. **Images as inputs** with the mirror as default.
5. **Test every component in its own project's pipeline**, included from
   `$CI_SERVER_FQDN/$CI_PROJECT_PATH/<name>@$CI_COMMIT_SHA`, against sample
   files in `tests/`. A tag pipeline that passes creates the release with
   the `release:` keyword.
6. **Consumers pin a full version** (`@1.1.0`). Partial versions (`@1`)
   and `~latest` work only for releases published to the CI/CD Catalog.
   A branch name is for testing only.
7. **A breaking change is a major version**: a renamed or removed input, a
   renamed job, a changed default that changes behaviour.

## Steps

1. Read the GitLab version. List the jobs to share, from two or more
   existing pipelines: what is the same, what differs. What differs
   becomes an input.
2. Write each component from the recipe's shape: `spec:` with
   `description` and `inputs`, `---`, then the jobs.
3. Add each component to the project's `.gitlab-ci.yml` test, and a sample
   under `tests/` that exercises it.
4. Lint; push; the pipeline must pass; tag `X.Y.Z`.
5. In one consumer, replace the copied jobs with the `include:component`
   and the inputs; dry-run it and compare the job list with before.

## Never

- Never include a shared file without a pinned `ref` or version in a
  pipeline that deploys: the next commit to the shared project would
  change production pipelines unreviewed.
- Never read a secret into an input's default or description.
- Never let a component `include` another by branch.

## Stop and ask

- The shared project is private and consumers are in other groups: each
  consumer's users need at least read access to it. Ask who administers
  that.
- The organisation already has a templates project in another shape.
  Extend it; do not start a second one without asking.
