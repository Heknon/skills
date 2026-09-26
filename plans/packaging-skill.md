# Plan: the packaging skill

Status: built in `skills/packaging/`. The recommended answers in
section 9 were taken as defaults so the skill could be built (section
10); each can be changed.

## 1. What it is

Turning Python code into something another machine can install, and
installing other people's packages safely: `pyproject.toml` (PEP 621
metadata, dependencies, extras, dependency groups), build backends and
how to tell which one a project uses, src and flat layouts, package
data, editable installs, entry points, wheels and sdists and what is in
them, versions (static or from git tags), monorepos (uv workspaces,
independent projects side by side, path dependencies), lockfiles and
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
| **Monorepo** | say how a repository of many packages is organised, or choose how it should be | its kind (workspace, independent projects, path dependencies), each member with its role, and whether one lock fits |
| **Workspace** | set up or fix a uv workspace: add, move or split a member | members, sources, bounds on siblings, `uv lock` and `uv sync --package` output |
| **Member release** | build, version or publish one member | the member's wheel, its `Requires-Dist` on siblings, the tag, dependents checked |
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
| **One lock for incompatible members** | two services that need different versions of a library forced into one workspace; the lock "fixed" by loosening the older service's bound |
| **Unbounded sibling** | `dependencies = ["core"]` in a member; its published wheel says `Requires-Dist: core` and accepts any `core` ever released |
| **Sibling without a source** | a member depends on a sibling with no `{ workspace = true }` entry; the model adds an index or a path instead |
| **Whole workspace installed** | `uv sync` at the root in a Dockerfile or job that needs one member; a member's lock expected in its own folder |
| **Library bumped alone** | `core` goes to 2.0 while `api` still says `core<2`; nobody checks the dependents |

## 5. Layout

```
skills/packaging/
  SKILL.md        router over the fourteen kinds, invariants, answer shape
  glossary.md     wheel, sdist, backend, frontend, editable, extra, group
  core/           one procedure per kind (orient, metadata, layout,
                  entry-points, build-and-inspect, versioning,
                  dependencies, monorepo (kinds, when one lock fits),
                  workspaces, member-release, indexes, across-the-gap,
                  publish, debug) and verify.md: the wheel in a clean
                  venv, offline, imported and its scripts run
  backends/       hatchling, setuptools, uv-build; others.md recognises
                  poetry-core, pdm-backend, flit-core (read only)
  uv/             commands, config (variables, credentials, CA),
                  lockfile (reading uv.lock), versions
  recipes/        built, installed and run: src-hatchling,
                  flat-setuptools, uv-build, workspace (libraries and
                  services, bounded siblings), independent-projects,
                  internal-index,
                  wheelhouse; tools/inspect_dist.py lists a wheel's or
                  sdist's files, METADATA and entry points (stdlib only)
  examples/       a data file lost in the wheel; a conflict; a release
  evals/          evals.json and sandboxes
```

## 5a. Monorepos

A monorepo is one repository holding many Python packages. The skill
recognises which kind it is before changing anything:

| Kind | Sign | One lock? |
| --- | --- | --- |
| uv workspace | `[tool.uv.workspace] members` in the root `pyproject.toml`; one `uv.lock` at the root | yes, for every member |
| independent projects | a `pyproject.toml` and a `uv.lock` per folder, no workspace table | no; each resolves alone |
| path dependencies | `{ path = "../core", editable = true }` in `[tool.uv.sources]`, no workspace | one per project |
| other tools | `pants.toml`, `BUILD` files, Poetry or Hatch workspaces | recognised, never migrated unasked |

Checked while planning on uv 0.8.17 (to recheck on the pinned 0.12.19):

- **One lock means one version of everything.** Members that need
  incompatible versions of a library make the workspace unsatisfiable
  ("your workspace's requirements are unsatisfiable"). The lock's
  `requires-python` is the strictest member's: one member needing 3.12
  raises the floor for all. A workspace fits members that are
  developed and upgraded together; services that must move at their own
  pace are independent projects.
- **A sibling needs a source.** Without `core = { workspace = true }`,
  `uv lock` stops with "`core` is included as a workspace member, but is
  missing an entry in `tool.uv.sources`".
- **The declared requirement is what a wheel publishes.** A member that
  lists a sibling as bare `core` builds a wheel with
  `Requires-Dist: core`, which accepts any release; listing
  `core>=1.2,<2` gives `Requires-Dist: core<2,>=1.2`. In development the
  workspace source still wins; only the published metadata changes.
- **Commands.** `uv lock` from any member's folder writes the root lock
  (no lock appears in the member). `uv sync --package api` installs
  `api` and the siblings it needs, nothing else. `uv build --package api`
  builds that member's wheel and sdist. `uv lock --locked` fails when the
  lock is stale.

**Layout, with no precedent.** A root `pyproject.toml` holding the
workspace table and the shared development tools as a dependency group;
libraries under `packages/`, deployable services under `services/`, each
a src-layout project with its own version. Shared namespaces (`acme.core`,
`acme.api`) are implicit namespace packages with no `__init__.py` in
`acme/`; how each backend is told so is to verify in the lab.

