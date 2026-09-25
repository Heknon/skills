# Writing a Dockerfile

For images that run on Kubernetes and OpenShift, built by Buildah or
Docker in CI. The recipes are `recipes/python-service/Dockerfile` (one uv
project) and `recipes/monorepo/services/api/Dockerfile` (one member of a
uv workspace). *lab* marks what ran with Buildah 1.43.4 or Docker 29.3.1.

## The shape

```dockerfile
ARG UV_IMAGE=registry.example.com/mirror/astral-sh/uv:0.12-python3.12-trixie-slim
ARG PYTHON_IMAGE=registry.example.com/mirror/library/python:3.12-slim-trixie

FROM ${UV_IMAGE} AS build                 # stage 1: tools, compilers, caches
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /src
COPY pyproject.toml uv.lock ./            # what changes rarely, first
RUN uv sync --locked --no-dev --no-install-project
COPY . .                                  # what changes often, last
RUN uv sync --locked --no-dev --no-editable

FROM ${PYTHON_IMAGE}                      # stage 2: only what runs
COPY --from=build --chown=1001:0 /app/.venv /app/.venv
ENV PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HOME=/tmp
WORKDIR /app
RUN chgrp 0 /app && chmod g=u /app
USER 1001
EXPOSE 8080
CMD ["python", "-m", "web"]
```

## Rules

1. **Fully qualified base images, from the mirror, as `ARG`s.**
   `FROM python:3.12` is a short name: Buildah resolves it through an
   alias file to docker.io, which fails air gapped (*lab:* `pinging
   container registry registry-1.docker.io ... Temporary failure in name
   resolution`). Write `registry/path/name:tag`. Pin a digest
   (`name:tag@sha256:...`) where builds must be repeatable.
2. **An `ARG` before `FROM` is only for `FROM` lines.** Inside a stage it
   is empty unless declared again with `ARG NAME` (*lab:* `base=[unset]`).
3. **Two stages**: build tools and caches stay in the first; the second
   gets the finished virtual environment. Both base images need the same
   Python minor version, since the venv points at the interpreter's path.
4. **Order by change rate**: lock files and the dependency install first,
   code last. With layer caching on, a code change re-runs only the last
   install (*lab:* every step up to `COPY . .` was `Using cache`).
5. **`.dockerignore`** keeps `.git`, `.venv`, caches, test reports and
   `deploy/` out of the context. Buildah reads it too, and
   `.containerignore` first if both exist.
6. **Ownership at copy time, not by a later `chown -R` or `chgrp -R`.**
   A recursive change after the copy stores every file again in a new
   layer: *lab, Docker:* a 50 MB file then `chgrp -R 0 /app && chmod -R
   g=u /app` gave a second 50 MB layer and a 213 MB image instead of 113
   MB. Use `COPY --chown=1001:0` (and `--chmod=0775` where needed; both
   work in Buildah, *lab*), and make only the folders written at run time
   group writable.
7. **OpenShift**: a numeric `USER`; files the process writes owned by
   group 0 and group writable; a port of 1024 or more; `HOME=/tmp`
   (`openshift/scc.md`). *lab:* the recipe image served `/healthz` run as
   UID 1000680000, group 0, with a read-only root.
8. **`CMD` in exec form, and a process that ends on SIGTERM.** Kubernetes
   sends SIGTERM, waits `terminationGracePeriodSeconds`, then kills.
   *lab, `docker stop -t 10`:*

   | Container | Stopped after | Exit |
   | --- | --- | --- |
   | exec form, process handles SIGTERM | 0.2 s | 0 |
   | shell form (`sh -c "python ..."`), process handles SIGTERM | 10 s, killed | 137 |
   | exec form, `http.server` with no handler | 10 s, killed | 137 |
   | the same with an init process (`docker run --init`) | 0.2 s | 143 |

   A process running as PID 1 ignores SIGTERM unless it installs a
   handler. uvicorn and gunicorn handle it; a bare script needs
   `signal.signal(signal.SIGTERM, ...)`, or an init such as `tini` as
   `ENTRYPOINT ["tini", "--"]` (installed from the mirror). Otherwise
   every rollout waits out the grace period for every pod.
9. **Secrets as build secrets**: `RUN --mount=type=secret,id=netrc,target=/root/.netrc,required=false`.
   Never `ARG TOKEN` or `COPY .netrc`: build arguments stay in the image
   history, copied files in a layer even if deleted later.
10. **Cache mounts** for package downloads:
    `RUN --mount=type=cache,target=/root/.cache/uv uv sync ...` keeps uv's
    cache between builds on the same builder without putting it in the
    image (works in Buildah, *lab*).
11. **Labels** for tracing back: `org.opencontainers.image.revision` and
    `.source`, set by the pipeline with `--label`.
12. **No `HEALTHCHECK` for Kubernetes.** Kubernetes ignores it and uses
    the pod's probes. Buildah's default OCI format drops it with a warning
    (*lab:* `HEALTHCHECK is not supported for OCI image format and will be
    ignored`).
13. **No `latest`** in `FROM` of a production image, no `apt-get upgrade`
    (unrepeatable), and `apt-get install --no-install-recommends` with the
    lists removed in the same `RUN` when a system package is needed.

## Checking an image

```
buildah inspect --type image --format '{{.OCIv1.Config.User}} {{.OCIv1.Config.Cmd}} {{.OCIv1.Config.ExposedPorts}}' <image>
docker run --rm --user 1000680000:0 --read-only --tmpfs /tmp <image>     # as OpenShift runs it
docker run --rm --user 1000680000:0 --entrypoint sh <image> -c 'id; echo HOME=$HOME; touch /app/x'
docker history <image>                                                   # layer sizes
```

Without Docker, the same checks run in a pod on the cluster, or with
`oc debug deployment/<name> --as-user=<uid>` on OpenShift.
