# Images

**Verdict you produce:** how the image is built, named, tagged, found by
the deploy, and pulled by the cluster.

```
builder:   <buildah | docker-in-docker | buildkit rootless | OpenShift build>  (gitlab/images.md)
name:      <registry/path>
tags:      <full commit SHA; plus vX.Y.Z on release tags>
deployed:  <by digest, from the build job's dotenv report>
base:      <base images, from which mirror, same Python minor in both stages>
pull:      <how the cluster authenticates: pull secret name, or internal registry>
```

## Rules

1. **Tag with the full commit SHA** (`$CI_COMMIT_SHA`). It is unique and
   says which code is inside. A release tag adds a second tag to the same
   image; it never builds a new one.
2. **Deploy by digest** when the build job can report it (`buildah push
   --digestfile`), else by the SHA tag. A digest cannot be moved by a
   later push; a tag can.
3. **Build once per commit.** Before building, try to pull the SHA tag;
   if it exists, reuse it. In the lab, the tag pipeline found the image
   the default branch had built and pushed the same digest again.
4. **Never deploy `latest` or a branch name.** A rollback to such a tag
   pulls whatever it points at now.
5. **Base images come from the mirror**, as build arguments with the
   mirror path as default, so a mirror move needs no Dockerfile edit.
6. **Written for OpenShift**: numeric non-root `USER`, files the process
   writes owned by group 0 and group writable, port 1024 or higher, no
   `sudo`, no `chown` at start (`openshift/scc.md`). The recipe Dockerfile
   does this and ran as UID 1000680000, group 0, with a read-only root.
7. **Secrets reach the build as build secrets**, never as build arguments
   or copied files: `buildah build --secret id=netrc,src=$INDEX_NETRC`
   and `RUN --mount=type=secret,id=netrc,target=/root/.netrc`. A build
   argument is stored in the image history.
8. **Label the image** with `org.opencontainers.image.revision` and
   `org.opencontainers.image.source`, so an image found in a cluster leads
   back to its commit.
9. **The internal CA** reaches the build as a secret too (`--secret
   id=ca,...`), when the package index uses it. Without it, `uv` fails with
   `invalid peer certificate: UnknownIssuer` (seen in the lab).

## Pulling in the cluster

| Registry | What the namespace needs |
| --- | --- |
| GitLab container registry, private project | a pull secret of type `kubernetes.io/dockerconfigjson` from a deploy token with `read_registry`, named in the chart's `imagePullSecrets` or linked to the service account (`openshift/access.md`) |
| internal mirror with anonymous pull | nothing |
| OpenShift internal registry, same project | nothing: the `default` service account can pull |

## Never

- Never `docker login` with a personal token in a pipeline. Use
  `CI_REGISTRY_USER` and `CI_REGISTRY_PASSWORD` for the project's own
  registry, and a deploy token for anything else.
- Never pass `--tls-verify=false` or mark a registry insecure to get past a
  certificate error. Give the builder the CA.
- Never rebuild an image for production "to be safe": it is a different
  image from the one that was tested.

## Stop and ask

- No runner can build images (no privileged Docker, Buildah blocked by
  seccomp or the SCC). Ask for a runner with the setting in
  `gitlab/images.md`, or use an OpenShift build (`openshift/builds.md`).
