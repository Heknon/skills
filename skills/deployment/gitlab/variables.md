# CI/CD variables

Checked against GitLab 19.4 documentation; lines marked *lab* were run on
19.4.1.

## Precedence, highest first

1. Variables of a pipeline execution policy or scan execution policy (only
   for the jobs the policy adds).
2. Manual job variables, typed when running a manual job.
3. **Pipeline variables**: the Run pipeline page, a schedule, the pipelines
   API, the triggers API, the `ci.variable` push option, and **an
   upstream pipeline** (what a parent passes to a child, including its
   forwarded `variables:`).
4. Project variables.
5. Group variables; the closest subgroup wins.
6. Instance variables.
7. Variables from dotenv reports of jobs in `needs` or `dependencies`.
8. Variables in `.gitlab-ci.yml`, highest first: `rules:variables` of the
   job, the job's `variables`, `workflow:rules:variables`, the top-level
   `variables`.
9. Deployment variables.
10. Predefined variables. `CI_ENVIRONMENT_ID`, `CI_ENVIRONMENT_SLUG`,
    `CI_ENVIRONMENT_URL` and `CI_PAGES_URL` cannot be overridden.

*lab:* an instance variable `HELM_IMAGE` overrode the file's top-level
`HELM_IMAGE` in a pipeline; in the same project's child pipelines the
parent's forwarded `HELM_IMAGE` won over the instance variable, as item 3
predicts.

## Kinds and flags

| Setting | Effect |
| --- | --- |
| type `env_var` | the value is in the environment variable |
| type `file` | the value is written to a temporary file; the variable holds its path. For kubeconfigs, certificates, `.netrc`. Tools that take a path (`KUBECONFIG`, `SSL_CERT_FILE`) work directly |
| protected | only pipelines for protected branches and protected tags receive it; otherwise the variable is absent, not empty |
| masked | `[MASKED]` replaces the value in job logs. The value must be one line, no spaces, 8 characters or more, and not the name of another variable. With expansion on, only letters, digits and `_ : @ - + . ~ = /` are allowed; turn expansion off (raw) to use any character |
| masked and hidden | also never shown again in the settings or the API; only settable when the variable is created (GitLab 17.6 and later) |
| raw (expansion off) | `$` in the value is kept literally. The UI's "Expand variable reference" is on by default; the API's `raw` defaults to `true`, so a variable created through the API is not expanded unless `raw: false` |
| environment scope | `*` for all jobs; `production` for jobs whose `environment:name` is `production`; `review/*` for any environment starting with `review/`. A job with no `environment:` receives only `*` variables (*lab:* a `staging` variable reached the `staging` job, not the job without environment nor the `production` one) |
| description | shown in the settings; use it to say who owns the value and how it rotates |

A masked value that a process prints changed (escaped, split, base64
encoded) is not masked. Masking is not a guarantee; file variables and
never printing are.

## Where a variable is expanded

| Place | Expanded? | By |
| --- | --- | --- |
| `script`, `before_script`, `after_script` | yes | the job's shell, at run time |
| `image`, `services:name`, `cache:key`, `artifacts:paths` | yes | the runner |
| `variables` | yes | GitLab, then the runner |
| `environment:name`, `environment:url`, `resource_group` | yes, without job-time (persisted) variables | GitLab |
| `include` | yes, only predefined (pre-pipeline), project, group, instance, trigger and schedule variables | GitLab |
| `rules:if` | compared, `$VAR` form only; not persisted variables, not `CI_ENVIRONMENT_SLUG` | GitLab |
| `rules:changes` paths and `rules:changes:compare_to` | yes, with variables known at pipeline creation. *lab:* `changes: [$SVC_DIR/**/*]` and `compare_to: refs/heads/$CI_DEFAULT_BRANCH` both matched as expanded; the 19.4 table in the documentation says "no", the behaviour says yes | GitLab |
| `rules:exists` | not tested here; check the instance's `/help` | GitLab |
| `tags`, `trigger:project` | yes | GitLab |

