# Chart repositories

Two kinds: an HTTP repository (an `index.yaml` and `.tgz` files) and an
OCI registry. Both were used in the lab with Helm 4.3.0 and 3.22.0.

## GitLab's Helm repository (HTTP)

Each project has one, with channels (such as `stable`).

| Action | Command |
| --- | --- |
| push, in the chart project's pipeline | `curl --silent --show-error --fail-with-body --user "gitlab-ci-token:$CI_JOB_TOKEN" --form "chart=@app-1.0.0.tgz" "$CI_API_V4_URL/projects/$CI_PROJECT_ID/packages/helm/api/stable/charts"` answers `{"message":"201 Created"}` |
| add, in another project's pipeline | `echo "$CI_JOB_TOKEN" \| helm repo add platform "$CI_API_V4_URL/projects/<chart project id>/packages/helm/stable" --username gitlab-ci-token --password-stdin` |
| add, from a workstation | same URL with your username and a token with `read_api`, from `--password-stdin` |
| list versions | `helm search repo platform/app --versions` |
| the raw index | `GET /api/v4/projects/<id>/packages/helm/stable/index.yaml` |

- A private chart project must list consumer projects in its job token
  allowlist, or `helm repo add` fails with `index.yaml : 404 Not Found`
  (lab; `gitlab/job-token.md`).
- GitLab accepted a second push of the same chart version with `201
  Created` and no warning (lab). Never do it: one version could then mean
  two different archives. Versions are immutable by convention: bump.
- The chart project's recipe pipeline publishes only from a tag equal to
  `v<Chart.yaml version>` (`recipes/generic-chart/.gitlab-ci.yml`).

## OCI registries

| Action | Command |
| --- | --- |
| log in | `echo "$CI_REGISTRY_PASSWORD" \| helm registry login "$CI_REGISTRY" --username "$CI_REGISTRY_USER" --password-stdin` |
| push | `helm push app-1.0.0.tgz oci://$CI_REGISTRY_IMAGE/charts` (lab: `Pushed: .../charts/app:1.0.0` and a digest) |
| install | `helm upgrade --install web oci://registry.example.com/platform/charts/app --version 1.0.0 ...` |
| inspect | `helm show chart oci://registry.example.com/platform/charts/app --version 1.0.0` |

- No `helm repo add` for OCI; the reference goes on each command.
- The chart's name and version become the repository path's last element
  and the tag: `oci://<registry>/<path>/app:1.0.0`.
- A registry served over plain HTTP needs `--plain-http` (lab only;
  never in production). A registry with the internal CA needs
  `--ca-file <pem>` or the CA in the system store.
- GitLab's container registry accepts Helm charts as OCI artifacts.

## Dependencies

```yaml
# Chart.yaml
dependencies:
  - name: app
    version: 1.0.0
    repository: https://gitlab.example.com/api/v4/projects/42/packages/helm/stable
```

`helm dependency build <chart>` downloads into `charts/` and uses
`Chart.lock`; `helm dependency update` resolves again and rewrites the
lock. A repository needing credentials must first be added with `helm
repo add` under any name; Helm matches it by URL (lab).

## Air gapped

- Third-party charts are pulled once where the internet is reachable
  (`helm pull <repo>/<chart> --version X`), reviewed, and pushed to the
  internal repository or registry. Their images are mirrored too, and the
  chart's image values point at the mirror.
- Never install from a public repository URL in a pipeline.
