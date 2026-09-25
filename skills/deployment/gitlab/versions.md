# Which GitLab version has what

Read the instance's version first (`GET /api/v4/version`), then check
every feature you plan to use against this table. Taken from the history
notes of the GitLab 19.4 documentation. A feature marked beta may have
been available earlier behind a flag; check that instance's `/help`.

| Feature | Available from |
| --- | --- |
| CI/CD components and the CI/CD Catalog | 17.0 (beta from 16.6) |
| `spec:inputs` | 17.0 |
| job token allowlist with groups | 17.0 |
| "Minimum role to use pipeline variables" | 17.1 |
| masked and hidden variables | 17.6 (17.4 behind a flag) |
| pipeline inputs recommended over pipeline variables | 17.7 |
| `trigger:strategy: mirror` | 18.2; before it, `strategy: depend` |
| maximum of 100 components per project (was 30) | 18.5 |
| `posix_escape` interpolation function | 18.6 |
| component context (`spec:component`, `$[[ component.version ]]`) | 18.7 (18.6 beta) |
| `split` interpolation function | 19.2 |
| kaniko documentation | removed; kaniko is unmaintained |

Keywords this skill uses that are older than every supported GitLab
version: `rules`, `workflow:rules`, `needs`, `extends`, `!reference`,
`rules:changes:compare_to`, `resource_group`, `environment`, `trigger`
with `include` and `forward`, `artifacts:reports:dotenv`, `include:rules`,
`interruptible`, `workflow:auto_cancel`.

## Runner

The runner's version is on the first line of any job log. When a job
behaves differently from these files, compare it with GitLab's version
before anything else; the lab ran both at 19.4.1.

## Helm, Kubernetes, OpenShift

`helm/versions.md` for Helm 3 and 4. Read the cluster with `kubectl
version` or `oc version`, which print the server's version under the
client's; this skill's commands were run with kubectl 1.37.1 and oc
4.22.14.