Predefined variables have an availability: **Pre-pipeline** (usable in
`include` and `rules`, such as `CI_COMMIT_BRANCH`, `CI_DEFAULT_BRANCH`,
`CI_PROJECT_PATH`), **Pipeline** (usable in `rules`, such as
`CI_ENVIRONMENT_NAME`), and **Job-only** (only in scripts, such as
`CI_JOB_TOKEN`, `CI_PIPELINE_ID`, `CI_REGISTRY_PASSWORD`).

To write a literal `$` in a value that is expanded, write `$$`.

## Predefined variables this skill uses

| Variable | Value |
| --- | --- |
| `CI_COMMIT_SHA`, `CI_COMMIT_SHORT_SHA` | the commit; the first eight characters |
| `CI_COMMIT_BRANCH` | branch name, in branch pipelines only |
| `CI_COMMIT_TAG` | tag name, in tag pipelines only |
| `CI_COMMIT_REF_NAME`, `CI_COMMIT_REF_SLUG` | branch or tag; lowercased, 63 bytes, `[a-z0-9-]`, for names and hosts |
| `CI_COMMIT_BEFORE_SHA` | the previous commit of the branch; all zeros for merge requests, schedules and new branches |
| `CI_DEFAULT_BRANCH` | the project's default branch |
| `CI_OPEN_MERGE_REQUESTS` | up to four merge requests whose source is this branch; set in branch and merge request pipelines when one is open |
| `CI_PIPELINE_SOURCE` | the event (`gitlab/rules.md`) |
| `CI_MERGE_REQUEST_IID`, `CI_MERGE_REQUEST_TARGET_BRANCH_NAME`, `CI_MERGE_REQUEST_DIFF_BASE_SHA` | merge request pipelines only |
| `CI_PROJECT_ID`, `CI_PROJECT_PATH`, `CI_PROJECT_NAME`, `CI_PROJECT_URL` | the project |
| `CI_SERVER_URL`, `CI_SERVER_FQDN`, `CI_API_V4_URL` | `https://gitlab.example.com`; `gitlab.example.com`; `https://gitlab.example.com/api/v4` |
| `CI_REGISTRY`, `CI_REGISTRY_IMAGE`, `CI_REGISTRY_USER`, `CI_REGISTRY_PASSWORD` | the project's container registry; **only set when the registry is enabled** (absent in the lab, whose registry was off) |
| `CI_JOB_TOKEN` | the job token (`gitlab/job-token.md`) |
| `CI_ENVIRONMENT_NAME`, `CI_ENVIRONMENT_SLUG`, `CI_ENVIRONMENT_URL` | set when the job has `environment:` |
| `CI_DEPLOY_USER`, `CI_DEPLOY_PASSWORD` | the project's deploy token named `gitlab-deploy-token`, if it exists |

## Pipeline variables can be switched off

Settings > CI/CD > Variables > **Minimum role to use pipeline variables**:
`no_one_allowed`, `owner`, `maintainer` (default on self-managed),
`developer`. A lower role gets `Insufficient permissions to set pipeline
variables`. GitLab recommends pipeline **inputs** instead (17.7 and
later).

## Checking a secret without showing it

In a job:

```sh
if [ -n "$KUBECONFIG" ]; then echo "KUBECONFIG set"; else echo "KUBECONFIG unset"; fi
test -s "$KUBECONFIG" && echo "kubeconfig file has $(wc -l < "$KUBECONFIG") lines"
test -n "$DEPLOY_TOKEN" && echo "DEPLOY_TOKEN length ${#DEPLOY_TOKEN}"
```

Never `echo "${VAR:-unset}"` or `${VAR:+...}${VAR:-...}` to report
presence: `${VAR:-x}` expands to the value when it is set, unmasked if the
variable is not masked (a File variable holding a kubeconfig cannot be).

Through the API or `glab`, list keys and flags only (`gitlab/api.md`,
`gitlab/glab.md`). `glab variable get` and `glab variable export` print
values: never for secrets.
