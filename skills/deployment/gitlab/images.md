# Building images in GitLab CI

Checked on GitLab 19.4.1 with runner 19.4.1 (Docker executor) and Buildah
1.43.4, in the lab.

The Buildah CLI in depth, its configuration files and its errors:
`containers/buildah.md`. Writing the Dockerfile: `containers/dockerfile.md`.

## Choose the builder

| Builder | Needs from the runner | Use when |
| --- | --- | --- |
| **Buildah, rootless** | Docker executor: `security_opt = ["seccomp:unconfined"]` for the job container. Kubernetes executor on OpenShift: an SCC that allows user namespaces for the build pod (ask the cluster admin; not tested here) | default; no privileged container |
| Docker-in-Docker | `privileged = true` and a `docker:dind` service | the runner is already privileged and the team knows Docker |
| BuildKit rootless | like Buildah: permission to create user namespaces | the team uses BuildKit features |
| OpenShift build | none from the runner; an `oc` login with rights to start builds | no runner can build (`openshift/builds.md`) |
| kaniko | | **not maintained**; GitLab's documentation lists it as removed. Replace it |

Add `--layers` to `buildah build` in CI, with `--cache-to` and
`--cache-from` a registry repository to share the cache between jobs:
Buildah caches nothing by default (`containers/buildah.md`).

*lab:* Buildah in an unprivileged Docker container failed with `Error
during unshare(CLONE_NEWUSER): Operation not permitted` until seccomp was
unconfined; adding capabilities or unconfining AppArmor alone did not help.

## The Buildah job

From the recipes:

```yaml
build-image:
  image: $BUILDAH_IMAGE
  variables:
    STORAGE_DRIVER: vfs          # overlay on overlay fails inside a container
    BUILDAH_ISOLATION: chroot    # no nested user namespace for RUN steps
    BUILDAH_FORMAT: docker
  before_script:
    - echo "$CI_REGISTRY_PASSWORD" | buildah login --username "$CI_REGISTRY_USER" --password-stdin "$CI_REGISTRY"
  script:
    - buildah build --tag "$IMAGE:$CI_COMMIT_SHA" .
    - buildah push --digestfile image.digest "$IMAGE:$CI_COMMIT_SHA"
    - echo "IMAGE_DIGEST=$(cat image.digest)" > image.env
  artifacts:
    reports:
      dotenv: image.env
```

- `buildah push --digestfile` writes `sha256:...`; the dotenv report hands
  it to deploy jobs that `needs` this job.
- Reuse: `buildah pull --quiet "$IMAGE:$CI_COMMIT_SHA"` succeeds when the
  image exists; skip the build then (the recipe does).
- A second tag: `buildah push "$IMAGE:$CI_COMMIT_SHA" "docker://$IMAGE:$CI_COMMIT_TAG"`.
- Build secrets: `buildah build --secret id=netrc,src=<file>` and in the
  Dockerfile `RUN --mount=type=secret,id=netrc,target=/root/.netrc,required=false ...`.
  `required=false` lets the same Dockerfile build without the secret.
- The `quay.io/buildah/stable` image has `git` and `curl`, but not
  `skopeo`, `podman` or `jq` (checked on 1.43.4).

## Registries

- The project's registry: `$CI_REGISTRY`, `$CI_REGISTRY_IMAGE`, user
  `$CI_REGISTRY_USER`, password `$CI_REGISTRY_PASSWORD` (the job token).
  These variables exist only when the container registry is enabled.
- Another project's registry: a deploy token of that project with
  `read_registry` or `write_registry`, stored as masked variables.
- A registry with the internal CA: the builder trusts
  `/etc/containers/certs.d/<registry host>/ca.crt`. The runner
  administrator mounts it there (`gitlab/runners.md`). Buildah pulls
  `FROM` images through the same trust (lab: `x509: certificate signed by
  unknown authority` until the CA was mounted).
- Never `--tls-verify=false`.

## Docker-in-Docker, for reference

```yaml
build-image:
  image: $DOCKER_IMAGE
  services:
    - name: $DOCKER_DIND_IMAGE
      alias: docker
  variables:
    DOCKER_HOST: tcp://docker:2376
    DOCKER_TLS_CERTDIR: "/certs"
  script:
    - echo "$CI_REGISTRY_PASSWORD" | docker login -u "$CI_REGISTRY_USER" --password-stdin "$CI_REGISTRY"
    - docker build -t "$IMAGE:$CI_COMMIT_SHA" .
    - docker push "$IMAGE:$CI_COMMIT_SHA"
```

Needs a runner with `privileged = true`; not tested in the lab.
