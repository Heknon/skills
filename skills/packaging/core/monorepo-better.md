# Make a repository of units better, one step at a time

For "this is a monorepo, let's make it better", or any request to clean
up how several units in one repository are packaged. The walk in
`examples/untangle-monorepo.md` followed this page from the worst
realistic state to one uv workspace, on uv 0.12.19; its before and after
are in `recipes/untangle/`.

**Verdict you produce:**

```
map:        the verdict of core/monorepo.md (units, ties, spectrum, problems, questions)
baseline:   <each unit's tests and entry points, run the way CI and the images run them today>
step <n>:   <what changed>  check: <the lines that show it passed>
            docker and CI: <what must change, for the deployment skill | nothing>
end:        <where it sits now; the problems left and why>
```

## Before the first step

1. **Map** with `core/monorepo.md` and ask its questions, if any, once.
2. **Baseline.** Run each unit's tests and entry points exactly as CI
   and the Dockerfiles run them today, and keep the output lines: every
   later check compares with them. Lab:
   ```
   PYTHONPATH=<root> pytest api/tests           1 passed
   python api/main.py quote 12.50 3             quote 37.50 EUR
   PYTHONPATH=. python -m worker 1.10 2.20      batch total 3.30 EUR
   ```
   If the baseline fails, stop: that is a bug to fix first
   (`core/debug.md`).
3. **Choose the end.** Units that import a shared library go into one
   workspace (`core/monorepo.md`, when one lock fits). Folders stay where
   they are: moving them changes every CI path and Dockerfile for no gain.

## Which step fixes which problem

| Problem | Step |
| --- | --- |
| copy, identical | 1 |
| copy, different | question 4 of `core/monorepo.md`; each unit keeps its own |
| no lock, a shared `requirements.txt` | 2 |
| path hack, `PYTHONPATH` for shared code | 3, when the code it reaches becomes a member |
| path hack, `PYTHONPATH` for a unit's own code | 4, when that unit becomes a member |
| unbounded sibling | 3 and 4: every sibling requirement is written with its bound |
| everything installed everywhere | 4: the unit's image installs `--package <member>` |
| a unit that cannot share the lock | an independent project (`core/workspaces.md`, split a member out) |
| units that already have their own projects and locks | skip steps 2 and 3; each joins the workspace in step 4 (below) |
| packages that share one `pyproject.toml` | no step 2; each moves out to its own member in steps 3 and 4 (below) |

## The steps

One step, then its check, then a commit (git skill), then the next.
Every check runs each affected unit's tests and entry points. A step that
fails its check is undone, not patched forward.

### Step 1: remove identical copies

Keep the module in the shared unit, point the copy's importers at it,
delete the copy. `git diff --no-index <a> <b>` printed nothing (exit 0)
first. Check: the search for the copy's import returns nothing (exit 1),
and the unit's tests and entry point match the baseline.

### Step 2: lock what is there

A workspace root with no members yet, holding the shared requirements
in a temporary group, so CI and the images install from a lock:

```toml
# pyproject.toml at the root: no [project], so it is never built.
[tool.uv.workspace]
members = []

[[tool.uv.index]]
name = "mirror"
url = "https://pypi-mirror.example.com/simple"
default = true
```

```
uv add --group legacy -r requirements.txt
uv remove --group legacy pytest
uv add --dev "pytest>=9.1.1"
```

Then add `[tool.uv] default-groups = ["dev", "legacy"]`, run `uv lock`,
and delete `requirements.txt`. Lab facts (uv 0.12.19):

- `uv add -r` wrote bounds from what it resolved (`click>=8.5.0`,
  `httpx>=0.28.1`) and kept the written ones (`pydantic>=2`).
- Without `default-groups`, `uv run` removes a group it was not given:
  `uv run python -c "import click"` failed with `ModuleNotFoundError: No
  module named 'click'`. With it, plain `uv run` and `uv sync` include
  `legacy`, and `uv sync --no-dev` removed only the `dev` tools.
- With no member yet, every command warns ``No `requires-python` value
  found in the workspace. Defaulting to `>=3.12`.`` The first member
  ends it.

