# hatchling

Verified on hatchling 1.32.4 (hatch-vcs 0.5.0 for versions from git),
built with uv 0.12.19. Every key below was built and the result listed
with `inspect_dist.py`. Anything else: read the installed source
(`hatchling/builders/wheel.py`, `hatchling/builders/config.py`) through the
offline-docs skill, never memory.

```toml
[build-system]
requires = ["hatchling==1.32.4"]          # add "hatch-vcs" for git versions
build-backend = "hatchling.build"
```

## Which files

**Default:** the wheel takes the folder named after the project (`-` as
`_`) from `src/` or the root. The sdist takes every file in the tree that
`.gitignore` does not exclude (lab: `tests/`, `uv.lock`, `README.md`).
**`.gitignore` applies even with no `.git` folder:** a `*.json` line left
`src/rates/data/rates.json` out of both.

When no folder matches:

```
ValueError: Unable to determine which files to ship inside the wheel using the following heuristics: https://hatch.pypa.io/latest/plugins/builder/wheel/#default-file-selection

The most likely cause of this is that there is no directory that matches the name of your project (acme_report).
```

| Need | Key (lab result) |
| --- | --- |
| the package folder has another name | `[tool.hatch.build.targets.wheel] packages = ["src/report"]` (wheel: `report/...`) |
| a namespace package | `packages = ["src/acme"]` (wheel: `acme/core/...`, no `acme/__init__.py`) |
| only some paths, with a prefix removed | `only-include = ["src/rates"]` and `sources = ["src"]` (wheel: `rates/...`) |
| ship a file `.gitignore` excludes | `[tool.hatch.build] artifacts = ["src/rates/data/*.json"]` (both sdist and wheel) |
| ship a file from outside the package | `[tool.hatch.build.targets.wheel.force-include] "extra/defaults.json" = "rates/data/defaults.json"` (included even though `.gitignore` excludes `*.json`) |
| keep files out of the sdist | `[tool.hatch.build.targets.sdist] exclude = ["tests", "CHANGELOG.md"]` |

**Where the key sits matters.** `artifacts` under
`[tool.hatch.build.targets.wheel]` only: `uv build --wheel` (from the
tree) included the file, but `uv build` (sdist, then the wheel from the
sdist) did not, because the sdist lacked it. Under `[tool.hatch.build]`
it reaches both.

**The silent mistake:** `packages = ["report"]` while the code is in
`src/report/` built a wheel of four `.dist-info` files and no error.

## Version

| Source | Configuration | Error when it cannot |
| --- | --- | --- |
| static | `[project] version = "1.2.0"` | none |
| a file | `dynamic = ["version"]`, `[tool.hatch.version] path = "src/acme/core/__init__.py"` (reads `__version__ = "..."`) | ``ValueError: Error getting the version from source `regex`: unable to parse the version from the file: src/acme/core/__init__.py`` |
| git tags | `requires = ["hatchling", "hatch-vcs"]`, `dynamic = ["version"]`, `[tool.hatch.version] source = "vcs"` | no `.git`: ``LookupError: Error getting the version from source `vcs`: setuptools-scm was unable to detect version for <path>.`` |

hatch-vcs 0.5.0 requires setuptools-scm, and setuptools-scm 10.3.4
requires vcs-versioning (2.5.0 in the lab), packaging and setuptools (read
from their METADATA): all must be on the mirror for a build. Versions it
produces: `core/versioning.md`.

## Editable installs

`uv sync` installs the project editable. hatchling then asks for
`editables~=0.3` as an extra build requirement: without it on the mirror,
`uv sync` failed with `Because editables was not found in the package
registry and you require editables>=0.3,<1.dev0` while `uv build` worked.
The editable install is a `_editable_impl_<name>.pth` file pointing at the
source folder.

## Messages and meanings

| Message or sign | Meaning |
| --- | --- |
| `Unable to determine which files to ship inside the wheel` | no folder matches the name: set `packages` |
| wheel with only `.dist-info` files | `packages` names a folder that does not exist |
| a data file in the checkout, not in the wheel | `.gitignore` excludes it, or `packages`/`only-include` leave it out |
| `Generator: hatchling 1.32.4` in `WHEEL` | the backend version that built it (`inspect_dist.py`: `built by:`) |
