# Workspaces: set up or fix a uv workspace

**Verdict you produce:** the members, their sources and bounds, and the
commands that passed.

```
members:  <uv workspace list>
sources:  <member>: <sibling> = { workspace = true }, bound <spec>
lock:     uv lock (at the root or in any member) -> "Resolved <n> packages"; no uv.lock in members
sync:     uv sync --package <member> -> <what it installed>
```

Recipe: `recipes/workspace/` (a library and a service, namespace
packages, verified end to end).

## The pieces

Root `pyproject.toml` (lab: a root with no `[project]` works; it is a
virtual root):

```toml
[tool.uv.workspace]
members = ["packages/*", "services/*"]
exclude = ["services/billing"]        # only when a folder must stay out

[[tool.uv.index]]                     # the index lives at the root, once
name = "mirror"
url = "https://pypi-mirror.example.com/simple"
default = true
```

A member that uses a sibling:

```toml
[project]
dependencies = ["acme-core>=1.2,<2"]  # bounded: the wheel publishes this

[tool.uv.sources]
acme-core = { workspace = true }      # in development: the folder
```

## Facts (uv 0.12.19, lab)

| Fact | Evidence |
| --- | --- |
| A sibling without a source stops the lock | ``error: Failed to build `acme-api @ file:///.../services/api` `` ... ``cause: `acme-core` is included as a workspace member, but is missing an entry in `tool.uv.sources` (e.g., `acme-core = { workspace = true }`)`` |
| A path source to a member is refused | ``cause: `acme-core` is included as a workspace member, but references a path in `tool.uv.sources`. Workspace members must be declared as workspace sources (e.g., `acme-core = { workspace = true }`).`` |
| `uv add acme-core` in a member writes the source and a **bare** requirement | `"acme-core"` and `acme-core = { workspace = true }`; `--bounds major` (preview) also left it bare. Write the bound: `uv add "acme-core>=1.2,<2"` |
| **The lock ignores the bound on a workspace source** | with acme-core at 2.0.0 and a member requiring `acme-core>=1.2,<2`, `uv lock` passed and `uv sync` installed 2.0.0; the lock records `{ name = "acme-core", editable = "packages/core" }` with no specifier. The same holds for `{ path = ... }` sources |
| The bound reaches the wheel | `Requires-Dist: acme-core<2,>=1.2`; bare gives `Requires-Dist: acme-core` |
| One lock, at the root | `uv lock` in `services/api` wrote the root `uv.lock`; no lock appeared in the member |
| One `.venv`, at the root | `uv sync` in a member folder uses the root `.venv` and removes what that member does not need |
| `uv sync` at a virtual root installs every member and the root's `dev` group | `+ acme-api`, `+ acme-core`, `+ acme-worker`, `+ pytest` ... |
| `uv sync --package acme-worker` installs that member, its siblings and its own groups | `+ acme-core`, `+ acme-worker`, `+ click`; not the root's `dev` group; add `--no-dev` to leave out the member's `dev` group too |
| A missing member folder breaks `--locked` | with `services/api` deleted, `uv sync --locked --package acme-worker` failed: `The lockfile at uv.lock needs to be updated` |
| A stale lock | `uv lock --locked` (or `--check`) exits 1: ``The lockfile at `uv.lock` needs to be updated, but `--locked` was provided.`` |
| An excluded project sees no root settings | `services/billing`, excluded, resolved against pypi.org until it had its own `[[tool.uv.index]]` |

## Steps: add a member

1. Create it from the root: `uv init --package --name acme-reports
   services/reports`. Without `--name` the project is named after the
   folder (`reports`). uv adds the path to `members` unless a glob already
   covers it (lab: `Adding reports as member of workspace`, or `is already
   a member`); `--no-workspace` keeps it out.
2. Give it the backend and layout of the others (`core/layout.md`).
3. For each sibling it uses: the bounded requirement and the workspace
   source, as above.
4. `uv lock` at the root; `uv sync --package <member>`; its tests with
   `uv run --package <member> pytest services/<member>`.

## Steps: split a member out (it needs other versions)

1. Add its folder to `exclude` in the root, or move it out of the globs.
2. Give it its own `[[tool.uv.index]]` (it no longer sees the root's),
   and turn each workspace source into a path source:
   `acme-core = { path = "../../packages/core", editable = true }`.
3. `uv lock` in its folder: a `uv.lock` appears there. `uv lock` at the
   root: the member is gone from the root lock.
4. Its CI job and image now use its own folder and lock: say so, for the
   deployment skill.

## Never

- Never fix a missing source with a path, an index or `--find-links`.
- Never run a bare `uv sync` at the root to prepare one member's image or
  job (`core/member-release.md`, deployment's monorepo recipe).
- Never trust `uv lock` to check sibling bounds; `core/member-release.md`
  has the check that does.
