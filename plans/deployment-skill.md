# Plan: the deployment skill

Status: built in `skills/deployment/`. Decisions P1 to P6 below were taken
as defaults so the skill could be built; each can be changed.

## 1. What it is

The knowledge a platform engineer brings to getting code from a merge
request into a running Kubernetes or OpenShift workload: GitLab CI/CD
pipelines, shared CI templates and components, CI/CD variables and
secrets, the GitLab API and `glab`, container images, Helm charts and
chart repositories, a generic chart shared by many services, Kubernetes
workloads, and what OpenShift changes about all of it. It covers Python
projects and monorepos first.

It follows what the seniority and navigation evals taught: the skill
carries knowledge and judgement, not enforcement. It has procedures that
end in a verdict, reference files with the facts a model cannot look up,
and recipes that are complete files verified by running them.

## 2. The environment it is written for

- **A weak model, air gapped.** No web. Every keyword, flag, API path and
  default the model needs is written into the skill, stamped with the
  version it was verified against. The skill also teaches the two sources
  an air-gapped network still has: GitLab serves its own documentation at
  `/help` for the exact running version, and every CLI has `--help`.
- **Zed's agent on Windows.** Local commands are PowerShell. `curl` in
  Windows PowerShell 5.1 is an alias for `Invoke-WebRequest`; the skill
  writes `curl.exe` or `Invoke-RestMethod`. Jobs themselves run on Linux
  runners, so everything inside `.gitlab-ci.yml` is POSIX shell.
- **Self-managed GitLab, internal registries and mirrors.** Nothing is
  pulled from Docker Hub, PyPI or a public chart repository. Images, Python
  packages and charts come from internal mirrors or the GitLab package and
  container registries.
- **Deploying is outward facing.** Changing a cluster, a CI/CD variable, a
  protected branch or a registry is never done unasked. The skill prefers
  checks that change nothing: CI lint, `helm template`, `helm lint`,
  server-side dry run, `kubectl diff`, `auth can-i`.

## 3. The kinds of task

| Kind | Asked to | Answer shape |
| --- | --- | --- |
| **Orient** | explain how this project builds and deploys today | the path from commit to running pod, each hop with the file or command that shows it |
| **Pipeline** | write or change `.gitlab-ci.yml` | the file, and CI lint output |
| **Template** | build or change shared CI: includes, components, a templates project | the component files, their inputs, a test pipeline |
| **Monorepo** | make a pipeline for many packages in one repository | the parent and child files, and which change triggers what |
| **Variables** | decide where a value or secret lives, or why a variable has the wrong value | the place, its flags, and the precedence that decides it |
| **Chart** | write or change a Helm chart, a generic chart, or a chart repository | the chart, `helm lint` and `helm template` output |
| **Deploy** | deploy, promote or roll back a release | the command, what it changed, and how it was observed |
| **Access** | connect GitLab to a cluster, or talk to GitLab's API | the identity, its permissions, where its credential is stored |
| **Debug** | a pipeline, job, image or deployment fails | the failing hop on the ladder, the evidence, the fix |

## 4. The failures it targets

| Failure | What it looks like |
| --- | --- |
| **Keyword from memory** | `only/except` mixed with `rules`; `strategy: depend` where `mirror` exists; Helm 3 flags on Helm 4 |
| **Duplicate pipelines** | a branch pipeline and a merge request pipeline for every push |
| **`rules:changes` misread** | assumes it compares with the default branch in a branch pipeline, when on a new branch it is always true |
| **Secret leak** | `echo $TOKEN`, `set -x`, a token in `values.yaml` or in the repository, `helm get values` output pasted |
| **Mutable tags** | `latest` or a branch name deployed; a rollback that pulls a different image |
| **Build per environment** | the image rebuilt for staging and production instead of promoted |
| **OpenShift as Kubernetes** | image that needs root or a fixed UID, port 80, writes to `/app`; `Ingress` where the platform expects a `Route` |
| **Blind deploy** | `helm upgrade` without `--wait`, no probes, success reported from the command's exit code alone |
| **Copy-paste pipelines** | the same fifty lines in every repository instead of a component with inputs |
| **Variable in the wrong place** | a per-environment value as a project variable without environment scope; a secret as a pipeline variable |
| **Guessing the failure** | "probably a network issue" instead of reading the job log, the events and the pod status |

## 5. Layout

```
skills/deployment/
  SKILL.md               router over the nine kinds, invariants, answer shape
  glossary.md
  core/                  one procedure per task kind or dilemma
  gitlab/                keywords, rules, variables, includes and components,
                         downstream pipelines, Python, images, API, glab,
                         runners, job token, versions
  helm/                  chart anatomy, templating, generic charts, repositories,
                         commands with Helm 3 and 4 differences, testing
  kubernetes/            workloads, configuration, debugging, jobs and hooks
  openshift/             what differs, security context constraints, routes,
                         access from CI, oc
  recipes/               complete files, verified: a Python service pipeline,
                         a monorepo parent and child, a CI components project,
                         a generic chart, an OpenShift-ready Dockerfile
  examples/              worked tasks with the real commands and output
  evals/                 scenarios and sandboxes
```