**Versions and releases.** Each member has its own version, bumped when
it changes; a library's major bump means reading every dependent's bound
first (`grep` for the library in each member's `pyproject.toml`). Tags
name the member (`core-v1.2.0`); git owns the tag, deployment the CI
that builds only what changed.

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
| `wrong-script` | "`acme hello` prints `<Group cli>`" | the script names a factory, not its `main` (built: a module-only script fails at install) |
| `publish-default` | "publish 1.3.0" | `uv publish` with no URL; right: dry run, stop and ask |
| `confusion` | "why did we get a different `acme-utils`?" | an extra index with `unsafe-best-match`; the mirror has a higher version |
| `pypi-lock` | "CI fails at `uv sync --locked`" | a lock made against pypi.org |
| `shallow-tag` | "the wheel says `0.1.dev1`, the tag is 1.4.0" | hatch-vcs in a clone without tags |
| `linux-wheelhouse` | "the offline install on Windows fails" | a wheelhouse downloaded for Linux |
| `workspace-sibling` | "member `api` cannot find `core`" | a sibling listed with no workspace source |
| `workspace-conflict` | "`uv lock` fails since `billing` needs `pydantic<2`" (built with pydantic; the draft said pandas) | one lock over services that must differ; loosening `billing` looks like the fix |
| `unbounded-sibling` | "publish `api` 0.4.0" | `api` lists bare `core`; its wheel would accept any `core` |
| `one-member` | "install only the worker for its image" | `uv sync` at the root installs every member |
| `library-major` | "release `core` 2.0" | two members still say `core<2`; nobody reads them |

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

### PK9. Monorepo default

*Recommended:* one uv workspace for members developed and upgraded
together; independent projects for services that need different versions
of a shared library or of Python; every sibling requirement bounded.
*Decided:* "monorepo" is not a label the skill needs in advance. It
reads the repository for logical units (anything that builds, runs or
deploys on its own) and the ties between them (imports, path hacks,
`PYTHONPATH`, path dependencies, copies, a workspace), places the repo
on that spectrum, and improves it one step at a time. It asks the
person only what the evidence cannot decide, once, with the default it
will take (`core/monorepo.md`).

## 10. Decisions taken as defaults

Each *Recommended* answer in section 9 was taken, as the pytest plan did:

- **PK1.** hatchling with src layout for new projects (`recipes/src-hatchling/`);
  uv_build documented for pure-Python projects (`recipes/uv-build/`),
  setuptools for existing ones (`recipes/flat-setuptools/`); flat projects
  are fixed, not converted.
- **PK2.** poetry-core, pdm-backend and flit-core are recognised and read
  (`backends/others.md`), never migrated unasked.
- **PK3.** A static version bumped with `uv version --bump`, checked
  against the tag; hatch-vcs and setuptools-scm documented for projects
  that use them.
- **PK4.** The mirror as the one `default = true` index; internal packages
  from an `explicit = true` index named per package in
  `[tool.uv.sources]`; no `unsafe-*` strategy.
- **PK5.** The model works on the air-gapped side and writes
  `fetch-wheels.sh` for a person on the connected side; the wheelhouse is
  checked for the target platform before it crosses.
- **PK6.** Releases go through deployment's CI component on a tag; the
  skill prepares, runs `uv publish --index <name> --dry-run`, and uploads
  only when asked.
- **PK7.** Compiled extensions are out of scope and recognised
  (`backends/others.md`, `core/build-and-inspect.md`).
- **PK8.** No Windows machine was available. PowerShell 7.5.3 for Linux
  ran the PowerShell forms (`Select-String`, `$env:`, `Push-Location`,
  `git grep`); Windows paths, `.exe` shims, `%APPDATA%` and the credential
  store are marked *not run on Windows*.
- **PK9.** One workspace for members developed together; independent
  projects for services that need other versions; every sibling bounded.

## 11. How it was verified

- **Versions.** uv and uv_build 0.12.19 (installed with pip into a scratch
  venv; the system uv 0.8.17 was used only for `uv/versions.md`), Python
  3.12.3, hatchling 1.32.4, hatch-vcs 0.5.0, setuptools 84.0.0,
  setuptools-scm 10.3.4 (with vcs-versioning 2.5.0), pip 26.2.1;
  poetry-core 2.5.0, pdm-backend 2.4.10 and flit-core 4.1.0 once each for
  `backends/others.md`.
- **The mirror** was a folder of wheels downloaded with pip, turned into
  a PEP 503 simple index and served with `python -m http.server` on
  loopback. **The internal index** was pypiserver 2.4.2 with basic
  authentication, standing in for GitLab's PyPI registry (deployment's
  lab already covers GitLab itself). **Flat indexes** (`format =
  "flat"`, local folders) carried the dependency-confusion case. **An
  HTTPS index** signed by a private CA made with openssl tested the CA
  settings.
- **The network was cut** with `unshare -rn` (a namespace with only
  loopback, the mirror served inside it) for every offline claim: the
  lock from pypi.org, the wheelhouse, the recipes' clean-venv installs,
  and `uv publish` with no URL (so nothing could reach PyPI).
