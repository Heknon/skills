# Keywords

The `.gitlab-ci.yml` keywords this skill uses, with what trips people up.
Checked against GitLab 19.4 documentation; lines marked *lab* were run
through the 19.4.1 lint API or a pipeline. For a keyword not here, read the
instance's `/help/ci/yaml/_index.md` before writing it.

## Top level

| Keyword | Use | Notes |
| --- | --- | --- |
| `workflow:rules` | whether a pipeline is created | `gitlab/rules.md` |
| `workflow:auto_cancel:on_new_commit` | what a newer pipeline on the same ref cancels | `conservative` (default): the whole older pipeline, only while no `interruptible: false` job has started; `interruptible`: only jobs with `interruptible: true`; `none` |
| `workflow:name` | pipeline title | variables allowed |
| `stages` | order of stages | default: `.pre`, `build`, `test`, `deploy`, `.post` |
| `variables` | defaults for every job | forwarded to child pipelines (`gitlab/downstream.md`) |
| `default` | `image`, `before_script`, `after_script`, `cache`, `interruptible`, `retry`, `tags`, `timeout` and others for every job | a job's own value replaces it, never merges |
| `include` | other files | `gitlab/includes-and-components.md` |
| `spec` | inputs of this file, then `---` | `gitlab/includes-and-components.md` |

**Reserved names.** A job cannot be named `image`, `services`, `stages`,
`before_script`, `after_script`, `variables`, `cache` or `include`.
*lab:* a job named `image:` made pipeline creation fail with `image name
should be a string`.

## Job

| Keyword | Notes |
| --- | --- |
| `stage` | default `test` |
| `image` | a string, or `name:` with `entrypoint: [""]` for images whose entrypoint is a program (such as `alpine/helm`, `bitnami/kubectl`): the runner needs a shell. Variables allowed: `image: $PYTHON_IMAGE` |
| `script`, `before_script`, `after_script` | lists of shell lines. `after_script` runs in a new shell (no variables or `cd` from `script` survive), also after failure, with its own timeout; its failure does not fail the job |
| `rules` | `gitlab/rules.md`. Never with `only` or `except` in the same job (*lab:* `config key may not be used with rules: only`) |
| `needs` | start when these jobs finish, ignoring stages; receives their artifacts and dotenv variables. `needs: []` starts at once. A needed job that rules removed rejects the pipeline unless written `{job: name, optional: true}` (*lab*) |
| `dependencies` | which earlier jobs' artifacts to download; `[]` for none. With `needs`, use `needs:artifacts` instead |
| `artifacts` | `paths`, `expire_in`, `when: always`, `reports: junit / coverage_report / dotenv` |
| `cache` | `key` (a string, or `key:files: [uv.lock]`), `paths`, `policy: pull-push / pull / push`. Best effort; never for passing results between jobs |
| `environment` | `name`, `url`, `deployment_tier` (`production`, `staging`, `testing`, `development`, `other`), `action` (`start`, `stop`, `prepare`, `verify`, `access`), `auto_stop_in`, `on_stop` (`gitlab/environments.md`) |
| `resource_group` | one job at a time across pipelines. Variables allowed, not persisted ones. *lab:* `deploy-$DEPLOY_ENV` from the job's variables worked |
| `interruptible` | may be cancelled by a newer pipeline; `false` for deploys |
| `when` | `on_success` (default), `on_failure`, `always`, `manual`, `delayed` (with `start_in`), `never` (only inside `rules`) |
| `allow_failure` | `true`, `false`, or `exit_codes: [..]` |
| `retry` | `max: 0..2`, `when: [runner_system_failure, stuck_or_timeout_failure, ...]`: retry infrastructure failures only |
| `timeout` | job timeout, such as `30m`; not above the runner's or project's |
| `tags` | runner tags the job needs (`gitlab/runners.md`) |
| `trigger` | a downstream pipeline (`gitlab/downstream.md`) |
| `release` | create a GitLab release; needs the `glab` or `release-cli` image (*lab:* `registry.gitlab.com/gitlab-org/cli` created it) |
| `coverage` | a regular expression over the log, such as `'/^TOTAL.*\s(\d+(?:\.\d+)?)%$/'` for pytest-cov |
| `id_tokens` | OIDC tokens for Vault and clouds |
| `secrets` | external secrets from Vault and others (Premium) |

## Reuse inside one file

- **`extends`**: merges the named hidden job into this job. Hashes merge
  deeply (`variables` combine, the job's value wins per key); **arrays are
  replaced** (*lab:* `.base` with `script: [base-1, base-2]` extended by a
  job with `script: [own]` ran `own` only, and kept `.base`'s
  `before_script`). Up to 11 levels; several parents allowed, later wins.
- **`!reference [.hidden, script]`**: inserts one key's value, such as a
  list of lines, inside another list (*lab:* `[login, deploy]`). Use it to
  combine script lines, which `extends` cannot.
- **YAML anchors** (`&name`, `*name`, `<<: *name`): only within one file;
  not across `include`.

## YAML traps

- Write scripts as block lists (`- line` under `script:`). *lab:* the flow
  form `script: [echo "X=${X:-absent}"]` failed to parse, and the pushed
  pipeline was created as failed.
- Quote a line that starts with a quote, `*`, `&`, `!`, `{`, `[`, or holds
  `: ` or ` #`.
- Values under `variables:` are parsed as YAML first: *lab:* `yes` and
  `on` became `true`, `1.10` became `1.1`. Quote them.
- Multi-line shell: `- |` keeps newlines (a real script);
  `- >` folds lines into one command (a long command with arguments).
