# Plan: the packaging skill

Status: draft for decision. Nothing is built yet.

## 1. What it is

Turning Python code into something another machine can install, and
installing other people's packages safely: `pyproject.toml` (PEP 621
metadata, dependencies, extras, dependency groups), build backends and
how to tell which one a project uses, src and flat layouts, package
data, editable installs, entry points, wheels and sdists and what is in
them, versions (static or from git tags), uv workspaces, lockfiles and
conflicts, internal indexes, wheelhouses across the air gap, and
publishing to an internal index.

Like the other skills: knowledge and judgement, not enforcement;
procedures that end in a verdict; facts stamped with a version; recipes
that were built and installed; evals written first.

## 2. The environment it is written for

- **A weak model in Zed on Windows, PowerShell, no web.** Every key and
  flag is in the skill with its version; the next sources are `uv help`
  and the backend's installed source (offline-docs owns reading those).
- **uv, packages only from the internal mirror, no PyPI.** `uv build`
  fetches the backend from the index too, so a backend missing from the
  mirror fails the build (message: to verify in the lab).
- **Credentials for the internal index** come from
  `UV_INDEX_<NAME>_USERNAME` and `_PASSWORD`, a netrc file or `uv auth
  login`; never from `pyproject.toml`, `uv.lock` or a URL in the
  repository. Where `uv auth` stores them on Windows: to verify.
- **An internal CA and Windows paths.** uv 0.12.19 warns that
  `UV_NATIVE_TLS` is deprecated for `UV_SYSTEM_CERTS`; which of that,
  `--cert` and `SSL_CERT_FILE` works here is to verify. Scripts are
  `.exe` shims in `.venv\Scripts\`.
- **Publishing is outward facing.** Nothing is uploaded unasked, and an
  upload cannot be taken back: a version cannot be uploaded twice.

## 3. The kinds of task

| Kind | Asked to | Answer shape |
| --- | --- | --- |
| **Orient** | explain how this project is packaged | backend, layout, version source, index, lock, each with the line that shows it |
| **Metadata** | write or fix `pyproject.toml`: name, Python range, dependencies, extras, groups | the file, and `uv lock` or `uv build` output |
| **Layout** | move to src layout, add a subpackage, ship data files | the tree, and the wheel listing that proves the files are in |
| **Entry point** | add or fix a console script | the `[project.scripts]` line, and the script run from a clean venv |
| **Build** | build a wheel or sdist and say what is in it | file names, and the listing with what is missing or extra |
| **Version** | bump, or derive from git tags | the version the built wheel carries, not the one intended |
| **Dependencies** | add, pin, upgrade, or resolve a conflict | the resolver's error read, the one constraint changed, the new lock |
| **Workspace** | set up or fix a uv workspace or monorepo | members, sources, `uv lock` and `uv sync --package` output |
| **Index** | configure the mirror and internal indexes | the `[[tool.uv.index]]` tables, and the index each package came from |
| **Across the gap** | bring packages in, or build a wheelhouse | the export, the download for the connected side, an offline install that passed |
| **Publish** | prepare or publish a release to the internal index | version, files, target URL, a dry run; the upload only when asked |
| **Debug** | an install, import, build or resolution fails | the failing step, its message, the cause, the fix, the check |

## 4. The failures it targets

| Failure | What it looks like |
| --- | --- |
| **src layout misconfigured** | the wheel builds but holds no package, or the wrong one; `ModuleNotFoundError` after install while tests in the repository pass |
| **Missing files in the wheel** | templates, JSON or `py.typed` absent; works from the checkout, fails once installed |
| **Editable hides the bug** | "ready to release" because `uv run pytest` passes, when the editable install reads the source tree and no wheel was built |
| **Unpin everything** | a conflict "fixed" by deleting every bound, or by `--frozen`, instead of reading which two requirements clash |
| **`pip install` outside uv** | installs into another interpreter or reaches for pypi.org; `uv.lock` never learns of it |
| **Wrong callable** | `[project.scripts]` names a module, a factory instead of the click group, or a function that needs arguments |
| **Accidental public publish** | `uv publish` with no URL, whose default is PyPI's upload URL (`uv help publish`, 0.12.19) |
| **Dependency confusion** | an internal name also on the mirror; `unsafe-best-match` or an extra index lets the higher public version win |
| **Lock from another world** | `uv.lock` records `https://pypi.org/simple` because it was made on a connected laptop |
| **Version from memory** | the tag says 1.4.0, the wheel says `0.1.dev1` because CI cloned without tags |
| **Wrong-platform wheelhouse** | Linux wheels fetched for a Windows target, or sdists that need a compiler |
| **Backend from memory** | a hatchling key in a setuptools project; setuptools' package data syntax invented |

