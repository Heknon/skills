# The GitLab REST API

Every endpoint below was called on GitLab 19.4.1 in the lab. Base URL:
`https://<gitlab>/api/v4`, or `$CI_API_V4_URL` in a job.

## Authentication

| Header | Token |
| --- | --- |
| `PRIVATE-TOKEN: <token>` | personal, project or group access token |
| `JOB-TOKEN: $CI_JOB_TOKEN` | in a job (`gitlab/job-token.md`) |
| `Authorization: Bearer <token>` | OAuth tokens, and also access tokens |

A wrong token answers `401`. A resource you cannot see answers `404`,
also when it exists but is private: a 404 is not proof of absence.

## Project ids

Use the numeric id, or the full path URL-encoded: `shop/web` is
`shop%2Fweb`. `GET /projects/shop%2Fweb` returns the id.

## Pagination

`per_page` (up to 100) and `page`. Follow the `X-Next-Page` header, or the
`Link` header's `rel="next"`, until it is empty. `X-Total` is not always
sent.

## Endpoints this skill uses

| Purpose | Request |
| --- | --- |
| GitLab version and edition | `GET /version` (`"enterprise": false` is Community Edition) |
| project | `GET /projects/:id` |
| project settings that decide the configuration | `GET /projects/:id`: `ci_config_path`, `auto_devops_enabled`, `default_branch`, `permissions` |
| the token itself | `GET /personal_access_tokens/self`: name, scopes, expiry |
| lint a configuration (needs the `api` scope; *lab:* `read_api` got 403) | `POST /projects/:id/ci/lint` body `{"content": "<yaml>"}`; add `?dry_run=true&include_jobs=true&ref=<ref>` to simulate a pipeline on a branch or tag. The POST form takes `ref`: `dry_run_ref` is silently ignored there and the simulation runs on the default branch (seen in the lab) |
| lint the committed configuration (works with `read_api`) | `GET /projects/:id/ci/lint?content_ref=<ref>&dry_run=true&include_jobs=true&dry_run_ref=<ref>`; the response's `includes` lists every resolved include (`core/discover.md`) |
| a file | `GET /projects/:id/repository/files/<url-encoded path>/raw?ref=<ref>` |
| a job's artifact file | `GET /projects/:id/jobs/:job_id/artifacts/<path>` |
| code search in one project | `GET /projects/:id/search?scope=blobs&search=<text>` (group and global code search need advanced search) |
| latest pipeline on a ref | `GET /projects/:id/pipelines/latest?ref=main` |
| pipelines | `GET /projects/:id/pipelines?ref=<ref>&status=failed&source=<source>&per_page=20` |
| create a pipeline | `POST /projects/:id/pipeline` (singular) body `{"ref": "main"}`; add `"inputs": {...}` or `"variables": [{"key":..., "value":...}]` |
| jobs of a pipeline | `GET /projects/:id/pipelines/:pipeline_id/jobs?per_page=100` |
| trigger jobs of a pipeline | `GET /projects/:id/pipelines/:pipeline_id/bridges`; `downstream_pipeline.id` is the child |
| a job's log | `GET /projects/:id/jobs/:job_id/trace` |
| retry, run a manual job, cancel | `POST /projects/:id/jobs/:job_id/retry`, `/play`, `/cancel` |
| variables, without values | `GET /projects/:id/variables`, `GET /groups/:id/variables`, `GET /admin/ci/variables` |
| one variable of one scope | `GET /projects/:id/variables/:key?filter[environment_scope]=production` |
| create a variable | `POST /projects/:id/variables` with `key`, `value`, `variable_type` (`env_var`, `file`), `protected`, `masked`, `masked_and_hidden`, `raw` (default `true` through the API), `environment_scope`, `description` |
| environments | `GET /projects/:id/environments` |
| last deployment to an environment | `GET /projects/:id/deployments?environment=staging&order_by=id&sort=desc&per_page=1` |
| packages | `GET /projects/:id/packages` |
| Helm repository index | `GET /projects/:id/packages/helm/<channel>/index.yaml` |
| push a chart | `POST /projects/:id/packages/helm/api/<channel>/charts` multipart field `chart` |
| job token allowlist | `GET` / `POST /projects/:id/job_token_scope/allowlist` |
| protect tags | `POST /projects/:id/protected_tags` `{"name": "v*", "create_access_level": 40}` |

Reading a job log, a pipeline or a variable list changes nothing. Every
`POST`, `PUT` and `DELETE` above changes something: invariant 1 applies.

## From Windows PowerShell

In Windows PowerShell 5.1, `curl` is an alias for `Invoke-WebRequest`.
Write `curl.exe` for curl, or use `Invoke-RestMethod`, which parses JSON.
Keep the token in the session, never in a script file:

```powershell
$env:GITLAB_TOKEN = Read-Host -MaskInput "GitLab token"   # PowerShell 7; 5.1: see below
$GitLab  = "https://gitlab.example.com"
$Headers = @{ "PRIVATE-TOKEN" = $env:GITLAB_TOKEN }
$project = [uri]::EscapeDataString("shop/web")

# Parentheses: a JSON array is one object in the pipeline until they unroll it
(Invoke-RestMethod -Uri "$GitLab/api/v4/projects/$project/pipelines?per_page=5" -Headers $Headers) |
  Select-Object id, status, ref, source

# Variables: keys and flags only, never values
(Invoke-RestMethod -Uri "$GitLab/api/v4/projects/$project/variables" -Headers $Headers) |
  Select-Object key, environment_scope, protected, masked, variable_type

# Lint a local file, and simulate a tag pipeline
$body = @{ content = (Get-Content -Raw .gitlab-ci.yml) } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$GitLab/api/v4/projects/$project/ci/lint?dry_run=true&include_jobs=true&ref=v1.0.0" `
  -Headers $Headers -ContentType "application/json" -Body $body |
  Select-Object valid, errors, warnings, @{ n = "jobs"; e = { $_.jobs | ForEach-Object { "$($_.name):$($_.when)" } } }

# A failing call: the status code
try { Invoke-RestMethod -Uri "$GitLab/api/v4/projects/$project/variables/NOPE" -Headers $Headers }
catch { $_.Exception.Response.StatusCode.value__ }
```

These ran in PowerShell 7.4 against the lab. In Windows PowerShell 5.1,
`Read-Host -MaskInput` does not exist: use
`$s = Read-Host -AsSecureString "GitLab token"` and
`$env:GITLAB_TOKEN = [Net.NetworkCredential]::new("", $s).Password`.
A self-signed or internal CA must be trusted by Windows (the certificate
store), or `Invoke-RestMethod` fails with a trust error; never skip the
check.

With `curl.exe` (the history keeps `$env:GITLAB_TOKEN`, not the token):

```powershell
curl.exe -sS --header "PRIVATE-TOKEN: $env:GITLAB_TOKEN" "$GitLab/api/v4/version"
```

## In a job

```sh
curl --silent --show-error --fail-with-body --header "JOB-TOKEN: $CI_JOB_TOKEN" \
  "$CI_API_V4_URL/projects/$CI_PROJECT_ID/pipelines/$CI_PIPELINE_ID/jobs?per_page=100"
```

`--fail-with-body` makes curl exit non-zero on an HTTP error and still
print GitLab's message.