- **Every recipe** was locked, tested, built (sdist then wheel), listed
  with `inspect_dist.py --against` (both files), installed by its path
  into a fresh venv with `--offline`, imported from outside the checkout,
  and its console script run (`recipes/README.md` has the output).
- **Every eval bait** in `evals/evals.json` was reproduced in a fresh copy
  of its sandbox, and every intended fix was applied and checked the same
  way; 16 scenarios.
- **Publishing** went only to the local pypiserver: dry runs, uploads, a
  409 on a repeated upload, and `--check-url`/`--index` skipping existing
  files.

## 12. What the lab changed

Findings that corrected this plan or a common belief, each now in the
skill:

- **uv's workspace lock ignores the version bound on a workspace or path
  source.** With acme-core bumped to 2.0.0 and members requiring
  `acme-core>=1.2,<2`, `uv lock` passed and `uv sync` installed 2.0.0;
  the lock records the requirement with no specifier. Same on 0.8.17. The
  plan's "the workspace source still wins" understated it: a library
  bumped past its dependents is caught only by building the wheels and
  resolving them together (`core/member-release.md`, eval
  `library-major`).
- **`uv add <sibling>` writes a bare requirement** (and `--bounds major`
  too), so the unbounded sibling is uv's default, not a typo.
- **`uv publish --dry-run` with no URL is not offline on 0.12.19:** it
  tries to fetch a trusted publishing token from `upload.pypi.org`.
  0.8.17 did not. The skill never runs `uv publish` without `--index` or
  `--publish-url`.
- **A rebuilt wheel of the same version can be stale when installed by
  name.** `uv pip install --find-links dist <name>` took the earlier build
  from uv's cache; installing by path, or `--refresh-package`, took the
  new one. The verify procedure installs by path.
- **hatchling honours `.gitignore` with no `.git` folder,** so a `*.json`
  line silently drops package data; `artifacts` set on the wheel target
  alone did not help because `uv build` builds the wheel from the sdist.
  `force-include` fixes the wheel but not the editable install.
- **`packages = ["report"]` for code in `src/report/`** builds a wheel
  with no package and no error; setuptools' flat layout silently skips
  packages named `tools`, `utils`, `scripts` and more.
- **uv refuses a module-only console script** (`invalid console script:
  'acme.cli'`) at install, while hatchling builds it. A factory as the
  target prints the returned object and exits 1: the plan's "prints
  nothing" became `<Group cli>` in the eval.
- **A mirror needs more than the backend:** `editables` for hatchling
  editable installs (`uv sync` failed without it), setuptools for
  hatch-vcs (through setuptools-scm), and Windows-only dependencies such
  as colorama, because the lock is universal.
- **uv_build is built into uv:** `uv build` and `uv sync` worked with no
  uv_build on the mirror (only `--force-pep517` or pip need it); unknown
  keys in `[tool.uv.build-backend]` are ignored silently, as are unknown
  keys inside a `[[tool.uv.index]]` table (`explicitt = true`).
- **`UV_DEFAULT_INDEX` leaks into `pyproject.toml`:** `uv add` wrote it as
  an unnamed default index.
- **`uv sync` cannot install a registry lock from a wheelhouse;** the
  offline path is `uv pip install --no-index --find-links` from the
  exported requirements. `uv pip compile --python-platform` checks a
  wheelhouse for Windows from Linux.
- **CA:** `SSL_CERT_FILE` worked; `UV_SYSTEM_CERTS` did not help with a
  CA outside the system store; `UV_NATIVE_TLS` still works but warns;
  `--cert` exists only on `uv pip install`.
- **Credentials:** `UV_INDEX_<NAME>_*` served both reading and `uv publish
  --index`; `uv auth login` stored the password in plain text
  (`~/.local/share/uv/credentials/credentials.toml` on Linux); credentials
  in an index URL are stripped from `uv.lock` but stay in
  `pyproject.toml`.
- **Removing `unsafe-best-match` alone left the confused version in the
  lock;** `--upgrade-package` (or the source pin) moved it.
- **New on 0.12.19:** `uv workspace list/dir`, `uv build --clear`; the
  package-conflicts setting can lock incompatible members together but is
  experimental and breaks `uv sync` at a virtual root. The skill offers it
  only as the person's choice.
- **Eval changes:** `workspace-conflict` uses pydantic 1 against pydantic
  2 instead of pandas, a pair whose both sides the lab mirror carried for
  Python 3.12; `wrong-script` baits a factory (`<Group cli>`) because a
  module-only script fails at install instead of printing nothing.

### Resolved "to verify" items from sections 2 and 7

- A backend missing from the mirror: ``Failed to resolve requirements from
  `build-system.requires` `` ... `Because hatchling was not found in the
  package registry`.
- `uv auth` stores credentials in `uv auth dir` (Linux:
  `~/.local/share/uv/credentials`); the Windows place was not run.
- A flat index (`format = "flat"`) works as a named index, local folders
  included; `--find-links` remains the tool for wheelhouses with `uv pip`.
- How each backend is told about namespace packages: hatchling
  `packages = ["src/acme"]`, uv_build `module-name = "acme.core"`,
  setuptools finds them unaided.
