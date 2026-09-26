---
name: packaging
description: Turn Python code into something another machine can install, and install other people's packages safely, with uv. Write and fix pyproject.toml (metadata, requires-python, dependencies, extras, dependency groups), tell which build backend a project uses (hatchling, setuptools, uv_build; recognise poetry-core, pdm-backend, flit-core), src and flat layouts, package data and missing files, editable installs, console scripts and entry points, build a wheel or sdist and say what is in it, versions (static, uv version --bump, or from git tags with hatch-vcs or setuptools-scm), resolve dependency conflicts and read uv.lock, monorepos and uv workspaces (members, workspace sources, one lock or several, bounds on siblings, uv sync --package, releasing one member), internal indexes and the mirror ([[tool.uv.index]], explicit, sources, credentials, internal CA, dependency confusion), wheelhouses across the air gap, and publishing to an internal index. Load it for: pyproject, wheel, sdist, build, backend, package data, entry point, console script, version bump, tag, lock, conflict, uv add, workspace, monorepo, member, index, mirror, wheelhouse, offline install, publish, release. Verified on uv 0.12.19, hatchling 1.32.4, setuptools 84.0.0, Python 3.12.
---

# Packaging

This skill knows how Python projects are built, versioned, resolved,
installed and published with uv, and every command, key, default and
message in it was run on uv 0.12.19 (and uv_build 0.12.19), hatchling
1.32.4, hatch-vcs 0.5.0, setuptools 84.0.0, setuptools-scm 10.3.4 and
Python 3.12. Never write a key, flag or default from memory: find it
here, in `uv help <command>`, or in the backend's installed source (how to
read that is the offline-docs skill's).

Read this file, then load only what the task needs.

## Read the versions first

```
uv --version                                   # uv 0.12.19
uv run --no-sync python --version              # the project's Python
Select-String -Path pyproject.toml -Pattern 'requires =|build-backend'
```

The backend that built a wheel is in its `WHEEL` file: `inspect_dist.py`
prints it as `built by: hatchling 1.32.4`. `uv/versions.md` lists what
differs between uv 0.8.17 and 0.12.19. If `[tool.uv] required-version`
is set and uv does not match, every command stops with `Required uv
version ... does not match the running version`.

## The kinds of task

| Kind | You were asked to | Load |
| --- | --- | --- |
| **Orient** | explain how this project is packaged | `core/orient.md` |
| **Metadata** | write or fix `pyproject.toml`: name, Python range, dependencies, extras, groups | `core/metadata.md` |
| **Layout** | move to src layout, add a subpackage, ship data files | `core/layout.md`, the backend's file in `backends/` |
| **Entry point** | add or fix a console script | `core/entry-points.md` |
| **Build** | build a wheel or sdist and say what is in it | `core/build-and-inspect.md` |
| **Version** | bump, or derive from git tags | `core/versioning.md` |
| **Dependencies** | add, pin, upgrade, or resolve a conflict | `core/dependencies.md`, `uv/lockfile.md` |
| **Monorepo** | say how a repository of many packages is organised, or choose how it should be | `core/monorepo.md` |
| **Workspace** | set up or fix a uv workspace: add, move or split a member | `core/workspaces.md` |
| **Member release** | build, version or publish one member | `core/member-release.md`, then `core/publish.md` |
| **Index** | configure the mirror and internal indexes, credentials, the CA | `core/indexes.md`, `uv/config.md` |
| **Across the gap** | bring packages in, or build a wheelhouse | `core/across-the-gap.md`, `recipes/wheelhouse/` |
| **Publish** | prepare or publish a release to the internal index | `core/publish.md` |
| **Debug** | an install, import, build or resolution fails | `core/debug.md` |

Before you say any change is done, load `core/verify.md`.

## Where the facts are

| Folder | Holds |
| --- | --- |
| `core/` | the procedures above, each ending in a verdict |
| `backends/` | hatchling, setuptools and uv_build: file selection, data, versions, the errors they print; `others.md` recognises poetry-core, pdm-backend and flit-core |
| `uv/` | `commands.md` (the commands and flags used here), `config.md` (indexes, variables, credentials, the CA), `lockfile.md` (reading `uv.lock`), `versions.md` (uv 0.8 and 0.12) |
| `recipes/` | complete projects that were built, installed and run: `src-hatchling/`, `flat-setuptools/`, `uv-build/`, `workspace/`, `independent-projects/`, `internal-index/`, `wheelhouse/`; and `tools/inspect_dist.py` |
| `examples/` | three finished tasks: a data file lost in the wheel (`lost-data-file.md`), a resolver conflict (`conflict.md`), a workspace member released (`member-release.md`) |

`glossary.md` fixes the words. `recipes/README.md` says what each recipe
shows and how it was checked. Run the inspector with
`uv run --no-project python <skill>\recipes\tools\inspect_dist.py "dist\*"`.

## Invariants

1. **The built wheel is the evidence.** A package works when its wheel,
   installed by its path into a fresh venv, imports and runs its scripts
   from outside the checkout. Tests passing in the repository, or an
   editable install, prove nothing about the wheel (`core/verify.md`).
2. **Nothing is uploaded unasked, and never without a URL.** `uv publish`
   with no URL uploads to PyPI, and even `uv publish --dry-run` with no
   URL contacts PyPI. A version cannot be uploaded twice.
3. **Dependencies change through uv.** `uv add`, `uv remove`, `uv lock`.
   Never pip, never `uv pip install` into a project, never an edited
   `uv.lock`, never `--frozen` to get past a lock that does not match.
4. **Read the resolver before changing a bound.** Name the two
   requirements it says clash, find why each is there, change one.
   Never delete bounds wholesale.
5. **Internal packages come only from the internal index**: an index with
   `explicit = true` and one `[tool.uv.sources]` line per internal name.
   Never `unsafe-best-match`, never an extra index that can win.
6. **Credentials never appear** in `pyproject.toml`, `uv.lock`, a URL, a
   command line you show, or your answer (`uv/config.md`).
7. **Backend keys come from `backends/`**, never from memory. Several
   backends ignore a misspelled key without a word.
8. **The version is what the wheel says**, read from its file name and
   METADATA, not what you meant to set.
9. **Every sibling requirement is bounded** (`acme-core>=1.2,<2`) and has
   a workspace source. uv's lock does not check that bound: before a
   library's release, read every dependent.
10. **One workspace, one lock, one version of each package.** Members
    that need different versions are independent projects.
11. **Resolve against the mirror.** A lock that names `pypi.org` was made
    in another world; a build fetches its backend from the mirror too.

## What you say when you finish

End with these headings, each with `none` when empty. If another skill is
loaded, its headings come first and these after.

```
## Result
<what changed, or the cause found, with paths>

## Checked
<each command run and the line of its output that shows the verdict:
the wheel listing, "Successfully built ...", "Resolved 9 packages", the
script's output from the clean venv>

## Not checked
<what could not be run here: Windows, the real index, the other side of
the gap, and how to check it>

## Needs a person
<each URL, credential, upload, tag or decision someone must provide>
```

The `evals/` folder is for people testing this skill. Never open it while
doing a task.
