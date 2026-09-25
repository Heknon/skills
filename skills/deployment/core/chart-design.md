# Chart design

**Verdict you produce:** which chart a service deploys with, where it
lives, and how its version moves.

```
chart:      <generic app chart vX.Y.Z | own chart in <path> | own chart with the library chart>
repository: <GitLab Helm repository of project N, channel stable | oci://...>
values:     <deploy/values.yaml, deploy/values-<env>.yaml>
versioning: <semver; who bumps; how consumers move>
```

## Which chart

Answer in order; the first yes decides.

1. **Does the service fit the generic chart?** One container image, run
   as a Deployment (web or worker), optionally a Service with a Route or
   Ingress, environment variables, Secrets by name, config files, a
   migration Job before upgrade, CronJobs with the same image. Then the
   **generic chart**, `recipes/generic-chart/app/`, and only values files
   in the service's repository. Most services fit.
2. **Does it need one or two things the generic chart lacks** that other
   services will want too (a sidecar, a volume claim)? **Add them to the
   generic chart** as optional values, off by default, as a minor version
   (`helm/generic-chart.md`).
3. **Is it a different shape**: a StatefulSet, an operator's custom
   resources, several cooperating Deployments? **Its own chart**, in the
   service's repository under `chart/`, deployed from that folder. If
   several such charts repeat the same helpers, share them in a **library
   chart** (`type: library`) as a dependency.
4. **Is it third-party software** (a database, a message broker)? Its
   upstream chart, **mirrored** into the internal repository at a pinned
   version, with values in the repository.

## Rules for the generic chart

1. **The values are its API.** Every key is in `values.yaml` with a
   comment, and in `values.schema.json` with `additionalProperties:
   false`, so a misspelt key fails the install instead of being ignored.
   The recipe's schema rejects `replicas` (for `replicaCount`) with
   `additional properties 'replicas' not allowed` and rejects the tag
   `latest`.
2. **Semantic versions.** A new optional value is a minor bump; a renamed
   or removed value, or a changed default that changes behaviour, is a
   major bump. The chart project's pipeline refuses a change without a
   version bump.
3. **Services pin the chart version** in their pipeline
   (`CHART_VERSION`), and move to a new one in a merge request, like any
   dependency.
4. **Secure by default**: the security context passes Kubernetes
   `restricted` and OpenShift `restricted-v2`; no `runAsUser`; a
   read-only root with a writable `/tmp`.
5. **Tested in its own project**: `helm lint --strict` and `helm template`
   with every file in `ci/*-values.yaml`, one per shape (web, worker, all
   options on).

## Never

- Never copy the generic chart into a service's repository to change one
  line. Add the option to the chart.
- Never put environment differences in templates (`if eq .Values.env
  "prod"`). They belong in values files.
- Never put secrets in values files, not even encrypted ones, unless the
  team runs a tool made for it and it is written down where.

## Stop and ask

- A change to the generic chart would change what existing services
  render with their current values. It is a major version; ask who owns
  the chart and how services will be moved.
