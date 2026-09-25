# Includes and components

Checked against GitLab 19.4 documentation; *lab* marks what ran on 19.4.1.

## Include types

| Type | Written | Reads from | Pin with |
| --- | --- | --- | --- |
| local | `include: local: ci/build.yml` (or a string starting with `/`) | this repository, same commit | nothing: moves with the commit |
| project | `include: {project: group/templates, ref: v1.2.0, file: [/python.yml]}` | another project on this instance | `ref:` a tag or SHA; without `ref` it follows that project's default branch |
| component | `include: component: $CI_SERVER_FQDN/group/components/name@1.2.0` | a component project's `templates/` | the version after `@` |
| template | `include: template: Jobs/SAST.gitlab-ci.yml` | templates shipped with the instance | the instance version |
| remote | `include: remote: https://...` | any URL, fetched at pipeline creation | nothing; unusable air gapped, avoid |

- Included content **merges** with the file: same-named jobs merge into
  one, top-level `variables` combine, the including file wins on
  conflicts. `stages` is a list, so it is replaced, not combined: set it
  once, in the main file, with every stage any included job uses.
- `include` entries may have `rules:` (`gitlab/rules.md`) and `inputs:`.
- Up to 150 nested includes per pipeline.
- `include:project` needs the pipeline's user to be able to read that
  project.

## Components

A component project has `README.md` and `templates/`, where each component
is `templates/<name>.yml` or `templates/<name>/template.yml`. Other files
in a component's folder are not part of it.

A component file is a header, `---`, then the configuration:

```yaml
spec:
  description: What it does, shown in the catalog.
  inputs:
    job-prefix:
      default: python
    stage:
      default: test
    ruff:
      type: boolean
      default: true
    when:
      options: [on_success, manual]
      default: on_success
    needs:
      type: array
      default: []
    namespace:
      description: No default: the input is required.
---
"$[[ inputs.job-prefix ]]-test":
  stage: $[[ inputs.stage ]]
  needs: $[[ inputs.needs ]]
  when: $[[ inputs.when ]]
  script:
    - echo "deploying to $[[ inputs.namespace ]]"
```

- **Types**: `string` (default), `number`, `boolean`, `array`. An input
  without `default` is required. `options` lists allowed values; `regex`
  validates a string; `description` documents it.
- **Interpolation**: `$[[ inputs.name ]]` anywhere after `---`, including
  job names (quote the key). The whole value `$[[ inputs.needs ]]` of an
  array input becomes a YAML list (*lab:* `needs: $[[ inputs.needs ]]`).
  Inside a string, it is text.
- **Functions**: `$[[ inputs.x | expand_vars ]]`, `truncate(offset,length)`,
  `posix_escape` (18.6), `split('sep')` (19.2). Up to three per block.
- **Inputs are fixed at pipeline creation**; variables are not visible to
  them except through `expand_vars`, which cannot see masked or
  environment-scoped variables.
- **Using a component**:
  ```yaml
  include:
    - component: $CI_SERVER_FQDN/platform/ci-components/python-checks@1.1.0
      inputs:
        job-prefix: api
        working-directory: services/api
  ```
  Only components on the same instance. Version, highest priority first:
  a commit SHA, a tag, a branch; then, for releases published to the
  CI/CD Catalog only, a partial version (`1`, `1.2`) or `~latest`.
  *lab:* `@1.1.0` resolved from a plain tag without a catalog release.
- **Testing a component in its own project**: include it from
  `$CI_SERVER_FQDN/$CI_PROJECT_PATH/<name>@$CI_COMMIT_SHA`
  (`recipes/ci-components/.gitlab-ci.yml`).
- **Publishing to the CI/CD Catalog**: the project is marked as a catalog
  project (Settings > General > Visibility, project features,
  permissions > CI/CD Catalog project, Owner role), has a description and
  a `README.md`, and a tag pipeline job creates the release with the
  `release:` keyword, not the Releases API. Tags are semantic versions.
- **Component context** (18.7 and later): with `spec: component: [name,
  version, sha, reference]`, `$[[ component.version ]]` gives the
  version the consumer included, such as to pull a matching tool image.

## Inputs for a whole pipeline

A project's own `.gitlab-ci.yml` may start with `spec:inputs` too; values
are given on the Run pipeline page, by `glab ci run --input key:value`, by
the pipelines API, or a schedule. Prefer them to pipeline variables for
choices a person makes when starting a pipeline.
