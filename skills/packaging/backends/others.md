# Other backends: recognise, read, never migrate unasked

Each was built once in the lab with uv 0.12.19 (poetry-core 2.5.0,
pdm-backend 2.4.10, flit-core 4.1.0) to confirm the backend string, where
the version comes from, and what METADATA says. Changing a project to
another backend is a migration: do it only when asked.

| `build-backend` | Backend | Version from | Dependencies from |
| --- | --- | --- | --- |
| `poetry.core.masonry.api` | poetry-core | `[project] version`, or `[tool.poetry] version` in older projects | `[project] dependencies`, or `[tool.poetry.dependencies]` |
| `pdm.backend` | pdm-backend | `[project] version`, or `dynamic = ["version"]` with `[tool.pdm.version] source = "file"`, `path = "src/acme_pd/__init__.py"` | `[project] dependencies` |
| `flit_core.buildapi` | flit-core | `dynamic = ["version", "description"]`: `__version__` and the docstring of the module (`[tool.flit.module] name = "acme_fl"`) | `[project] dependencies` |

## Poetry projects

Two shapes:

- **`[project]` table present** (poetry-core 2): uv reads it like any
  project. Lab: `Requires-Dist: click (>=8.1)`.
- **Only `[tool.poetry]`** (older projects): uv sees no project.
  `uv version` fails with ``No `project` table found in: <path>``, and
  `uv lock` "succeeded" with nothing in it (`warning: No requires-python
  value found in the workspace`, `Resolved in 1ms`): the dependencies in
  `[tool.poetry.dependencies]` are invisible to uv. The build still works:
  `click = "^8.1"` became `Requires-Dist: click (>=8.1,<9.0)`.

So in a `[tool.poetry]`-only project, do not use `uv lock`, `uv add` or
`uv sync` as if they managed it. Say what the project uses, and ask
before converting it.

## Recognising other signs

| Sign | Means |
| --- | --- |
| `poetry.lock` | Poetry resolves this project; `uv.lock` beside it is a second truth |
| `pdm.lock` | PDM resolves it |
| `[tool.poetry.group.dev.dependencies]` | Poetry's dependency groups, not `[dependency-groups]` |
| `setup.py` with `ext_modules`, `.c`/`.pyx` files, `build-backend = "maturin"` or `"scikit_build_core.build"` | compiled code: out of this skill's scope; say so |

For anything these backends do beyond the table, read their installed
source through the offline-docs skill (`poetry/core/masonry/api.py`,
`pdm/backend/__init__.py`, `flit_core/buildapi.py` hold the entry points).
