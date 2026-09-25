# Buildah

Builds OCI and Docker images without a daemon. Checked with Buildah 1.43.4
(`quay.io/buildah/stable`), inside unprivileged Docker containers as a
GitLab job runs it (*lab*). Buildah runs on Linux only; on a Windows
workstation it runs inside WSL or a Linux VM, or the build is left to CI.
Podman's `podman build` uses the same code and flags.

## Running it in a container

| Setting | Why |
| --- | --- |
| seccomp unconfined for the container | *lab:* without it every build failed with `Error during unshare(CLONE_NEWUSER): Operation not permitted`; capabilities or AppArmor changes alone did not help |
| `STORAGE_DRIVER=vfs` | overlay on the container's own overlay file system fails; vfs is slower and uses more disk, and works everywhere |
| `BUILDAH_ISOLATION=chroot` | `RUN` steps without a nested user namespace |
| `BUILDAH_FORMAT=docker` | keeps Docker-only fields such as `HEALTHCHECK`; the default is `oci` |

## Commands

| Task | Command |
| --- | --- |
| build | `buildah build -f Dockerfile -t <image>:<tag> <context>` |
| log in, secret from stdin | `echo "$CI_REGISTRY_PASSWORD" \| buildah login --username "$CI_REGISTRY_USER" --password-stdin "$CI_REGISTRY"` |
| who am I logged in as | `buildah login --get-login <registry>` |
| push, and record the digest | `buildah push --digestfile image.digest <image>:<tag>` |
| push under another name | `buildah push <local image> docker://<registry>/<path>:<tag>` |
| push to a file | `buildah push <image> docker-archive:out.tar:<name>:<tag>` (or `oci-archive:`); `docker load -i out.tar` reads it |
| pull | `buildah pull --quiet <image>` (exit code 0 means it exists: the recipes' "already built" check) |
| tag locally | `buildah tag <image> <other name>` |
| list, inspect | `buildah images`; `buildah inspect --type image --format '{{.OCIv1.Config.User}}' <image>` |
| clean up | `buildah rmi <image>`, `buildah rmi --prune`, `buildah prune` (build cache) |
| where things are | `buildah info` (*lab:* `vfs /var/lib/containers/storage`) |

## `buildah build` flags that matter

| Flag | Default | Use |
| --- | --- | --- |
| `--layers` (or `BUILDAH_LAYERS=true`) | **off** | keep a layer per step and reuse unchanged ones. *lab:* without it, an unchanged second build re-ran every step |
| `--cache-to <repo>`, `--cache-from <repo>` | | share the layer cache between CI jobs through a registry repository; needs `--layers`. *lab:* in the python-service recipe's pipeline, a second commit that changed only code reused every step up to the dependency install (`Using cache`), with each job starting from empty storage |
| `--secret id=<id>,src=<file>` | | a file for `RUN --mount=type=secret,id=<id>`, never stored in the image |
| `--build-arg NAME=value`, `--build-arg-file <file>` | | values for `ARG`; stored in the image's history: not for secrets |
| `--label`, `--annotation` | | image metadata, such as `org.opencontainers.image.revision=$CI_COMMIT_SHA` |
| `--target <stage>` | last stage | build only up to a named stage |
| `--format docker\|oci` | `oci` | *lab:* `oci` drops `HEALTHCHECK` with a warning |
| `--pull=missing\|always\|never\|newer` | `missing` | `always` to pick up a moved base tag; `never` in a fully offline build |
| `--platform linux/amd64,linux/arm64` with `--manifest <list>` | host's | multi-architecture; `RUN` steps for another architecture need qemu emulation on the builder (not run here) |
| `--no-cache` | | ignore cached layers |
| `--iidfile <file>` | | write the image id |
| `--timestamp <seconds>`, `--source-date-epoch`, `--rewrite-timestamp` | now | repeatable image digests |
| `--squash` | | one layer; loses layer reuse on pull |
| `--retry <n>` | 3 | pull and push retries |
| `--tls-verify` | true | **never false**; give the CA instead |
| `--authfile <file>` | | a credentials file other than the default |

## Credentials and trust

- `buildah login` writes `${XDG_RUNTIME_DIR}/containers/auth.json`; as
  root without that variable, `/run/user/0/containers/auth.json` (*lab*).
  `REGISTRY_AUTH_FILE` or `--authfile` pick another file. Docker's
  `~/.docker/config.json` is also read.
- A registry's CA: `/etc/containers/certs.d/<registry host[:port]>/ca.crt`
  (*lab:* a pull failed with `x509: certificate signed by unknown
  authority` until the CA was mounted there), or `--cert-dir`.

## Mirrors and short names: `registries.conf`

`/etc/containers/registries.conf` and files in
`/etc/containers/registries.conf.d/`. A mirror lets an unchanged
`FROM docker.io/library/alpine:3.22` pull from the internal registry:

```toml
[[registry]]
prefix = "docker.io"
location = "docker.io"

[[registry.mirror]]
location = "registry.example.com/dockerhub"
```

*lab:* with docker.io unreachable, the build succeeded through the mirror,
yet the log still said `Trying to pull docker.io/library/alpine:3.22...`:
the log names the reference, not the mirror. Without the file, the same
build failed. `insecure = true` on a mirror is for plain-HTTP labs only.

Short names (`FROM alpine`) resolve through `unqualified-search-registries`
and the alias files in `registries.conf.d` (the image's set
`"alpine" = "docker.io/library/alpine"`), with `short-name-mode =
"enforcing"`. Write full names instead.

## Scripted builds, without a Dockerfile

```sh
c=$(buildah from registry.example.com/mirror/library/alpine:3.22)
buildah run "$c" -- sh -c 'echo hi > /hello'
buildah copy "$c" ./config.toml /etc/app/config.toml
buildah config --user 1001 --cmd '["cat","/hello"]' --label org.opencontainers.image.source="$CI_PROJECT_URL" "$c"
buildah commit "$c" registry.example.com/team/tool:1.0
buildah rm "$c"
```

*lab:* the result's config showed `User 1001` and `Cmd [cat /hello]`.
Useful when a build needs logic a Dockerfile cannot express; otherwise
prefer the Dockerfile, which reviewers can read.

## Errors

| Error | Cause |
| --- | --- |
| `Error during unshare(CLONE_NEWUSER): Operation not permitted` | the container's seccomp profile; the runner needs `security_opt = ["seccomp:unconfined"]` |
| `x509: certificate signed by unknown authority` pulling `FROM` or pushing | the registry's CA is not in `certs.d` |
| `invalid peer certificate: UnknownIssuer` inside a `RUN` (uv, pip, curl) | the build step does not trust the internal CA: pass it as a build secret (`gitlab/images.md`) |
| `pinging container registry registry-1.docker.io` | a short or docker.io name without a mirror, air gapped |
| `HEALTHCHECK is not supported for OCI image format` | warning only; `--format docker` keeps it, Kubernetes ignores it anyway |
| `image not known` on push | the build failed earlier or used another tag; read up the log |
| `unauthorized` on push | not logged in to that registry, or the token cannot write to that path |
