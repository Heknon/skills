# The generic chart

`recipes/generic-chart/` holds the chart (`app/`) and its project's
pipeline. Verified with Helm 4.3.0 and 3.22.0: `helm lint --strict` and
`helm template` with each `ci/*-values.yaml`, kubeconform against
Kubernetes 1.33 schemas, a server-side dry run, and installs under the
Pod Security `restricted` level on a Kubernetes 1.37 API server with the
OpenShift Route API added.

## What it deploys

| Values | Objects |
| --- | --- |
| always | Deployment |
| `service.enabled` (default true) | Service on port `service.port`, to the container's `http` port |
| `route.enabled` | OpenShift Route with TLS `route.termination` (default `edge`) |
| `ingress.enabled` | Ingress; `fail`s if a Route is enabled too |
| `config.files` | ConfigMap mounted at `config.mountPath`; pods restart when it changes |
| `autoscaling.enabled` | HorizontalPodAutoscaler on CPU |
| `podDisruptionBudget.enabled` and more than one replica | PodDisruptionBudget, `maxUnavailable: 1` |
| `serviceAccount.create` | ServiceAccount, with its token mounted; otherwise no token is mounted |
| `migration.enabled` | Job run as a `pre-install,pre-upgrade` hook (`helm/hooks.md`) |
| `cronJobs.<name>` | CronJob per entry, `concurrencyPolicy: Forbid` |

Every pod: `runAsNonRoot`, `seccompProfile: RuntimeDefault`, no privilege
escalation, all capabilities dropped, read-only root, an `emptyDir` at
`/tmp`; no `runAsUser` or `fsGroup`, so OpenShift assigns them. Probes are
HTTP on `probes.path`: startup (for up to `probes.startupSeconds`), then
readiness and liveness. The rollout keeps old pods until new ones are
ready (`maxUnavailable: 0`).

## A service's values

```yaml
# deploy/values.yaml
env:
  LOG_LEVEL: info
probes:
  path: /healthz
resources:
  requests: {cpu: 100m, memory: 128Mi}
  limits: {memory: 256Mi}

# deploy/values-production.yaml
replicaCount: 3
route:
  enabled: true
  host: web.example.com
envFromSecrets: [web-secrets]
```

The pipeline sets `image.repository`, `image.tag` and `image.digest`
with `--set-string`. A worker sets `service.enabled: false` and `args`.

## Changing the chart

1. Add the value to `values.yaml` with a comment and a default that keeps
   today's output unchanged.
2. Add it to `values.schema.json` (types, `additionalProperties: false`).
3. Use it in a template; render with every `ci/*-values.yaml` and a new
   one that turns it on.
4. Bump `version` in `Chart.yaml`: minor for a new optional value, major
   for anything that changes what existing values render. The chart
   project's pipeline fails a merge request that changes `app/` without
   a new version (lab).
5. Merge, tag `vX.Y.Z` equal to the chart version; the tag pipeline
   publishes it. Services move to it in their own merge requests.

## Checking what a service's values render

```
helm template web app -f deploy/values.yaml -f deploy/values-production.yaml `
  --set-string image.repository=r/web --set-string image.tag=abc123 `
  --api-versions route.openshift.io/v1
```

(PowerShell continues lines with a backtick.) With a chart from the
repository, `helm template web platform/app --version 1.0.0 ...` after
`helm repo add` (`helm/repositories.md`).
