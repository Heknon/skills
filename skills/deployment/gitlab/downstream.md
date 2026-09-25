# Downstream pipelines

Checked against GitLab 19.4 documentation; *lab* marks what ran on 19.4.1.

## Parent-child

```yaml
api:
  stage: units
  trigger:
    include: services/api/.gitlab-ci.yml
    strategy: mirror
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes: [services/api/**/*]
```

- The child runs in the same project, for the same commit. Its
  `CI_PIPELINE_SOURCE` is `parent_pipeline`.
- `trigger:include` takes a local path, or a list of `local`, `project`,
  `component` or `artifact` entries.
- **Status**: by default the trigger job succeeds as soon as the child is
  created. `strategy: mirror` (18.2 and later) makes it take the child's
  status exactly; `strategy: depend` (older, not recommended now) waits too
  but shows `running` while the child waits for a manual job. *lab:* with
  `mirror`, a child whose only pending job was an optional manual deploy
  counted as success.
- **Variables**: the trigger job's `variables` and the parent's top-level
  `variables` are passed down (`trigger:forward:yaml_variables: true` by
  default). They arrive as **pipeline variables**, so in the child they
  outrank project, group and instance variables (*lab*). Set
  `trigger:forward:pipeline_variables: true` to also pass the parent's own
  pipeline variables. Forwarding is not repeated into grandchildren
  unless that trigger job forwards too.
- **Workflow in the child**: a child file with `workflow:rules` must let
  `parent_pipeline` through, or the child is empty.
- **Artifacts from the parent**: a child job uses `needs:pipeline:job`
  with `pipeline: $PARENT_PIPELINE_ID`, where the trigger job sets
  `PARENT_PIPELINE_ID: $CI_PIPELINE_ID` in its `variables`.
- A merge request shows only the parent pipeline's status; the child's
  jobs are under the trigger job.

## Dynamic child pipelines

A job writes the child configuration, and the trigger job runs it:

```yaml
generate:
  stage: plan
  script:
    - python3 ci/generate.py > child.yml
  artifacts:
    paths: [child.yml]

run-child:
  stage: units
  needs: [generate]
  trigger:
    include:
      - artifact: child.yml
        job: generate
    strategy: mirror
```

Use it when the list of units cannot be written by hand. The generated
file is linted only when the child is created: print it in the generating
job's log so a failure can be read.

## Multi-project

```yaml
deploy-config:
  trigger:
    project: platform/deployments
    branch: main
    strategy: mirror
  variables:
    SERVICE: api
    IMAGE_DIGEST: $IMAGE_DIGEST
```

The downstream pipeline runs in the other project, as the user who
started the upstream one; that user needs at least the Developer role
there. `CI_PIPELINE_SOURCE` is `pipeline`. Variables sent are pipeline
variables there, and the downstream project's "Minimum role to use
pipeline variables" can refuse them.
