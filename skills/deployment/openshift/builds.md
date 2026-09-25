# Building images in OpenShift

When no GitLab runner can build images (`gitlab/images.md`), the cluster
can: a BuildConfig with the Docker strategy builds the repository's
Dockerfile in a build pod and pushes to the internal registry. Commands
checked against `oc` 4.22.14's help; *not run* on a cluster here.

## Once per project

```
oc new-build --binary --strategy=docker --name=web -n <p>
```

Creates a BuildConfig `web` that takes its source from an upload, and an
ImageStream `web`. The build's output is the ImageStreamTag `web:latest`.

## Per pipeline

A job with `oc` and a kubeconfig (the deployer can start builds with the
`edit` role):

```sh
oc start-build web --from-dir=. --follow --wait -n "$KUBE_NAMESPACE"
oc tag "web:latest" "web:$CI_COMMIT_SHA" -n "$KUBE_NAMESPACE"
oc get istag "web:$CI_COMMIT_SHA" -n "$KUBE_NAMESPACE" -o jsonpath='{.image.dockerImageReference}'
```

- `--from-dir=.` uploads the working directory, so a `.dockerignore`
  keeps it small.
- `--follow` streams the build log into the job; `--wait` makes the job
  fail when the build fails.
- The last command prints `image-registry.openshift-image-registry.svc:5000/<p>/web@sha256:...`:
  deploy that digest, as with any other image.
- Build arguments: `oc start-build ... --build-arg UV_IMAGE=...`. Build
  secrets are Secrets referenced in the BuildConfig, not files from the job.

## Limits

- The image lives in one project's internal registry; other clusters
  (production in another cluster) cannot pull it without mirroring.
- Cluster administrators can disable the Docker strategy; `oc start-build`
  then fails with a policy error. Ask.