## 6. How it was verified

A lab in the build container: GitLab CE 19.4.1 with a Docker-executor
runner 19.4.1, a Kubernetes 1.37 API server with its controller manager
(no nodes, so objects are admitted and controllers run, but pods are not
started), Helm 4.3.0 and 3.22.0, kubectl 1.37.1, oc 4.22.14 and glab.
Every recipe pipeline ran on that GitLab; every chart was linted,
rendered, validated and installed on that API server under the
`restricted` Pod Security level; the Dockerfile was run as an arbitrary
UID with group 0, the way OpenShift runs it. What could not be run there,
such as a real OpenShift cluster and its security context constraints, is
marked in the file that states it.

## 7. Decisions taken as defaults

### P1. Deploy by push from CI, with Helm

A deploy job runs `helm upgrade --install` against the cluster with a
namespace-scoped service account. It works on any GitLab and any cluster,
air gapped. The GitLab agent for Kubernetes and pull-based GitOps (Argo CD,
OpenShift GitOps) are documented as alternatives in `core/access.md`, and
chosen from facts. *Change it if* you already run Argo CD or the agent.

### P2. Components over copied includes

Shared CI lives in one project as CI/CD components with `spec:inputs`,
included by version. Plain `include:project` with `extends` is kept for
GitLab older than 17.0. *Change it if* your GitLab is older than 17.0.

### P3. One generic chart, versioned, in a chart repository

Services that share a shape (a web service, a worker, a cron job) deploy
with one generic application chart, published to the GitLab package
registry or an OCI registry, and each service keeps only values files.
Services that do not fit it keep their own chart. `core/chart-design.md`
decides.

### P4. Image builds with Buildah

kaniko is no longer maintained, and GitLab's own documentation lists it
as removed. Rootless Buildah builds without a privileged runner, which
OpenShift runners usually are not. Docker-in-Docker is documented for
runners that allow privileged containers.

### P5. Python through uv

As in seniority: `uv sync --locked`, `uv run`, an internal index. Wheels
are published to the GitLab PyPI registry with the job token.

### P6. Versions

Written against GitLab 19.4, Helm 4.3 with Helm 3.22 differences, Kubernetes
1.37 and OpenShift 4.22. `gitlab/versions.md` lists when each keyword the
skill uses arrived, so an older instance is handled by reading its version
first.

## 8. What the lab taught

Findings from running the recipes that changed the skill, each now written
into the file named:

- A job named `image` is read as the global `image:` keyword and the
  pipeline fails with `image name should be a string` (`gitlab/keywords.md`).
- Variables in a parent's `variables:` reach child pipelines as pipeline
  variables and outrank instance and group variables there, while losing
  to them in the parent (`gitlab/variables.md`, `examples/wrong-variable.md`).
- The POST form of the CI lint API takes `ref`; `dry_run_ref` is ignored
  there and the simulation silently uses the default branch (`gitlab/api.md`).
- `/help` redirects to docs.gitlab.com unless an administrator empties the
  Documentation pages URL (`SKILL.md`).
- Buildah in a non-privileged Docker executor needs seccomp unconfined; no
  capability or AppArmor change is enough (`gitlab/images.md`).
- Image builds behind an internal CA need the CA as a build secret
  (`core/images.md`).
- A private chart project answers the job token with `404`, fixed by its
  allowlist; an internal one needs no entry (`gitlab/job-token.md`).
- Without `--wait`, Helm 4 marks a release `deployed` with no pod ready;
  `--rollback-on-failure` cannot rescue a release whose previous revision
  was never healthy (`helm/versions.md`, `core/deploy.md`).
- `--set` turns an all-digit tag into a number (`helm/templating.md`).
- As a random UID, `HOME` is `/` and writing `~/.cache` fails; the recipe
  Dockerfiles set `HOME=/tmp` (`openshift/scc.md`).
- The chart's migration Job first carried the Deployment's selector labels,
  so the Service would have routed to it; fixed in
  `recipes/generic-chart/app/templates/migration-job.yaml`.
- In `variables:`, `yes` and `on` arrive as `true` and `1.10` as `1.1`
  (`gitlab/keywords.md`).

## 9. Not yet done

- A weak-model eval run of `evals/evals.json`, as the other skills had.
- A real OpenShift cluster: security context constraint messages, Routes
  through the router, and Buildah on OpenShift runners are written from
  the product's documented behaviour and marked *not run*.
