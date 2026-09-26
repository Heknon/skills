# Built with the repository root as context:
#   buildah build --file services/worker/Dockerfile .
ARG UV_IMAGE=registry.example.com/mirror/astral-sh/uv:0.12-python3.12-trixie-slim
ARG PYTHON_IMAGE=registry.example.com/mirror/library/python:3.12-slim-trixie

FROM ${UV_IMAGE} AS build
ENV UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /src
COPY . .
RUN uv sync --locked

FROM ${PYTHON_IMAGE}
COPY --from=build /app/.venv /app/.venv
ENV PATH=/app/.venv/bin:$PATH
CMD ["acme-worker"]
