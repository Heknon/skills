# Orient: how is this project packaged?

**Verdict you produce:** six lines, each with the file and line that shows
it. Read only; nothing is built or changed.

```
kind:     <single project | uv workspace (members) | independent projects | other tool>
backend:  <build-backend> from <requires>        (pyproject.toml:<line>)
layout:   <src | flat | namespace>, import name <name>, folder <path>
version:  <static "x.y.z" | dynamic: <source>>   (pyproject.toml:<line>)
indexes:  <name, url, default/explicit> per index, or "none: uv's default (PyPI)"
lock:     <uv.lock at <path>, registries in it> | <no lock>
```

## Steps

1. **Find every `pyproject.toml`** and any `uv.lock` that git tracks:
   `git ls-files "*pyproject.toml"` and `git ls-files "*uv.lock"` (the
   same in PowerShell and a POSIX shell; they skip `.venv`). More than one
   `pyproject.toml` means a monorepo: `core/monorepo.md` decides its kind.
2. **The backend.** Read `[build-system]`:

   | `build-backend` | Backend | Facts |
   | --- | --- | --- |
   | `hatchling.build` | hatchling | `backends/hatchling.md` |
   | `setuptools.build_meta` | setuptools | `backends/setuptools.md` |
   | `uv_build` | uv's own | `backends/uv-build.md` |
   | `poetry.core.masonry.api`, `pdm.backend`, `flit_core.buildapi` | poetry-core, pdm-backend, flit-core | `backends/others.md`: read, never migrate unasked |
   | no `[build-system]` | not a package: uv installs only its dependencies | `core/metadata.md` |

   `[tool.uv] package = false` also means "not built": `uv sync` installs
   the dependencies and not the project (`source = { virtual = "." }` in
   the lock).
3. **The layout.** A `src/` folder holding the package is src layout; a
   package folder beside `pyproject.toml` is flat; a folder with no
   `__init__.py` over the package (`src/acme/core/`) is a namespace. Note
   whether the folder name is the project name with `-` as `_`: if not,
   the backend must be told (`core/layout.md`).
4. **The version.** `version = "..."` in `[project]` is static.
   `dynamic = ["version"]` means the backend computes it: from a file
   (`[tool.hatch.version] path`, `[tool.setuptools.dynamic] version`) or
   from git tags (`source = "vcs"`, `[tool.setuptools_scm]`). `uv version`
   on a dynamic project fails: `We cannot get or set dynamic project
   versions in: pyproject.toml`.
5. **The indexes.** Every `[[tool.uv.index]]` table, which one has
   `default = true`, which have `explicit = true`, and the
   `[tool.uv.sources]` lines that name them (`core/indexes.md`). No table
   means uv's default, PyPI, unless the environment sets one
   (`UV_DEFAULT_INDEX`, a user `uv.toml`: `uv/config.md`).
6. **The lock.** `Select-String -Path uv.lock -Pattern 'registry = '`
   shows which indexes the packages came from (`uv/lockfile.md`). A line
   with `https://pypi.org/simple` in an air-gapped team is a finding.
7. **What would change it.** Only if asked: `uv build` to see the files
   (`core/build-and-inspect.md`), `uv lock --check` to see whether the lock
   matches (it resolves, so it needs the index).

## Never

- Never run `uv sync`, `uv lock` or `uv add` to "have a look": each can
  change the lock or the environment. Orient reads files.
- Never guess the backend from habit: the `build-backend` line decides,
  and a project can carry tables for a backend it no longer uses.
