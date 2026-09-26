# Monorepo: which kind is it, and which kind should it be

**Verdict you produce:** the kind, every package with its role, and
whether one lock fits.

```
kind:     <uv workspace | independent projects | path dependencies | other tool: <name>>
members:  <folder>  <distribution>  <library | service>  depends on <siblings, with bounds>
lock:     <one uv.lock at <root> | one per project: <paths>>
one lock fits: <yes | no: <package> needs <a> in <x> and <b> in <y>>
```

The deployment skill owns building only what changed and one member per
image; linting owns hooks per member; this skill owns the rest.

## Recognise the kind

| Kind | Sign | Locks |
| --- | --- | --- |
| uv workspace | `[tool.uv.workspace] members = [...]` in the root `pyproject.toml`; `{ workspace = true }` sources; one `uv.lock` at the root | one for every member |
| independent projects | a `pyproject.toml` and a `uv.lock` per folder, no workspace table above them | one per project, each resolved alone |
| path dependencies | `{ path = "../core", editable = true }` in `[tool.uv.sources]`, no workspace | one per project |
| other tools | `pants.toml`, `BUILD` files, Poetry or Hatch workspace settings | recognised, never migrated unasked |

`uv workspace list` prints the members' names (`--paths` for folders;
new in 0.12, `uv/versions.md`). A folder named in `exclude = [...]` of
the workspace table is not a member, even inside a member glob.

## When one lock fits

A workspace resolves every member together: **one version of each
package for the whole repository.** Lab, uv 0.12.19:

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

So:

| Situation | Choose |
| --- | --- |
| members developed, tested and upgraded together; libraries and the services that use them | one workspace (`core/workspaces.md`, `recipes/workspace/`) |
| a service that must stay on an older library or Python while the rest move | an independent project beside the workspace, using the library by path (`recipes/independent-projects/`) |
| services that share nothing but the repository | independent projects |

uv 0.12.19 can also declare members that conflict, in one lock:
`[tool.uv] conflicts = [[{ package = "acme-api" }, { package =
"acme-billing" }]]`. It locked both pydantic versions in the lab, but
each command warns ``Declaring conflicts for packages (`package = ...`)
is experimental``, and `uv sync` at a virtual root then fails with
``Package `acme-api` and package `acme-billing` are incompatible with the
declared conflicts``. Offer it as the person's choice, never as the
default.

## Layout for a new monorepo

```
pyproject.toml          # [tool.uv.workspace], the index, a dev group
uv.lock                 # the one lock
packages/core/          # libraries: acme-core, import acme.core
services/api/           # deployable services: acme-api, import acme.api
```

Each member is a src-layout project with its own version. Shared
namespaces (`acme.core`, `acme.api`) are namespace packages
(`core/layout.md`). Distribution names carry the team prefix
(`acme-core`, not `core`), so an internal name never matches a public one
by accident (`core/indexes.md`).

## Never

- Never loosen one service's bound so the whole repository locks: that
  changes the service's behaviour to fix a layout problem.
- Never convert a repository between kinds unasked; say which kind fits
  and why, and let the person decide.
