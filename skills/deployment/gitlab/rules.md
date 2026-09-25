# Rules and workflow

Checked against GitLab 19.4 documentation and the lab instance.

## Evaluation

- `workflow:rules` decides whether a pipeline is created. First matching
  rule wins; `when: never` or no match means no pipeline. Without
  `workflow:rules`, every event creates one.
- A job's `rules` decide whether the job is in the pipeline. First matching
  rule wins; no match means the job is absent. A rule with no `if`,
  `changes` or `exists` always matches: use it last, as the default.
- Inside one rule, `if`, `changes` and `exists` must all be true.
- A matching rule may set `when` (`on_success` default, `manual`,
  `delayed` with `start_in`, `always`, `never`), `allow_failure`,
  `variables`, `needs` and `interruptible`.
- A pipeline whose jobs all fail their rules is not created. The API
  answers `The resulting pipeline would have been empty. Review the rules
  configuration.` (seen on 19.4).

## Which variables exist per event

| Variable | Branch | Tag | Merge request | Scheduled |
| --- | --- | --- | --- | --- |
| `CI_COMMIT_BRANCH` | yes | | | yes |
| `CI_COMMIT_TAG` | | yes | | if scheduled on a tag |
| `CI_PIPELINE_SOURCE == "push"` | yes | yes | | |
| `CI_PIPELINE_SOURCE == "schedule"` | | | | yes |
| `CI_PIPELINE_SOURCE == "merge_request_event"` | | | yes | |
| `CI_MERGE_REQUEST_IID` and other `CI_MERGE_REQUEST_*` | | | yes | |
| `CI_COMMIT_REF_NAME` | branch | tag | source branch | ref |

`CI_PIPELINE_SOURCE` values: `push`, `merge_request_event`, `schedule`,
`web` (Run pipeline page), `api` (pipelines API), `trigger` (trigger
token), `parent_pipeline` (child pipeline), `pipeline` (multi-project),
`chat`, `webide`, `external`, `external_pull_request_event`,
`security_orchestration_policy`, `ondemand_dast_scan`,
`ondemand_dast_validation`.

## The workflow that avoids duplicate pipelines

Without it, a push to a branch with an open merge request creates two
pipelines. This is the recipes' block:

```yaml
workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS
      when: never
    - if: $CI_COMMIT_BRANCH
    - if: $CI_COMMIT_TAG
```

Merge request pipeline when a merge request is open, branch pipeline
otherwise, and tag pipelines. Schedules and the Run pipeline page on a
branch set `CI_COMMIT_BRANCH`, so they pass the third rule, except while
that branch has an open merge request, when the second rule stops them.
To run them always, add `- if: $CI_PIPELINE_SOURCE == "schedule"` (or
`"web"`) above the `never` rule. CI lint warns `may allow multiple
pipelines to run for a single action` when a job uses `rules:when` and the
file has no `workflow:rules`.

## `if` expressions

- Compare: `$VAR == "value"`, `$VAR != "value"`, `$VAR` (set and not
  empty), `$VAR == null`.
- Regular expressions: `$VAR =~ /^v\d+\.\d+\.\d+$/`, `!~`. The right side
  may be a variable holding the pattern.
- Combine with `&&`, `||` and parentheses.
- Only `$VAR` form, not `${VAR}`. Persisted variables (job-time values such
  as `CI_JOB_ID`) and `CI_ENVIRONMENT_SLUG` are not available.
- Job `variables:` are available to that job's `rules:if` (the components
  recipe uses `if: $RUFF == "true"` with `RUFF` set in the job; it ran on
  19.4).
- Quote the whole expression when it starts with a quote or holds `: `.

## `changes`

```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    changes:
      - services/api/**/*
  - if: $CI_COMMIT_BRANCH
    changes:
      paths: [services/api/**/*]
      compare_to: refs/heads/main
```

| Pipeline | `changes` compares with |
| --- | --- |
| merge request | the target branch |
| branch, existing | the previous push to the branch |
| branch, new | nothing: true |
| tag, schedule, web, API, trigger | nothing: true |
| any, with `compare_to: <ref>` | that ref |

- Globs: `**` crosses folders; `dir/**/*` matches every file under `dir`.
- `compare_to` takes a branch (`refs/heads/main`), tag or SHA. Variables
  known at pipeline creation are expanded in it and in `changes` paths
  (*lab:* `refs/heads/$CI_DEFAULT_BRANCH` and `$SVC_DIR/**/*` worked on
  19.4.1, although the documentation's table says otherwise).
- `exists:` checks files in the repository at the commit.

## `include` with rules

An `include:` entry may carry `rules:` with `if` (and `exists`,
`changes`). Only variables known when the configuration is read are
usable: predefined, project, group, instance, trigger and schedule
variables, not job variables. The monorepo recipe includes build and
deploy components only `if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH`.

## Manual jobs

| Written as | Pipeline waits for it | Seen on 19.4 |
| --- | --- | --- |
| `when: manual` in a rule | yes (blocking), pipeline status `manual` until run | `allow_failure: false` |
| `when: manual` at job level | no (optional) | `allow_failure: true` |
| `when: manual` in a rule with `allow_failure: true` | no | |
