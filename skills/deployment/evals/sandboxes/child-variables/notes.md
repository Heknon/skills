Group variables of shop (Settings > CI/CD > Variables):

| Key | Value | Protected | Scope |
| --- | --- | --- | --- |
| PYTHON_IMAGE | registry.example.com/mirror/astral-sh/uv:0.12-python3.12-trixie-slim | no | * |

We moved to uv 0.12 last week by changing the group variable. The api-test
job log still says:

    Using docker image ... for registry.example.com/mirror/astral-sh/uv:0.11-python3.12-bookworm-slim
