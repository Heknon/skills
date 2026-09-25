# Worked example: a new Python service, from repository to staging

Kinds: Orient, Pipeline, Chart, Access, Deploy. Copy the order of the
steps and the answer's shape; change the names. The outputs are from the
lab run of `recipes/python-service/`.

## The ask

> We have a small Python service in `shop/web` (uv, pytest). Get it
> deploying to staging on OpenShift from GitLab, and to production when
> we tag a release.

## Steps

1. **Orient** (`core/orient.md`). No `.gitlab-ci.yml`, no chart, no
   Dockerfile. `pyproject.toml` and `uv.lock` exist; tests in `tests/`.
   Read versions: `GET /api/v4/version` gives `19.4.1`; the platform's
   generic chart is published by `platform/charts` (project 2) as
   `app-1.0.0`.
2. **Copy the recipe** `recipes/python-service/`: `.gitlab-ci.yml`,
   `Dockerfile`, `.dockerignore`, `deploy/`. Change the variables block:
   `CHART_PROJECT_ID: "2"`, the mirror image paths, the namespaces
   `shop-staging` and `shop-production`, the environment URLs. Change
   `CMD` in the Dockerfile to the service's module.
3. **Check the image runs as OpenShift runs it** (`core/verify.md`):
   ```
   buildah build ... -t web:test .
   docker run -d --user 1000680000:0 --read-only --tmpfs /tmp web:test
   wget -q -O- http://<container>:8080/healthz      -> ok
   ```
4. **Check the chart with the service's values** (`helm/generic-chart.md`):
   `helm template web platform/app --version 1.0.0 -f deploy/values.yaml
   -f deploy/values-staging.yaml --set-string image.repository=r/web
   --set-string image.tag=abc` renders a Deployment, a Service and a
   Route.
5. **Lint and dry-run the pipeline** (`gitlab/api.md`): `valid: true`;
   jobs for `main`: `lint, test, build-image, deploy-staging`; for
   `v0.1.1`: `lint, test, build-image, deploy-production:manual`.
6. **List what a person must do** (`core/access.md`): the deployer in
   each namespace, the `KUBECONFIG` File variables, the job token
   allowlist entry in `platform/charts`, the protected tag `v*`.
7. After the person did it and pushed: the pipeline on `main` passed; the
   deploy job printed `STATUS: deployed`, `REVISION: 1`, and the image
   `registry.../shop/web@sha256:15f3dfbf...`. The tag `v0.1.1` reused the
   same digest; its production job waited for a manual start.

## The answer

```
## Result
Added .gitlab-ci.yml, Dockerfile, .dockerignore and deploy/values*.yaml,
from the deployment skill's python-service recipe. Merge requests run lint
and test; main builds one image per commit and deploys it to shop-staging;
a tag vX.Y.Z reuses that image and deploys to shop-production when started
by hand. Deploys use platform/app 1.0.0 with --wait and --rollback-on-failure.

## Checked
- CI lint: valid: true, no warnings.
- Dry run for main: lint, test, build-image, deploy-staging.
- Dry run for v0.1.1: lint, test, build-image, deploy-production (manual).
- helm template with deploy/values.yaml and values-staging.yaml: Deployment,
  Service, Route; values schema accepted.
- Image run as UID 1000680000, group 0, read-only root: /healthz answered ok.

## Not checked
- The first real pipeline, with the project's runners and variables: see
  Build > Pipelines after the merge.
- The Route answering from outside: curl.exe https://<host>/healthz after
  the first staging deploy.

## Needs a person
- A project admin of shop-staging and shop-production: apply
  recipes/cluster-access/deployer.yaml in each (oc apply -n <project> -f ...).
- A Maintainer of shop/web: File variables KUBECONFIG, protected, scoped
  staging and production, from the deployer kubeconfigs (core/access.md).
- A Maintainer of platform/charts: add shop/web to its CI/CD job token
  allowlist, if platform/charts is private.
- A Maintainer of shop/web: protect tags v* (Settings > Repository >
  Protected tags), so production credentials reach tag pipelines only.
- An administrator of the namespace: the Secret web-secrets in
  shop-production, which values-production.yaml references.
```
