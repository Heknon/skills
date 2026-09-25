# Discover

Find everything that makes up a project's pipelines: where the
configuration comes from, every file it includes (and what those
include), the final form of every job, and every pipeline it starts in
this project or others. Also the reverse: which projects use a given
templates project or component. Everything here is read only.

**Verdict you produce:** the map, each line with the evidence behind it.

```
project <path> @ <ref>
config:    <.gitlab-ci.yml | other path | EXTERNAL file@project:ref | none, Auto DevOps | none>
includes:  <type  location  @ ref  (included from)   flags: not pinned | rules>
jobs:      <jobs a pipeline on the ref would have, with when>
triggers:  <job -> child file | dynamic artifact | project/branch>, each followed the same way
runtime:   <latest pipeline and its downstream pipelines, if asked>
not seen:  <what could not be resolved, and why>
```

## The fast way: the script

`recipes/tools/ci_map.py` does every step below and prints the map. It
reads only (`GET` requests, plus `POST /ci/lint`, which changes nothing).

```powershell
$env:GITLAB_URL = "https://gitlab.example.com"
$env:GITLAB_TOKEN = <token: read_api is enough for most; api also resolves child pipeline files>
uv run <skill>\recipes\tools\ci_map.py group/project --runtime
uv run <skill>\recipes\tools\ci_map.py --consumers platform/templates --group shop
```

*lab, GitLab 19.4.1:* on a project with local, pinned and unpinned project
includes nested two deep, a component, an include with rules, a child
pipeline with its own includes, a dynamic child and a multi-project
trigger, it listed every include with where it came from, flagged the
unpinned one, followed the child and the other project, and printed the
last pipeline's tree of downstream pipelines. It also recognised a project
whose configuration lives in another project, and one with no file where
Auto DevOps runs instead.

Without Python or the script, do the steps by hand.

## Steps

1. **Where the configuration comes from.** `GET /projects/:id` and read
   `ci_config_path` and `auto_devops_enabled`:
   - empty: `.gitlab-ci.yml` in the repository;
   - a path: that file in the repository;
   - `file.yml@group/project` or `file.yml@group/project:ref`: the
     **whole configuration is in another project**. The repository may
     have no `.gitlab-ci.yml` at all (*lab:* 404), its pipelines still
     run, and `GET /ci/lint` fails with `Please provide content of
     .gitlab-ci.yml`. Never conclude "no CI" from the repository alone.
   - no file, and `auto_devops_enabled: true` (the instance default):
     GitLab runs the Auto DevOps template. *lab:* `GET /ci/lint` then
     lints that template without saying so.
2. **Every include, resolved by GitLab.**
   `GET /projects/:id/ci/lint?include_jobs=true&content_ref=<ref>&dry_run=true&dry_run_ref=<ref>`
   (works with `read_api`). Its `includes` list holds every include,
   nested ones too, each with `type` (`local`, `file` for a project
   include, `component`, `template`, `remote`), `location`,
   `extra.project` and `extra.ref`, `extra.rules`, `context_project` (the
   project whose file included it) and `blob` (a link pinned to the exact
   commit). Flag:
   - `extra.ref: "HEAD"`: a project include **without `ref`**, which
     follows that project's default branch, so a commit there changes this
     pipeline unreviewed;
   - an include whose rules were false is **absent** from the list (*lab:*
     a `template` include with a false `if` was missing): read the file
     itself for includes with `rules:`, and say which ones did not apply
     on this ref.
3. **Every job in its final form.** `glab ci config compile` in the
   repository prints each job with `extends` applied and `!reference`
   inserted (*lab*); the lint response's `merged_yaml` has the same
   content. `jobs` from the dry run lists the jobs a pipeline on that ref
   would have, with `when`. A static lint (without `dry_run`) lists every
   job whatever its rules.
4. **Downstream pipelines, from the configuration.** In `merged_yaml`,
   find the jobs with `trigger:`:
   - `trigger: include: <file>` or `- local:` / `- project:` / `- component:`:
     a **child pipeline**. Its file is not in the parent's `includes`
     list: lint it on its own, in the project's context, with
     `POST /projects/:id/ci/lint` and the content
     `include: [{local: <file>}]` (needs the `api` scope; *lab:* the child
     file's own project include came back resolved). With only
     `read_api`, read the file raw
     (`GET /projects/:id/repository/files/<url-encoded path>/raw?ref=<ref>`)
     and list its `include:` entries by hand.
   - `- artifact: <file>` with `job: <job>`: a **dynamic child pipeline**,
     written by that job at run time. Its content is known only from a
     pipeline that ran: `GET /projects/:id/jobs/<id of that job>/artifacts/<file>`
     (*lab*).
   - `trigger: project: <path>`: a **multi-project pipeline**. Repeat this
     procedure for that project and branch.
5. **Downstream pipelines, from a pipeline that ran** (when asked for
   what happened, or to catch what the configuration does not show):
   `GET /projects/:id/pipelines/<id>/bridges` gives each trigger job's
   `downstream_pipeline` (`id`, `project_id`, `source`: `parent_pipeline`
   or `pipeline`); repeat for each. Compare the jobs that ran
   (`GET .../pipelines/<id>/jobs`) with the configuration's list: a job
   that ran but is in no file came from outside the repository, such as a
   pipeline execution policy or compliance pipeline (Premium; ask a group
   owner which policies apply).
6. **Say what you could not see**: projects you cannot read (a 404 is
   also "no access"), child files you could not lint, dynamic children
   that never ran, `remote` includes, and rules that depend on variables
   only known at run time.

## Who uses this template or component

1. **With the script**: `--consumers <templates project> --group <group>`
   lints every project in the group (subgroups included, default
   branches) and lists each include of that project, and each project
   whose whole configuration points at it. *lab:* it found both the
   pinned and the unpinned include and the external configuration.
2. **By hand**: list the group's projects
   (`GET /groups/:id/projects?include_subgroups=true&per_page=100`) and
   for each, `GET /projects/:id/ci/lint` and read `includes`. This finds
   nested and component uses that a text search misses.
3. **Search**: on Community Edition only per project:
   `GET /projects/:id/search?scope=blobs&search=platform/templates`
   (*lab:* found `.gitlab-ci.yml` and `ci/child.yml`). Global and group
   code search need advanced search: without it the API answers `scope
   does not have a valid value` (*lab*).
4. **Sourcegraph, if its tools are connected** (`tools/sourcegraph.md`):
   one search across every repository finds candidates in seconds,
   including repositories outside the group. It sees text only, so an
   include written through a variable, a nested include or an external
   configuration can be missed: confirm each hit with the lint API or the
   script, and use the script for the group even when Sourcegraph found
   nothing.

## Never

- Never say a project has no CI because its repository has no
  `.gitlab-ci.yml`: check `ci_config_path` and Auto DevOps first.
- Never read only the top file: includes, `extends` and child pipelines
  are where most of a pipeline lives.
- Never report an include list as complete when an include has `rules`
  or a child file could not be linted; say what is missing.

## Stop and ask

- A project or file the map needs cannot be read with your token. Name
  it and ask for access, or for someone with access to run the script.
