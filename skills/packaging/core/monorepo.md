# Monorepo: read the repository and say where it sits

"Monorepo" is not a kind a repository either is or is not. A repository
holds one or more units, tied to each other in some ways; this procedure
finds them from the files and places them on a spectrum. It never starts
from the person's word: "this is a monorepo" is a request to look, and a
repository nobody calls a monorepo can hold three services.

**Verdict you produce:**

```
units:
  <folder>  <service | job | library | unknown>  signs: <pyproject, Dockerfile, script, CI job ...>
            sits: <unpackaged | in one project with <units> | own project, own lock | workspace member>
            ties: <imports <unit> (file:line) | sys.path (file:line) | PYTHONPATH (file:line)
                   | copy of <file> | path dependency on <unit> | reads <shared file>>
spectrum:   <one project with folders | unpackaged units tied by paths | one project, several
             deployables | projects with their own locks | one uv workspace | mixed: <each part>>
lock:       <none | <requirements file> shared by <units> | uv.lock at <root> | one per project: <paths>>
one lock fits: <yes, because <units> share <library> | no: <package> needs <a> in <x> and <b> in <y>>
problems:   <each, with file:line: path hack, PYTHONPATH, copy, no lock, lock that does not fit,
             unbounded sibling, everything installed everywhere>
questions:  <each question from the list below, with its evidence and default | none>
```

The deployment skill owns building only what changed, one member per
image, and every Dockerfile and CI file; linting owns hooks per member;
this skill owns the rest.

## Steps

1. **Map.** Run `recipes/tools/map_units.py` from the root, then confirm
   each finding with its search in `core/units-and-ties.md`.
2. **Name each unit and its role.** A *service* is deployed (its own
   Dockerfile or deploy job); a *job* runs on its own but is not a
   deployed service (a script or main guard, a CI job that runs it); a
   *library* has no entry point and other units import it; *unknown*
   has code, no sign and no importer.
3. **Write each unit's ties** with file:line.
4. **Place each unit, then the repository,** with the table below.
5. **Decide whether one lock fits** (the section after it).
6. **Name the problems** with the words in the verdict, each with its
   evidence line.
7. **Collect the questions** the evidence cannot answer (last section).
   Everything else you decide.
8. **Give the verdict.** Asked to improve it: `core/monorepo-better.md`.
   One project with folders: there is nothing to split; `core/layout.md`
   if the layout itself is the problem.

## The spectrum

| Where it sits | Signs | Better, when asked |
| --- | --- | --- |
| **one project with folders** | one `pyproject.toml` or none, one thing built and run; the folders are subpackages | not a monorepo: nothing to split; `core/layout.md` |
| **unpackaged units tied by paths** | units with no `pyproject.toml`, reached through `sys.path` lines, `PYTHONPATH` or copies; one shared `requirements.txt` or none | one uv workspace (`core/monorepo-better.md`) |
| **one project, several deployables** | one `pyproject.toml` with several scripts or packages, several Dockerfiles, one lock; every image installs everything | one workspace: a member per deployable and per shared library |
| **projects with their own locks** | a `pyproject.toml` and a `uv.lock` per folder; path dependencies, or no ties | a workspace when path dependencies tie them and one lock fits; otherwise they stay apart |
| **one uv workspace** | `[tool.uv.workspace]` at the root, one `uv.lock`, `{ workspace = true }` sources | bounds on siblings, one member per image (`core/workspaces.md`, `core/member-release.md`) |
| **another tool** | Pants, Bazel, Poetry, PDM or Hatch settings | recognised, never migrated unasked |

A repository can be **mixed**: a workspace with an independent project
beside it, or a workspace plus a folder of scripts reached through
`PYTHONPATH`. Place each unit and say so.

## The problems

| Problem | Evidence | Why it matters (lab, `recipes/untangle/before/`) |
| --- | --- | --- |
| **path hack** | `sys.path.insert` or `append` | works only from the checkout: the api tests without the CI variable failed with `ModuleNotFoundError: No module named 'common'` |
| **PYTHONPATH** | set in CI, a Dockerfile, `.env` | the same: `python -m worker` from another folder printed `No module named worker` |
| **copy** | the same module in two units | two places to fix a bug; a copy that drifted changes behaviour silently |
| **no lock** | a `requirements.txt` with no pins, no `uv.lock` | each build resolves again and can install other versions |
| **lock that does not fit** | the resolver's `cause:` for two units | the whole repository cannot lock (next section) |
| **unbounded sibling** | `Requires-Dist: acme-core` with no bound | the wheel accepts any future major version (`core/workspaces.md`) |
| **everything installed everywhere** | an image's install lists another unit's dependencies | bigger images, and a change to one unit's dependencies reaches every image |