## 5. Layout

```
skills/packaging/
  SKILL.md        router over the twelve kinds, invariants, answer shape
  glossary.md     wheel, sdist, backend, frontend, editable, extra, group
  core/           one procedure per kind (orient, metadata, layout,
                  entry-points, build-and-inspect, versioning,
                  dependencies, workspaces, indexes, across-the-gap,
                  publish, debug) and verify.md: the wheel in a clean
                  venv, offline, imported and its scripts run
  backends/       hatchling, setuptools, uv-build; others.md recognises
                  poetry-core, pdm-backend, flit-core (read only)
  uv/             commands, config (variables, credentials, CA),
                  lockfile (reading uv.lock), versions
  recipes/        built, installed and run: src-hatchling,
                  flat-setuptools, uv-build, workspace, internal-index,
                  wheelhouse; tools/inspect_dist.py lists a wheel's or
                  sdist's files, METADATA and entry points (stdlib only)
  examples/       a data file lost in the wheel; a conflict; a release
  evals/          evals.json and sandboxes
```

## 6. Dependencies and boundaries

| Skill | Needs | Relies on by name | Existing skills it touches |
| --- | --- | --- | --- |
| packaging | none | offline-docs | deployment (uv, mirrors, images) |

| Ground | Owner | The other side |
| --- | --- | --- |
| building and publishing Python distributions | packaging | deployment owns container images and Helm charts; both use the same internal mirror |

- **Needs none** (wave 1). **offline-docs by name**: what an installed
  package offers is its question; packaging inspects distributions it
  built or is about to install.
- **The line with deployment.** Deployment's `gitlab/python.md` has a
  default `[[tool.uv.index]]`, the credential variables, the CA, and a
  CI job that runs `uv build` and `uv publish` with the job token.
  Deployment keeps what runs in CI or an image: jobs, the job token,
  CI/CD variables holding credentials, `uv sync` in a Dockerfile.
  Packaging owns what is built and why: `pyproject.toml`, the backend,
  the wheel's contents and version, index semantics (default, explicit,
  strategy, sources), `uv.lock`, wheelhouses, and cutting a release. It
  writes no CI jobs; it points at deployment's publish component.

### Proposed changes to the roadmap

1. Add **pytest** and **navigation** to "touches". pytest owns import
   errors under pytest (rootdir, import mode); packaging owns "does not
   import once installed", shown by the wheel in a clean venv.
   navigation reads entry points; packaging declares and fixes them.
2. A row for **`pyproject.toml`**: packaging owns `[build-system]`,
   `[project]`, `[dependency-groups]`, `[tool.uv]` and backend tables;
   linting owns `[tool.ruff]`, `[tool.mypy]`, `[tool.pyright]`; pytest
   owns `[tool.pytest]`.
3. A row for **`[[tool.uv.index]]`**: packaging owns its meaning;
   deployment's `gitlab/python.md` keeps its CI facts and points here.
4. Notes: git owns bundles, packaging wheelhouses; git makes tags,
   packaging turns them into a version, deployment's clone depth
   decides whether CI sees them.

## 7. How it will be verified

Pinned (the latest on the index while writing this): uv and uv_build
0.12.19 (deployment's uv), Python 3.12 (as deployment and pytest),
hatchling 1.32.4, hatch-vcs 0.5.0, setuptools 84.0.0, setuptools-scm
10.3.4, and pip 26.2.1 for the connected side of a wheelhouse only.

- **No network during checks.** A flat folder of wheels stands in for
  the mirror, GitLab CE 19.4.1's PyPI registry (deployment's lab) for
  the internal index; the network is cut (how: to verify).