Docker and CI (deployment's files): `pip install -r requirements.txt`
becomes `uv sync --locked` in CI and `uv sync --locked --no-dev
--no-editable` in each image, with the whole repository as the build
context (`COPY . .`, `.venv` in `.dockerignore`); the ties the units
still need (`PYTHONPATH`) stay. Check: the baseline again, through `uv
run` and in each image.

### Step 3: shared code becomes a member

For each library unit, starting with the one others import most:

1. Move its modules into `<folder>/src/<prefix>_<name>/` (`git mv`).
2. From the root:
   ```
   uv init --lib --name acme-common --build-backend hatch --vcs none --no-readme --no-pin-python --author-from none common
   ```
   uv printed ``Adding `acme-common` as member of workspace``, kept the
   existing `__init__.py`, and added `py.typed`. Set the version (it
   writes `0.1.0`) and the description, and bound the backend
   (`requires = ["hatchling>=1.27"]`). Without `--author-from none` it
   copies `authors` from git config.
3. Rename every import of the old name, then prove none is left:
   `git grep -n -E "^\s*(from|import)\s+common\b"` must print nothing
   (exit 1). In a large repository this is the refactoring skill's move.
4. Delete each path hack that existed only for this unit.

Check: `uv lock` (lab: `Added acme-common v1.0.0`), every importer's
tests and entry points against the baseline, and the library's wheel:
`uv build --package acme-common`, `inspect_dist.py --against
common/src/acme_common` (`every source file is in the distribution`),
installed by path in a clean venv and imported from outside the
checkout. Docker and CI: nothing; a sync at the root installs every
member.

### Step 4: each deployable unit becomes a member

One unit per step:

1. Move its modules into `<folder>/src/<prefix>_<name>/`; delete
   `conftest.py` files that only added paths.
2. `uv init --package` with the same options and the unit's name and
   folder. **Fix what it wrote at once:** `[project.scripts] acme-api =
   "acme_api:main"`, and, with no `__init__.py` there, an `__init__.py`
   whose `main` prints `Hello from acme-api!`. With an existing empty `__init__.py` it kept that
   file, and the script failed: `ImportError: cannot import name 'main'
   from 'acme_worker'`. Point the script at the real command
   (`acme_api.main:cli`) and empty the generated `__init__.py`.
3. Rename its imports and prove none of the old names is left.
4. Its dependencies, bounded, the sibling with a workspace source:
   ```
   uv add --package acme-api "acme-common>=1.0,<2" "click>=8.5.0" "pydantic>=2"
   uv remove --group legacy pydantic
   ```
   Remove from `legacy` only what no unit still outside needs.

Check: `uv lock --check`; its tests with no `PYTHONPATH`; its script
through `uv run`; `uv build --package` for it and its siblings, both
wheels installed by path in a clean venv, the script run from outside
the checkout; its tests against the wheels:

```
uv run --isolated --no-project --with dist\acme_api-1.0.0-py3-none-any.whl --with dist\acme_common-1.0.0-py3-none-any.whl --with pytest pytest api/tests
```

Docker and CI: its image installs `uv sync --locked --no-dev
--no-editable --package acme-api` and runs the console script. Lab: that
sync installed acme-api, acme-common, click, pydantic and their
dependencies, and nothing from `legacy`: **`--package` leaves out the
root's groups, default or not.** The units still outside keep their
root sync; `uv sync --locked` needs every member's folder in the build
context.

**Units that already have projects and locks** join here. Lab, with
`recipes/independent-projects/` (billing uses core by path):

1. Add the folders to `members` in a root `pyproject.toml` with the
   index. `uv lock` at the root then stopped: ``cause: `acme-core` is
   included as a workspace member, but references a path in
   `tool.uv.sources`.``
2. Turn each such source into `acme-core = { workspace = true }`.
   `uv lock` passed (`Resolved 10 packages`).
3. Delete each member's own `uv.lock`: uv ignored them without a word,
   so they only mislead. Delete each member's `[[tool.uv.index]]`: the
   root's serves every member (the lock still resolved from the mirror).
4. Check: `uv workspace list` printed both; billing's tests passed with
   `uv run --package acme-billing --group dev pytest billing/tests`.

**Packages that share one `pyproject.toml`** (one project, several
deployables) move out the same way, one per step, and need no `legacy`
group: the root's `[project]` keeps what has not moved. Lab, a root
`acme-platform` building `acme_api`, `acme_worker` and `acme_shared`:

1. `acme_shared` moved to `shared/src/`, its own `pyproject.toml`,
   `[tool.uv.workspace] members = ["shared"]` added to the root, and
   `uv add "acme-shared>=1.0,<2"` at the root. The root is then both
   workspace root and member: `uv workspace list` printed
   `acme-platform` and `acme-shared`. Take the moved package out of the
   root's `packages` list in the backend's settings.
2. `acme_api` moved to `api/` with its script and dependencies. **At a
   root with `[project]`, `uv sync` installs only the root project:**
   the tests then failed with `ModuleNotFoundError: No module named
   'acme_api'` until `uv sync --all-packages`. CI uses `--all-packages`
   until the root is virtual.
3. With `acme_worker` moved too, the root's `[project]`, scripts,
   `[build-system]` and backend settings were deleted, leaving the
   workspace table, the index and the `dev` group. `uv lock` printed
   `Removed acme-platform v3.2.0` and `Added acme-worker v3.2.0`; `2
   passed`, and both scripts ran.

### Step 5: remove what the transition needed

When the last unit is a member: delete the `legacy` group and the
`default-groups` line, and `PYTHONPATH` from CI, the Dockerfiles, `.env`
and the README. Check:

- `git grep -n PYTHONPATH` and `git grep -n -E
  "sys\.path\.(insert|append)"` print nothing; `map_units.py` lists no
  sys.path lines, no `PYTHONPATH`, no copies, and one workspace.
- `uv lock --check`, `uv workspace list` (every member), all tests.
- `uv build --all-packages` and `inspect_dist.py` on each wheel: every
  sibling requirement bounded (`Requires-Dist: acme-common<2,>=1.0`).
- Each service's wheels in its own clean venv: the venv holds only its
  needs (lab: the worker's had httpx and no pydantic, the api's the
  reverse, neither pytest), and each script runs from outside the
  checkout.
- Each image's sync lists only its unit's needs.

## Docker and CI

This skill says what must change; the deployment skill writes it
(`deployment/core/monorepo.md` and its `recipes/monorepo/` Dockerfile).
The lab had no container engine: each image was checked by extracting
the committed tree as the build context, running the Dockerfile's `uv
sync` line in it, and running its command from another folder. Say so
under `Not checked`.

## Never

- Never do several steps at once, or go on after a red check.
- Never move folders, rename distributions already published, or merge
  copies that differ as part of this procedure.
- Never leave a `uv init` script line unchecked: run each script once.
- Never keep a `PYTHONPATH` or `sys.path` line "just in case": the map
  must end clean, or say which line stays and why.