Distribution names carry the team prefix (`acme-common`, not `common`),
and so do new import packages (`acme_common`), so an internal name never
meets a public one (`core/indexes.md`).

## When one lock fits

A workspace resolves every member together: **one version of each
package for the whole repository.** Units that import a shared library
must agree on it anyway, so for them one lock fits unless the resolver
says otherwise. Lab, uv 0.12.19:

- Two members needing incompatible versions stop the lock:
  ```
  cause: Because acme-api depends on pydantic>=2.13 and acme-billing depends on pydantic<2, we can conclude that acme-api and acme-billing are incompatible.
         And because your workspace requires acme-api and acme-billing, we can conclude that your workspace's requirements are unsatisfiable.
  ```
- The lock's `requires-python` is the highest floor of any member: one
  member at `>=3.13` makes the lock `>=3.13`, and even `uv sync --package
  acme-api` on Python 3.12 fails:
  ```
  error: The requested interpreter resolved to Python 3.12.3, which is incompatible with the project's Python requirement: `>=3.13` (from workspace member `acme-worker`'s `project.requires-python`).
  ```

| Situation | Choose |
| --- | --- |
| units that import a shared library, or are developed, tested and upgraded together | one workspace (`core/workspaces.md`, `recipes/workspace/`) |
| a unit that must stay on an older library or Python while the rest move | an independent project beside the workspace, using the library by path (`recipes/independent-projects/`) |
| units that share nothing but the repository | question 1 below; default independent projects |

uv 0.12.19 can also declare members that conflict, in one lock:
`[tool.uv] conflicts = [[{ package = "acme-api" }, { package =
"acme-billing" }]]`. It locked both pydantic versions in the lab, but
each command warns ``Declaring conflicts for packages (`package = ...`)
is experimental``, and `uv sync` at a virtual root then fails with
``Package `acme-api` and package `acme-billing` are incompatible with the
declared conflicts``. Offer it as the person's choice, never as the
default.

## Questions the evidence cannot answer

Only these, and only when the answer changes the plan. Ask them
together, once, before the first change, each with its evidence and the
default you will take. If the person says to go ahead, or has no
preference, take the defaults and list them under `Needs a person`.

| # | Question | Arises when | Show | Default |
| --- | --- | --- | --- | --- |
| 1 | Must `<x>` and `<y>` upgrade together? | two units share no import, no path dependency and no library | the empty tie searches for the pair | independent projects, each with its own lock; joining later is one step |
| 2 | Is `<folder>` a unit or dead code? | code with no sign and no importer | the map's last section, the search for its names, `git log -1 --format="%cs %s" -- <folder>` | leave it where it is, outside every member and every image; delete nothing |
| 3 | Is `<unit>` deployed on its own? | an entry point (a main guard, a script) that no Dockerfile or CI job names | the sign, and the empty searches for its folder and script in Dockerfiles and CI | its own member with a console script; no image changes |
| 4 | Which copy is right? | the same module in two units with different content | `git diff --no-index <a> <b>` | each unit keeps its own version inside its own package; merging them changes one unit's behaviour, so it waits for the answer |
| 5 | Should `<unit>` stay behind or migrate? | it cannot share the lock: a resolver conflict, or its image runs an older Python | the resolver's `cause:` lines, or the `FROM` line | an independent project beside the workspace; migrating is a separate task |

Decide the rest from the repository and say what you decided: which
folders are units and their roles, the order of the steps, prefixed
names, that folders stay where they are, the backend and layout the
other projects use (hatchling and src layout when there are none),
bounds from the current version (`>=1.0,<2`), one workspace when units
share code, and what each image installs. Never ask whether the
repository is a monorepo.

## Layout for a new monorepo

```
pyproject.toml          # [tool.uv.workspace], the index, a dev group
uv.lock                 # the one lock
packages/core/          # libraries: acme-core, import acme.core
services/api/           # deployable services: acme-api, import acme.api
```

Each member is a src-layout project with its own version. Shared
namespaces (`acme.core`, `acme.api`) are namespace packages
(`core/layout.md`). An existing repository keeps its folders where they
are (`core/monorepo-better.md`).

## Never

- Never decide from the word "monorepo", or ask the person to classify
  the repository: map it.
- Never loosen one service's bound so the whole repository locks: that
  changes the service's behaviour to fix a layout problem.
- Never convert a repository unasked; give the verdict and let the
  person decide. Asked to "make it better", follow
  `core/monorepo-better.md`.
