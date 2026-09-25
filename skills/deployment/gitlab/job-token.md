# The job token

`CI_JOB_TOKEN` is created for each job and valid while it runs. It acts
with the permissions of the user who started the pipeline, limited to
certain endpoints and by allowlists. Checked on GitLab 19.4.1.

## What it can do

| Use | How | Checked |
| --- | --- | --- |
| clone other projects the user can read | `https://gitlab-ci-token:${CI_JOB_TOKEN}@gitlab.example.com/group/project.git` | |
| the project's container registry | `$CI_REGISTRY_USER` / `$CI_REGISTRY_PASSWORD` (the job token) | |
| push a chart to the project's Helm registry | `curl --user "gitlab-ci-token:$CI_JOB_TOKEN" --form "chart=@app-1.0.0.tgz" "$CI_API_V4_URL/projects/$CI_PROJECT_ID/packages/helm/api/stable/charts"` | lab: `201 Created` |
| pull a chart from another project | `helm repo add ... --username gitlab-ci-token --password-stdin` | lab |
| publish to the project's PyPI registry | `uv publish` with user `gitlab-ci-token` | lab |
| install from another project's PyPI registry | index URL with `gitlab-ci-token:${CI_JOB_TOKEN}@` | lab |
| API endpoints | header `JOB-TOKEN: $CI_JOB_TOKEN`; only the endpoints GitLab lists for job tokens, such as the jobs and pipelines of its project, packages, releases | lab: listing the pipeline's jobs |

## The allowlist

A project's **CI/CD job token allowlist** (Settings > CI/CD > Job token
permissions) lists the groups and projects whose job tokens may access
it. By default it holds only the project itself.

- **Private target project**: a job from another project gets `404 Not
  Found`, not 403. *lab:* `helm repo add` failed with `failed to fetch
  http://gitlab.lab/api/v4/projects/2/packages/helm/stable/index.yaml :
  404 Not Found` until the chart project added the service project to its
  allowlist.
- **Internal or public target project**: its public resources, such as
  packages, are readable by any project's job token unless the target
  also limits those to its allowlist. *lab:* the internal chart project
  served its chart without an allowlist entry.
- The user who started the pipeline must also be a member of the target
  project with enough rights.
- Administrators can enforce the allowlist on every project.

Add an entry through the API (Maintainer of the target project):

```
POST /api/v4/projects/<target id>/job_token_scope/allowlist   {"target_project_id": <consumer id>}
POST /api/v4/projects/<target id>/job_token_scope/groups_allowlist   {"target_group_id": <group id>}
```

## Never

- Never replace the job token with a personal token to get past a 404.
  Ask for the allowlist entry.
- Never pass the job token to anything that outlives the job.
