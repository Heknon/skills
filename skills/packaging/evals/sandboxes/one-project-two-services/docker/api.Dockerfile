FROM python:3.12-slim
COPY --from=registry.example.com/mirror/astral-sh/uv:0.12.19 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src/ src/
RUN uv sync --locked --no-dev --no-editable
CMD ["/app/.venv/bin/acme-api", "1.10", "2.20"]
