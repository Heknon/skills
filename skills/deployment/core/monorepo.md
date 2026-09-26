# Monorepo

**Verdict you produce:** the units, what each depends on, and the
pipeline shape that runs each unit only when one of its paths changed.

```
units:
  <unit>: <folder>  kind: <library | service>  depends on: <libraries, lock file>
shape:  <parent-child | one pipeline with rules:changes>
changes compared with: <per event, from the table below>
```

## Find the units

1. List the folders with their own build file (`pyproject.toml`,
   `Dockerfile`, `Chart.yaml`). Each is a candidate unit. Units can also
   exist without a build file (a folder reached by `sys.path` or
   `PYTHONPATH`, a program with only a `requirements.txt`): the
   packaging skill's `recipes/tools/map_units.py` lists every unit and
   tie with `file:line`, and `core/monorepo.md` there says what to do
   about them.
2. For Python, read the root `pyproject.toml`: `[tool.uv.workspace]
   members` lists the workspace members, and each member's
   `[tool.uv.sources]` with `workspace = true` names the members it
   depends on. One `uv.lock` at the root serves the whole workspace.
3. A unit's paths are its folder, every workspace library it depends on
   (transitively), the root `pyproject.toml` and `uv.lock`. A library
   change must run every unit that uses it.

## Choose the shape

1. **More than about three units, or units with their own build and
   deploy jobs:** **parent-child pipelines**. The parent has one trigger
   job per unit with `rules:changes`; each unit has its own child file in
   its folder. Recipe: `recipes/monorepo/`. Job names in a child only need
   to be unique in that child, and a unit's pipeline can be read alone.
2. **Two or three units with a few jobs each:** one pipeline, each job
   with `rules:changes` on its unit's paths. Simpler, but the file grows
   with every unit.
3. **Units discovered at run time** (hundreds, or generated): a job writes
   a child configuration file and a trigger job runs it as an artifact
   (`gitlab/downstream.md`, dynamic child pipelines). Harder to read;
   use only when the list cannot be written by hand.

## What `changes` compares with

| Pipeline | Compared with | Consequence |
| --- | --- | --- |
| merge request | the merge request's target branch | the right set, every push |
| default branch | the previous push to the branch | only what this push changed |
| other branch | the previous push; for a new branch, nothing: always true | add `compare_to: refs/heads/$CI_DEFAULT_BRANCH` |
| tag, schedule, web, API | nothing: always true | every unit runs; add `compare_to` or accept it |

`compare_to` takes a ref; `refs/heads/$CI_DEFAULT_BRANCH` works (lab).
The recipe's rules use `changes` in merge requests and on the default
branch, and `compare_to: refs/heads/$CI_DEFAULT_BRANCH` on other branches. In the lab, a
change to `packages/common` ran the library and the service that depends
on it; a change to the service alone ran only the service; a change to the
root CI file ran no unit.

## Rules that keep it working

1. **Keep one job that always runs** in the parent. A pipeline whose rules
   match no job is not created, and a merge request that needs a passing
   pipeline cannot merge.
2. **`trigger:strategy: mirror`** on each trigger job, so the parent shows
   the child's result (GitLab 18.2 and later; `depend` before that).
3. **Build a workspace member from the workspace root**: the build context
   is the root, the Dockerfile is in the unit
   (`recipes/monorepo/services/api/Dockerfile`), and `uv sync --package
   <name>` installs only that member and its dependencies.
4. **Environments per unit**: `staging/api`, `production/api`. A variable
   scoped `staging/*` reaches every unit's staging deploy.
5. **Variables forwarded to children outrank settings**: the parent's
   `variables:` arrive in each child as pipeline variables
   (`core/variables.md`).

## Never

- Never list only the unit's own folder in its paths when it imports a
  workspace library.
- Never deploy from a tag pipeline in a monorepo without deciding which
  units the tag releases: every `changes` rule is true there. Use per-unit
  tags (`api-v1.2.0`) with `if: $CI_COMMIT_TAG =~ /^api-v/`, or deploy
  from the default branch.

## Stop and ask

- The units share one release cadence and one version. Ask whether they
  should deploy together; then they are one unit.
