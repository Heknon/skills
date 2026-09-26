# Metadata: write or fix `pyproject.toml`

**Verdict you produce:** the changed tables, and the command that accepted
them.

```
changed:  <table.key = value>, one line each
accepted: uv lock -> "Resolved <n> packages"   (and uv build when [project] changed)
published as: <the METADATA lines that changed, from inspect_dist.py>
```

Packaging owns `[build-system]`, `[project]`, `[dependency-groups]`,
`[tool.uv]` and the backend's table. `[tool.ruff]`, `[tool.mypy]` and
`[tool.pyright]` are the linting skill's; `[tool.pytest]` is pytest's.

## The `[project]` table

Checked on hatchling 1.32.4 and setuptools 84.0.0 (METADATA read from the
built wheel):

| Key | Write | Becomes in METADATA |
| --- | --- | --- |
| `name` | `"acme-report"` | `Name: acme-report`; the wheel file is `acme_report-...` |
| `version` | `"1.2.0"`, or `dynamic = ["version"]` (`core/versioning.md`) | `Version: 1.2.0` |
| `requires-python` | `">=3.12"` | `Requires-Python: >=3.12` |
| `dependencies` | `["click>=8.1"]` | `Requires-Dist: click>=8.1` |
| `optional-dependencies` | `http = ["httpx>=0.28"]` | `Provides-Extra: http` and `Requires-Dist: httpx>=0.28; extra == 'http'` |
| `license` | an SPDX expression: `"MIT"`, `"LicenseRef-Proprietary"` | `License-Expression: LicenseRef-Proprietary` |
| `readme` | `"README.md"` | the long description |
| `scripts` | `acme-report = "acme_report.cli:main"` | `entry_points.txt` (`core/entry-points.md`) |

- `license = { text = "..." }`, the old table form, still builds on
  setuptools 84.0.0 but warns `` `project.license` as a TOML table is
  deprecated ``. Write the string form.
- `[dependency-groups]` are never published: a wheel built with a `dev`
  group has no `Requires-Dist` for it (lab). Test and lint tools go there;
  what users of the package need goes in `dependencies`; what some users
  need goes in an extra.
- `requires-python` is a floor for the lock too: uv resolves for every
  Python the range allows. In a workspace the strictest member's floor
  applies to all (`core/workspaces.md`).

## Change dependencies with uv

| To | Command (lab, uv 0.12.19) | Writes |
| --- | --- | --- |
| add | `uv add httpx` | `"httpx>=0.28.1"` (a lower bound at the newest version) |
| add with your bound | `uv add "httpx>=0.28,<1"` | the bound as written |
| add to a group | `uv add --dev pytest`, `uv add --group lint ruff` | `[dependency-groups] dev = [...]`, `lint = [...]` |
| add an extra | `uv add --optional http httpx` | `[project.optional-dependencies] http = [...]` |
| add from the internal index | `uv add --index internal "acme-report>=1.0"` | the requirement and `acme-report = { index = "internal" }` |
| remove | `uv remove httpx` | removes the line and relocks |

Each also locks and syncs. Read the diff afterwards: `uv remove` kept the
removed line's trailing comment as a line of its own, and `uv add --index`
wrote `[tool.uv.sources]` below the index tables instead of where it was
(lab).

`uv add` with `UV_DEFAULT_INDEX` set writes that URL into
`pyproject.toml` as a `[[tool.uv.index]]` with `default = true` and no
name (lab). Check the diff after `uv add`, and give the index a name
(`core/indexes.md`).

## Check it

1. `uv lock`: the resolver accepts the requirements (`Resolved <n>
   packages`). A failure is `core/dependencies.md`.
2. When `[project]` changed: `uv build` and read METADATA with
   `inspect_dist.py` (`core/build-and-inspect.md`): the published lines are
   what other projects will get.

## Never

- Never run `pip install` or `uv pip install` to add a dependency: it
  reaches no file, and the next `uv sync` removes it (lab: `- rich==15.0.0`).
- Never copy the old table forms (`license = { file = ... }`, license
  classifiers) from another project without building once to read the
  warnings.