- **Every recipe:** `uv build` (the sdist, then the wheel from it); list
  both with `inspect_dist.py` against the source tree; install the wheel
  in a clean venv with `--no-index --find-links dist`; import from
  outside the checkout; run each console script.
- **Every fact** in `uv/` and `backends/` is run and its error copied
  verbatim; a wheelhouse is downloaded for `win_amd64` and installed
  offline. Windows itself: see PK8.

Seen while writing this: uv 0.12.19 has no `uv pip download`, so the
connected side uses `uv export` then `pip download`; `uv lock` accepts
a `format = "flat"` default index beside an `explicit` one with a
`publish-url`. Whether a flat index replaces `--find-links`: to verify.

## 8. Evals, written first

Sandboxes in `evals/sandboxes/`, each baiting one failure; each bait is
reproduced in the lab first, and each intended fix passes section 7.

| Sandbox | Task given | The bait |
| --- | --- | --- |
| `src-empty-wheel` | "the CLI fails after install, fix it" | hatchling finds no package under `src/`; the fix is not `sys.path` |
| `lost-template` | "installed, it cannot find `report.html`" | setuptools without package data; editable works |
| `editable-green` | "tests pass, is 2.0 ready to publish?" | only an editable install was ever tested |
| `conflict` | "`uv lock` fails, make it work" | two bounds clash; unpinning all looks like a fix |
| `pip-habit` | "add `httpx` to this project" | `pip install httpx` |
| `wrong-script` | "`acme` prints nothing" | the script names a module, not its `main` |
| `publish-default` | "publish 1.3.0" | `uv publish` with no URL; right: dry run, stop and ask |
| `confusion` | "why did we get a different `acme-utils`?" | an extra index with `unsafe-best-match`; the mirror has a higher version |
| `pypi-lock` | "CI fails at `uv sync --locked`" | a lock made against pypi.org |
| `shallow-tag` | "the wheel says `0.1.dev1`, the tag is 1.4.0" | hatch-vcs in a clone without tags |
| `linux-wheelhouse` | "the offline install on Windows fails" | a wheelhouse downloaded for Linux |
| `workspace-sibling` | "member `api` cannot find `core`" | a sibling listed with no workspace source |
## 9. Decisions needed

### PK1. Backend and layout for a new project

*Recommended:* hatchling with src layout. Deployment's recipes use
hatchling; src layout makes tests run against the installed package.
uv_build is documented for pure-Python projects, setuptools for
existing ones; a flat project is fixed, not converted unasked.

### PK2. Poetry, PDM and flit projects

*Recommended:* recognised and read (their backend and version), never
migrated unasked.

### PK3. Where the version comes from

*Recommended:* static, bumped with `uv version --bump`, checked against
the tag before publishing: no plugin in the mirror, no tags in the
clone. Dynamic versions are documented for projects that use them.

### PK4. The mirror and the internal index

What is the mirror (Nexus, Artifactory, devpi, a folder)? Are internal
packages on it, or only in GitLab's registry? *Recommended:* the mirror
as the one `default = true` index; internal packages from an index
marked `explicit = true` and named per package in `[tool.uv.sources]`;
no `unsafe-*` index strategy.

### PK5. Who crosses the gap

*Recommended:* the model works on the air-gapped side only; for the
other side it writes a script for a person (export, then `pip download`
with platform and Python version), and proves the result offline.

### PK6. Publishing from a workstation

*Recommended:* releases go through deployment's CI component on a tag.
The skill prepares the release and runs `uv publish --dry-run`; a manual
upload happens only when the person asks for it.

### PK7. Compiled extensions

*Recommended:* out of scope; the skill recognises a project that needs a
compiler (C sources, `ext_modules`, a Rust backend) and says so.

### PK8. A Windows machine for the lab

*Recommended:* use one for PowerShell, script shims and credential
storage; otherwise those lines are marked *not run on Windows*.
