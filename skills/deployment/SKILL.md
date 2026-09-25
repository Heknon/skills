---
name: deployment
description: Get code from a merge request to a running workload on Kubernetes or OpenShift, with GitLab CI/CD and Helm. Write and fix .gitlab-ci.yml for Python projects and monorepos, build shared CI components and templates, decide where a CI/CD variable or secret lives and why it has the value it has, discover every include and downstream pipeline behind a project, connect through the GitLab REST API and glab, write Dockerfiles and build images with Buildah, use the Helm CLI, write a generic Helm chart and publish it to a chart repository, deploy, promote and roll back releases, connect a pipeline to a cluster, make images and charts pass OpenShift's security constraints, and debug a failing pipeline, job, image or rollout from its evidence. Verified against GitLab 19.4, Helm 4.3 and 3.22, Kubernetes 1.37 and OpenShift 4.22 clients.
---

# Deployment

This skill knows how pipelines, charts and clusters behave, and it has
recipes that were run. Every answer rests on a file you read, a command
you ran, or a line in this skill. Never write a keyword, flag, API path or
default from memory: find it here, in the instance's own `/help` pages, or
in the tool's `--help`.

Read this file, then load only the files the task needs.

## The eleven kinds of task

Decide which kind you have. Most tasks start with **Orient**. A task often
needs several kinds in turn, such as Orient, then Pipeline, then Deploy.

| Kind | You were asked to | Load |
| --- | --- | --- |
| **Orient** | explain how this project builds and deploys today | `core/orient.md` |
| **Discover** | map every file, include, job and downstream pipeline behind a project's pipelines; find who uses a template or component | `core/discover.md`, `recipes/tools/ci_map.py` |
| **Pipeline** | write or change `.gitlab-ci.yml`; make a job run or not run | `core/pipeline.md`, `core/when-jobs-run.md` |
| **Shared CI** | build or change templates, includes or CI/CD components | `core/shared-ci.md` |
| **Monorepo** | run only what changed in a repository with many units | `core/monorepo.md` |
| **Image** | write or fix a Dockerfile; build, tag, push or inspect an image; use Buildah | `core/images.md`, `containers/dockerfile.md`, `containers/buildah.md` |
| **Variables** | decide where a value or secret lives; find why a variable has a wrong or empty value | `core/variables.md` |
| **Chart** | write or change a Helm chart, a generic chart, or a chart repository | `core/chart-design.md` |
| **Deploy** | deploy, promote or roll back a release; choose image tags | `core/deploy.md`, `core/images.md` |
| **Access** | connect to GitLab (REST API, `glab`) and prove who you are; connect a pipeline to a cluster | `core/connect.md`, `core/access.md` |
| **Debug** | a pipeline, job, image build, release or pod fails | `core/debug.md` |

Before you say any change is done, load `core/verify.md`.

## Where the facts are

| Folder | Holds |
| --- | --- |
| `gitlab/` | keywords, rules, variables, includes and components, downstream pipelines, environments, Python jobs, image builds, runners, job token, REST API, `glab`, GitLab's optional MCP server, and which GitLab version added what |
| `containers/` | writing Dockerfiles; the Buildah CLI, its configuration and errors |
| `helm/` | Helm 3 and 4 differences, the CLI, chart anatomy, templating, the generic chart, repositories, commands, hooks |
| `kubernetes/` | workloads, configuration and secrets, security context, RBAC, debugging |
| `openshift/` | what OpenShift changes, security context constraints, Routes, access from CI, in-cluster builds, `oc` |
| `tools/` | optional tools, used only when they appear among your tools: Sourcegraph for search across every repository (`tools/sourcegraph.md`) |
| `recipes/` | complete files that ran: `python-service/`, `monorepo/`, `ci-components/`, `generic-chart/`, `cluster-access/`, and `tools/ci_map.py`, a read-only script that maps a project's pipelines |
| `examples/` | three finished tasks: a new service (`new-python-service.md`), a variable with the wrong value (`wrong-variable.md`), a deploy that fails on OpenShift (`openshift-permission-denied.md`) |

`glossary.md` fixes the words. A recipe is copied whole and changed only
where its top comment says; it is the fastest way to a working file.

## Read the versions first

Features and flags differ by version. Before you write configuration or a
command for a system, read its version, and write for that version:

| System | Command |
| --- | --- |
| GitLab | `GET /api/v4/version` (`gitlab/api.md`), or the Help page of the instance |
| GitLab Runner | the first line of any job log: `Running with gitlab-runner 19.4.1` |
| Helm | `helm version` |
| Kubernetes | `kubectl version` |
| OpenShift | `oc version` |

`gitlab/versions.md` says which GitLab version added each keyword this
skill uses. `helm/versions.md` has the Helm 3 and Helm 4 flag differences.

When a fact is not in this skill, the instance's own documentation for its
exact version is the next source, at `https://<gitlab>/help/<path>.md`,
such as `/help/ci/yaml/_index.md`. By default `/help` redirects to
docs.gitlab.com, which an air-gapped network cannot reach. Ask an
administrator to make the instance serve the pages itself by emptying
**Admin > Settings > Preferences > Help page > Documentation pages URL**
(verified on 19.4; it takes effect in about a minute); never change it
yourself. Without it, say the fact is unverified instead of recalling it.

## Invariants

1. **Nothing changes outside the repository unasked.** Deploying, running
   or retrying a pipeline, creating or changing a CI/CD variable, a
   protected branch, a runner, a registry, a namespace or a cluster
   object: each is done only when the person asked for that action. When
   they asked for the goal and not the action, prepare it and say what
   will run.
2. **Production is challenged before it is touched.** Say what will
   change, what could break, how to undo it, and what you checked first.
   Never delete a release, namespace, PersistentVolumeClaim or Secret to
   make an error go away.
3. **A secret never appears.** Not in the repository, a values file, a
   job log, a command line, or your answer. Never print one to check it:
   check its presence and length (`gitlab/variables.md`). Never run
   `set -x` or `env` in a job that holds secrets.
4. **One image per commit, promoted, never rebuilt.** Deploy by commit SHA
   tag or digest. `latest` and branch names are never deployed.
5. **Configuration in the repository, secrets in CI/CD variables or the
   cluster.** A value that is not secret lives in `.gitlab-ci.yml` or a
   values file where review sees it (`core/variables.md`).
6. **A deploy is done when the workload is ready, not when the command
   returned.** `--wait`, then the rollout status, the pods and the events.
7. **The error message is the first evidence.** Read the failing job's log
   and the cluster's events before any hypothesis. "Probably the network"
   is not a finding (`core/debug.md`).
8. **Check before you claim.** CI lint for pipelines, `helm lint` and
   `helm template` for charts, a server-side dry run or `kubectl diff` for
   cluster changes (`core/verify.md`). Say which ran and paste its
   verdict line.
9. **OpenShift runs your image as a random user in group 0.** Every image
   and chart is written for that, even for plain Kubernetes
   (`openshift/scc.md`).
10. **What the person must do is named, not assumed.** A variable only a
    Maintainer can set, a role only an admin can grant, an approval only a
    person can give: list each one with where it is done.

## What you say when you finish

End with these headings, in this order, each with `none` when empty.
If another skill is loaded, its headings come first and these after.

```
## Result
<the files changed, the cause found, or the answer, with paths>

## Checked
<each check: the command, and the line of its output that shows the verdict>

## Not checked
<what could only be seen on the real GitLab or cluster, and how to see it>

## Needs a person
<each setting, permission, variable or approval someone must provide, and where>
```

The `evals/` folder is for people testing this skill. Never open it while
doing a task.
