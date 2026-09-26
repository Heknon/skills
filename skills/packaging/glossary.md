# Glossary

One sentence per term. Use these words and no synonyms.

| Term | Meaning |
| --- | --- |
| distribution | What is installed and published under one name, such as `acme-report`; its import name may differ (`acme_report`, `report`). |
| wheel | A built distribution (`.whl`, a zip): files copied into `site-packages` as they are, plus a `.dist-info` folder. |
| sdist | A source distribution (`.tar.gz`): the source tree a wheel is built from, with `PKG-INFO`. `uv build` makes the sdist first, then the wheel from it. |
| METADATA | The file in a wheel's `.dist-info` with the name, version, `Requires-Python`, `Requires-Dist` and extras; what installers read. |
| `Requires-Dist` | One published dependency line in METADATA, such as `acme-core<2,>=1.2`; written from `[project] dependencies`. |
| build backend | The package that turns a source tree into a wheel and sdist: hatchling, setuptools, uv_build; named in `[build-system] build-backend`. |
| build frontend | The tool that calls the backend: `uv build`, and uv whenever it installs the project. |
| build requirement | A package in `[build-system] requires`, fetched from the index at build time, not recorded in `uv.lock`. |
| src layout | The package lives in `src/<name>/`, so it cannot be imported from the checkout by accident. |
| flat layout | The package folder sits next to `pyproject.toml`. |
| namespace package | A package folder with no `__init__.py`, such as `acme/`, shared by several distributions (`acme.core`, `acme.api`). |
| package data | Files other than `.py` inside a package (templates, JSON, `py.typed`) that must be listed or included for the backend to ship them. |
| editable install | The project installed as a pointer (a `.pth` file) to the source tree; what `uv sync` does for the project. It reads the checkout, not the wheel. |
| entry point | A name mapped to `module:callable` in the wheel's `entry_points.txt`; a console script is the `[project.scripts]` kind. |
| console script | A command (`acme-report`, on Windows `acme-report.exe`) written into the environment at install time that calls the named function. |
| extra | An optional group of dependencies published with the package: `[project.optional-dependencies]`, installed as `acme-report[http]`. |
| dependency group | A named list in `[dependency-groups]` (such as `dev`) for working on the project; never published. |
| lock | `uv.lock`: every package and version for every platform, with the index or path each came from. |
| resolution | Choosing one version of every package that satisfies all requirements; uv's resolver prints why when none exists. |
| bound | A version limit in a requirement: lower (`>=1.2`), upper (`<2`), or both. |
| pin | A requirement to one version (`==1.4.0`). |
| index | A package server read by uv: the mirror, the internal index, or a local folder (`format = "flat"`). |
| mirror | The internal copy of the public index, the default index. |
| internal index | Where the team publishes its own packages, such as GitLab's PyPI registry. |
| explicit index | An index with `explicit = true`: used only for packages pinned to it in `[tool.uv.sources]`. |
| source | A `[tool.uv.sources]` entry that tells uv where one package comes from: `{ workspace = true }`, `{ path = ... }`, `{ index = ... }`. |
| dependency confusion | A public package with an internal package's name, chosen because an index strategy or a missing source let it win. |
| unit | Anything in a repository that builds, runs or deploys on its own (a project, a program with its own Dockerfile, CI job or entry point, a package with its own script inside a larger project), or shared code that other units import. |
| tie | What makes one unit depend on another: an import, a path hack, `PYTHONPATH`, a path or workspace source, a copied module, a shared requirements file or config. |
| path hack | A `sys.path.insert` or `sys.path.append` line, or a `PYTHONPATH` setting, that makes code importable only from the checkout. |
| monorepo | A repository that holds more than one unit; not a kind but a place on a spectrum from unpackaged units tied by paths to one workspace (`core/monorepo.md`). |
| workspace | A uv workspace: a root `pyproject.toml` with `[tool.uv.workspace] members`, one `uv.lock`, one `.venv`. |
| member | A project inside a workspace, with its own `pyproject.toml` and version. |
| sibling | Another member of the same workspace that a member depends on. |
| virtual root | A workspace root with no `[project]` table; `uv sync` there installs every member. |
| independent project | A project with its own `uv.lock` and `.venv`, outside any workspace, even when it sits in the same repository. |
| wheelhouse | A folder of wheels carried across the air gap and installed with `--no-index --find-links`. |
| platform tag | The part of a wheel's name that says where it runs: `win_amd64`, `manylinux_2_17_x86_64`, or `any`. |
| dynamic version | A version the backend computes at build time (`dynamic = ["version"]`), from a file or git tags. |
