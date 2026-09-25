# Recipe: image for a Python service managed by uv, runnable on OpenShift.
# Copy whole. Change: the module in CMD, and the two image defaults to your mirror.
# Needs: pyproject.toml and uv.lock at the root, code under src/.
# Build: buildah build --build-arg PYTHON_IMAGE=... --build-arg UV_IMAGE=... -t <image> .
# Optional build secrets, never baked into a layer:
#   --secret id=netrc,src=<file>  credentials for a private package index, in .netrc format
#   --secret id=ca,src=<file>     the internal CA certificate, when the index uses it

# Both images must carry the same Python minor version: the virtual environment
# built in the first stage points at the interpreter path of the second.
ARG UV_IMAGE=registry.example.com/mirror/astral-sh/uv:0.12-python3.12-trixie-slim
ARG PYTHON_IMAGE=registry.example.com/mirror/library/python:3.12-slim-trixie

FROM ${UV_IMAGE} AS build
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /src
# Dependencies first, so this layer is reused while only the code changes.
COPY pyproject.toml uv.lock ./
RUN --mount=type=secret,id=netrc,target=/root/.netrc,required=false \
    --mount=type=secret,id=ca,target=/run/secrets/ca.pem,required=false \
    if [ -s /run/secrets/ca.pem ]; then export SSL_CERT_FILE=/run/secrets/ca.pem; fi; \
    uv sync --locked --no-dev --no-install-project
COPY . .
RUN --mount=type=secret,id=netrc,target=/root/.netrc,required=false \
    --mount=type=secret,id=ca,target=/run/secrets/ca.pem,required=false \
    if [ -s /run/secrets/ca.pem ]; then export SSL_CERT_FILE=/run/secrets/ca.pem; fi; \
    uv sync --locked --no-dev --no-editable

FROM ${PYTHON_IMAGE}
# Owned by group 0 as it is copied: a later chgrp -R would store every file a second time
# in a new layer (seen with Docker: 50 MB file, 50 MB more).
COPY --from=build --chown=1001:0 /app/.venv /app/.venv
ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/tmp \
    PORT=8080
WORKDIR /app
# OpenShift runs the container as a random UID that belongs to group 0.
# A folder the process writes to at run time must be group 0 and group writable;
# only the folder, so no file is copied into a new layer.
RUN chgrp 0 /app && chmod g=u /app
# A numeric non-root user, so runAsNonRoot can be checked on plain Kubernetes too.
USER 1001
EXPOSE 8080
CMD ["python", "-m", "web"]
