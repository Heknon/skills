# Glossary

One sentence per term. Use these words and no synonyms.

## GitLab CI/CD

| Term | Meaning |
| --- | --- |
| pipeline | Every job GitLab created for one commit and one trigger; its source is in `CI_PIPELINE_SOURCE`. |
| branch pipeline | A pipeline for a push to a branch; `CI_COMMIT_BRANCH` is set. |
| merge request pipeline | A pipeline for a merge request's source branch; `CI_PIPELINE_SOURCE` is `merge_request_event` and `CI_COMMIT_BRANCH` is not set. |
| tag pipeline | A pipeline for a pushed tag; `CI_COMMIT_TAG` is set and `CI_COMMIT_BRANCH` is not. |
| parent pipeline, child pipeline | A pipeline, and one it started from its own repository with `trigger:include`; the child's source is `parent_pipeline`. |
| multi-project pipeline | A pipeline started in another project with `trigger:project`. |
| trigger job | A job with `trigger:`; it runs no script and starts a downstream pipeline. GitLab's API calls it a bridge. |
| stage | A named group of jobs; without `needs`, a stage starts when the previous one finished. |
| job | One script run by a runner in one container; the unit that passes or fails. |
| hidden job | A top-level key starting with `.`; never runs, exists to be extended or referenced. |
| rules | The list a job or `workflow` evaluates to decide whether it exists in a pipeline and how it runs; first match wins. |
| workflow | The top-level `workflow:rules` that decides whether a pipeline is created at all. |
| artifact | Files a job uploads for later jobs and for download; passed with `needs` or `dependencies`. |
| dotenv report | An artifact of `NAME=value` lines whose variables later jobs receive. |
| cache | Files kept between pipelines to save work, such as package downloads; never used to pass results between jobs. |
| environment | A named deploy target in GitLab, such as `staging` or `production/api`, with its deployments and history. |
| resource group | A name that lets only one job at a time run across all pipelines of a project. |
| runner | The agent that picks up jobs; its executor (Docker, Kubernetes, shell) decides where the script runs. |
| include | Pulling YAML from another file, project or template into this configuration. |
| CI/CD component | A versioned, reusable configuration file in a project's `templates/` folder, included with `include:component` and configured with `inputs`. |
| input | A typed parameter of a component or a configuration file, declared in `spec:inputs`, fixed when the pipeline is created, and used as `$[[ inputs.name ]]`. |
| CI/CD variable | A name and value available to jobs, from the configuration, the settings of a project, group or instance, or the pipeline's trigger. |
| predefined variable | A variable GitLab sets for every job, such as `CI_COMMIT_SHA`. |
| pipeline variable | A variable given when the pipeline was created: run page, schedule, API, trigger, push option, or upstream pipeline. |
| protected variable | A variable given only to pipelines on protected branches and protected tags. |
| masked variable | A variable whose value is replaced with `[MASKED]` in job logs. |
| hidden variable | A masked variable whose value can never be read back in the settings or the API. |
| file variable | A variable whose value GitLab writes to a temporary file; the variable holds the file's path. |
| environment scope | The environments a variable reaches, such as `production` or `staging/*`; `*` is all. |
| job token | `CI_JOB_TOKEN`, a token valid while the job runs, with the rights of the user who started it, limited by allowlists. |

## Images

| Term | Meaning |
| --- | --- |
| image repository | The path without tag, such as `registry.example.com/shop/web`. |
| tag | A movable name for an image in a repository, such as the commit SHA or `v1.2.0`. |
| digest | `sha256:...`, the content hash of an image manifest; it never moves. |
| immutable tag | A tag that is never pushed twice, such as the full commit SHA. |
| promotion | Deploying to the next environment the same image, by digest or immutable tag, that passed the previous one. |
| mirror | An internal registry or index holding copies of external images, packages and charts. |

## Helm and Kubernetes

| Term | Meaning |
| --- | --- |
| chart | A versioned package of Kubernetes templates, with `Chart.yaml` and `values.yaml`. |
| generic chart | One chart deployed by many services, each with its own values files. |
| library chart | A chart of named templates only, used as a dependency by other charts; it installs nothing. |
| values | The inputs a chart's templates read; `values.yaml` holds the defaults, `-f` and `--set` override. |
| values schema | `values.schema.json`, the JSON Schema Helm checks values against before rendering. |
| release | One installation of a chart in one namespace, under a name, with numbered revisions. |
| revision | One version of a release; `helm history` lists them, `helm rollback` returns to one. |
| hook | A template Helm runs at a point in the release life cycle, such as `pre-upgrade`, instead of with the rest. |
| chart repository | An HTTP location serving `index.yaml` and chart archives, or an OCI registry holding charts. |
| namespace | The Kubernetes scope of names and permissions; OpenShift calls it a project. |
| workload | A Deployment, StatefulSet, Job or CronJob and the pods it runs. |
| rollout | A Deployment replacing its pods with a new template, observed with `kubectl rollout status`. |
| probe | A check the kubelet runs on a container: startup, readiness (receives traffic) and liveness (restart). |
| service account | The identity pods and pipelines use to call the Kubernetes API. |
| deployer | The service account a pipeline deploys with, limited to one namespace. |
| Pod Security Admission | The Kubernetes admission check that enforces the `privileged`, `baseline` or `restricted` level per namespace. |

## OpenShift

| Term | Meaning |
| --- | --- |
| project | An OpenShift namespace with extra metadata, created with `oc new-project`. |
| security context constraint (SCC) | OpenShift's admission policy for what a pod may run as; `restricted-v2` is the default. |
| UID range | The block of user ids a project owns, in the annotation `openshift.io/sa.scc.uid-range`; pods run with a UID from it. |
| Route | OpenShift's object that exposes a Service through the cluster's router, with a host and TLS termination. |
| edge, passthrough, reencrypt | Route TLS modes: the router ends TLS; the pod ends TLS; the router ends it and opens new TLS to the pod. |
| ImageStream | An OpenShift object that tracks image tags and can trigger builds and deployments. |
| BuildConfig | An OpenShift object that builds an image inside the cluster. |
