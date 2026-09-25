# glab

GitLab's command-line client. Checked with glab 1.119.0 (the
`registry.gitlab.com/gitlab-org/cli` image) against GitLab 19.4.1.

## Configure it for a self-managed, air-gapped instance

| Setting | Environment variable | Config key |
| --- | --- | --- |
| the instance | `GITLAB_HOST=gitlab.example.com` | `host` |
| the token | `GITLAB_TOKEN` | stored by `glab auth login` |
| the internal CA (PEM) | `GLAB_CA_CERT` | `ca_cert`, per host |
| HTTP instead of HTTPS | `GLAB_API_PROTOCOL=http` | `api_protocol`, per host |
| no update check | `GLAB_CHECK_UPDATE=false` | `check_update` |

Without `GLAB_CHECK_UPDATE=false`, every command tries gitlab.com and
prints `failed checking for glab updates` in an air-gapped network. In a
Git folder whose remote is on the instance, glab finds the project; else
pass `-R group/project`.

Login once, token read from the terminal, not the command line:

```
glab auth login --hostname gitlab.example.com --stdin
```

(paste the token, then end input). `glab auth status` shows the result.

## Commands this skill uses

| Task | Command | Changes something |
| --- | --- | --- |
| lint the local `.gitlab-ci.yml` | `glab ci lint`, or `glab ci lint path/to/file.yml` | no |
| the whole configuration, in final form | `glab ci config compile` (includes merged, `extends` applied, `!reference` inserted) | no |
| simulate a pipeline on a ref | `glab ci lint --dry-run --ref v1.0.0` (says valid or not; the job list needs the API, `gitlab/api.md`) | no |
| list pipelines | `glab ci list -R group/project -P 5` | no |
| status of the branch's pipeline | `glab ci status --branch main` | no |
| a pipeline with its jobs | `glab ci get -R group/project -p <pipeline id> --with-job-details` | no |
| a job's log | `glab ci trace <job id or name> -p <pipeline id>` | no |
| variables: keys and flags | `glab variable list -R group/project`, `--group <group>`, `--instance` | no |
| start a pipeline | `glab ci run -b main`; inputs `--input key:value`; variables `--variables-env KEY:value` | yes |
| retry a job | `glab ci retry <job id>` | yes |
| set a variable | `glab variable set KEY --scope production --protected --type file < kubeconfig` (the value from a file on stdin, never `-v <secret>` on the command line) | yes |
| any API call | `glab api projects/:id/pipelines` (`:id` is filled from the repository) | depends on the method |

## Never

- Never `glab variable get` or `glab variable export` for a secret: both
  print values (`export` prints every variable's value).
- Never pass a token with `--token` on a command line that is saved in
  shell history; use `--stdin` or the environment variable.
