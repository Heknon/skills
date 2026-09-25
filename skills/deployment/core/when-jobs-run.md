# When jobs run

**Verdict you produce:** for each job in question, whether it is in the
pipeline for a given event, and how it runs, with the rule that decided.

```
<job> on <event>: <in pipeline: on_success | manual (blocking) | manual (optional) | delayed | not in pipeline>
  decided by: <workflow rule n or job rule n, file:line>
  shown by:   <dry-run output, or the pipeline's job list>
```

Events: merge request, push to the default branch, push to another branch,
tag, schedule, run from the web page, API, parent pipeline.

## Steps

1. **Workflow first.** Evaluate `workflow:rules` top to bottom; the first
   rule whose `if`, `changes` and `exists` are all true decides. `when:
   never` there means no pipeline at all; no matching rule also means no
   pipeline. Without `workflow:rules`, every event creates a pipeline.
2. **Then the job's rules**, the same way. First match wins; its `when`
   (default `on_success`), `allow_failure`, `variables` and `needs` apply.
   No match: the job is not in the pipeline. A job without `rules`, `only`
   or `except` is always in the pipeline.
3. **Know which variables exist for the event** (`gitlab/rules.md`, the
   event table). The usual mistake: `$CI_COMMIT_BRANCH` is empty in merge
   request pipelines and tag pipelines, and `$CI_MERGE_REQUEST_*` exist
   only in merge request pipelines.
4. **`changes` depends on the event** (`gitlab/rules.md`): against the
   target branch in a merge request, against the previous push on a
   branch, always true for a new branch, a tag, a schedule, a web or API
   pipeline unless `compare_to` is set.
5. **Check it**, do not reason it out alone: CI lint with
   `dry_run=true&include_jobs=true` and the ref (`ref=` on the POST form,
   `dry_run_ref=` on the GET form) lists the jobs and their `when` for that
   branch or tag (`gitlab/api.md`). For a merge
   request, read the latest merge request pipeline's jobs instead.

## Common asks, and the rule that does it

| Ask | Rule |
| --- | --- |
| only in merge requests | `if: $CI_PIPELINE_SOURCE == "merge_request_event"` |
| only on the default branch | `if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH` |
| only on release tags | `if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/` |
| only when files changed | `changes:` with `paths:`, and `compare_to:` outside merge requests (`core/monorepo.md`) |
| a person starts it and the pipeline waits | `when: manual` inside a rule: blocking, `allow_failure: false` |
| a person may start it, the pipeline does not wait | `when: manual` at job level, or `allow_failure: true` in the rule |
| never in scheduled pipelines | first rule `if: $CI_PIPELINE_SOURCE == "schedule"` with `when: never` |
| only if a file exists | `exists: [Dockerfile]` |

## Never

- Never compare `$CI_COMMIT_BRANCH` in a rule meant for merge request
  pipelines.
- Never rely on `changes` in a tag or scheduled pipeline without
  `compare_to`: it is always true there.
- Never give a job `needs` on a job that rules can remove, unless the need
  is `optional: true`; the pipeline is rejected with `'b' job needs 'a'
  job, but 'a' does not exist in the pipeline`.

## Stop and ask

- The person wants a job to run "when someone approves". Approval rules
  for deployments are a Premium feature (`gitlab/environments.md`). Ask
  which tier the instance has before designing it.
