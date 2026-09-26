FROM python:3.12-slim
COPY --from=registry.example.com/mirror/astral-sh/uv:0.12.19 /uv /usr/local/bin/uv
WORKDIR /app
COPY . .
RUN uv sync --locked --no-dev --no-editable --package acme-api
CMD ["/app/.venv/bin/acme-api", "quote", "1", "1"]
