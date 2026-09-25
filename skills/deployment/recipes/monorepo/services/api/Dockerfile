# Recipe: image of one member of a uv workspace. Built with the workspace root
# as context, since the member imports the workspace's libraries:
#   buildah build --file services/api/Dockerfile .
# Change: the package name in both uv sync lines and in CMD.
ARG UV_IMAGE=registry.example.com/mirror/astral-sh/uv:0.12-python3.12-trixie-slim
ARG PYTHON_IMAGE=registry.example.com/mirror/library/python:3.12-slim-trixie

FROM ${UV_IMAGE} AS build
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /src
# The whole workspace: uv checks the lock against every member's pyproject.toml.
COPY . .
RUN --mount=type=secret,id=netrc,target=/root/.netrc,required=false \
    --mount=type=secret,id=ca,target=/run/secrets/ca.pem,required=false \
    if [ -s /run/secrets/ca.pem ]; then export SSL_CERT_FILE=/run/secrets/ca.pem; fi; \
    uv sync --locked --no-dev --no-editable --package api

FROM ${PYTHON_IMAGE}
COPY --from=build /app/.venv /app/.venv
ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/tmp
WORKDIR /app
RUN chgrp -R 0 /app && chmod -R g=u /app
USER 1001
CMD ["python", "-m", "api"]
