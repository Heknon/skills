# Roadmap: the next eleven skills

Status: all eleven plans written, one branch each, and reconciled here.
Nothing is built yet. Section 7 records what the plans changed.

This file is the map the eleven plans share: what each skill is, which
branch its plan lives on, what it depends on, and where the line runs
between two skills that touch the same ground. Each plan repeats its own
part of this map in its "Dependencies and boundaries" section; when the
two disagree, fix both.

## 1. The skills

| Skill | Plan | Branch | In one line |
| --- | --- | --- | --- |
| **debugging** | `plans/debugging-skill.md` | `claude/plan-debugging` | reproduce, shrink, one hypothesis at a time, fix, prove the fix |
| **offline-docs** | `plans/offline-docs-skill.md` | `claude/plan-offline-docs` | answer "how does this library work" with no web: installed source, `help()`, `pydoc`, `dist-info`, `--help` |
| **pydantic** | `plans/pydantic-skill.md` | `claude/plan-pydantic` | v2 models, validators, serialization, typing details, settings and config management, partial models for PATCH |
| **api** | `plans/api-skill.md` | `claude/plan-api` | API design (the contract) and FastAPI (the mechanics) |
| **architecture** | `plans/architecture-skill.md` | `claude/plan-architecture` | code structure from a single file to a service: where a new thing goes, custom errors, router, service, repository/DAL, the models at each boundary |
| **mongodb** | `plans/mongodb-skill.md` | `claude/plan-mongodb` | efficient queries, indexes, `explain`, aggregation, schema design, Beanie |
| **packaging** | `plans/packaging-skill.md` | `claude/plan-packaging` | `pyproject.toml`, build backends, wheels, entry points, monorepos and uv workspaces, internal indexes |
| **linting** | `plans/linting-skill.md` | `claude/plan-linting` | ruff, mypy and pyright: read, fix, configure, suppress; pre-commit in full |
| **git** | `plans/git-skill.md` | `claude/plan-git` | everyday git, naming commits, branches and tags by the repository's convention, tidying history before review, conflicts, bisect, recovery, bundles across the air gap |
| **refactoring** | `plans/refactoring-skill.md` | `claude/plan-refactoring` | behaviour-preserving steps, each checked |
| **code-review** | `plans/code-review-skill.md` | `claude/plan-code-review` | a severity-ranked review that ends in a verdict |

All eleven follow what the existing skills taught: a skill carries
knowledge and judgement, not enforcement; procedures end in a verdict;
facts are stamped with the version they were verified on; recipes are
complete files that ran; evals bait the failures and are written first.

## 2. The environment all eleven assume

The same as the existing skills: a weak model (MiniMax 2.7 for evals) in
Zed's agent on Windows with PowerShell, air gapped, Python run through uv,
packages only from an internal mirror, no web. Every name, flag, option
and API in a skill is verified on a pinned version or looked up in the
installed source, never written from memory.

## 3. Dependencies

"Needs" means the skill cannot be built well until the other one exists,
because it relies on its facts. "Relies on by name" means it points the
model at the other skill for part of a task, the way documentation relies
on navigation. Seniority is loaded on every task and is not listed.

| Skill | Needs | Relies on by name | Existing skills it touches |
| --- | --- | --- | --- |
| debugging | none | offline-docs, git (bisect), packaging | pytest, navigation, observability, deployment |
| offline-docs | none | navigation (which interpreter runs) | navigation |
| pydantic | none | offline-docs, linting, api, mongodb | deployment, documentation, pytest |
| packaging | none | offline-docs | deployment, pytest, navigation |
| linting | none | pydantic, offline-docs, git | pytest, navigation, deployment, documentation |
| git | none | none | navigation, deployment, pytest |
| api | pydantic | pydantic, offline-docs | pytest, observability, deployment, navigation |
| mongodb | pydantic | pydantic, offline-docs | observability, pytest, deployment |
| architecture | pydantic, api, mongodb | api, mongodb, pydantic | pytest, navigation |
| refactoring | architecture (only its `recipes/`) | architecture, linting, git, debugging | pytest, navigation, seniority's harness |
| code-review | architecture, linting | architecture, linting, pydantic, api, mongodb, offline-docs, git | pytest, navigation, deployment |

The "Needs" column as a graph:

```
pydantic ──┬──> api ──────┐
           ├──> mongodb ──┼──> architecture ──┬──> refactoring recipes
           └──────────────┘                   └──> code-review <── linting

debugging, offline-docs, packaging, git: need nothing new
```

## 4. Build order

Plans can all be written in parallel: a plan only needs to know the
boundaries in section 5. Building cannot:

| Wave | Build | Because |
| --- | --- | --- |
| 1 | pydantic, debugging, offline-docs, packaging, linting, git | need nothing new |
| 2 | api, mongodb; refactoring's `core/`, `steps/` and `legacy/` | api and mongodb stand on pydantic; refactoring's procedure stands on linting and git |
| 3 | architecture | stands on api and mongodb |
| 4 | code-review; refactoring's `recipes/` | stand on architecture and linting |

Inside wave 1, pydantic comes first: it is the only one others wait on.

## 5. Boundaries: who owns what

Where two skills touch the same ground, one owns the facts and the other
points at it.

### Data, models and APIs

| Ground | Owner | The other side |
| --- | --- | --- |
| a PATCH end to end | shared, see R4 | pydantic parses the partial model and validates the merged result with the full model; api owns the meaning (omitted is unchanged, `null` clears); mongodb writes only the changed fields as a dotted `$set`, guarded by a revision |
| partial models (`pydantic-partial`, `exclude_unset`, unset vs `None`) | pydantic | api and mongodb, as above |
| validation errors | pydantic owns `ValidationError` and its structure | api owns how it becomes a 422 or problem-details response |
| settings and config management (pydantic-settings, `.env`, layering, tracing a value) | pydantic | deployment owns where values are injected (CI variables, ConfigMaps, Secrets) |
| what pydantic types mean (`Annotated`, generics, discriminated unions, `Optional` vs default) | pydantic | linting owns running the checkers, their config and the pydantic mypy plugin setting |
| pagination | api owns the contract (cursor, page size, links) | mongodb owns the keyset query and the index behind it |
| error responses | api owns the error shape | architecture owns translating errors layer by layer on the way to it |
| custom exceptions: when to define one, the hierarchy, where it lives, its fields | architecture | api owns the handlers and response; pydantic owns errors inside validators; linting owns the ruff rules that flag them (N818, TRY002, TRY003, B904) |
| where one new thing goes (error, constant, enum, helper, type): existing file or new | architecture | a constant that differs by environment is a setting, owned by pydantic |
| FastAPI `Depends` mechanics, `dependency_overrides` | api | architecture owns what is injected and swapped; pytest owns fixtures |
| request and response models | api | architecture owns keeping them apart from domain and database models |
| Beanie (`Document`, `Link`, `init_beanie`, queries) | mongodb | architecture owns the repository pattern around it |
| transactions | mongodb owns Mongo sessions, transactions and their cost | architecture owns which layer starts and ends them (unit of work) |
| index builds on a large collection | mongodb | deployment runs one as a one-off job |
| SQLAlchemy repositories and sessions | architecture, for now | see R5 |
| renaming a serialized or stored name | api (wire names), mongodb (stored field names) | not a refactoring: refactoring stops and says so |

### Code, tools and the repository

| Ground | Owner | The other side |
| --- | --- | --- |
| layering rules (what a router, service, repository may do) | architecture, as checklist IDs with before and after shapes | code-review cites the IDs; refactoring's recipes move code between the shapes |
| layer rules enforced by a tool (import-linter) | architecture writes the rules | linting runs the tool |
| what ruff, mypy and pyright output means, and their config | linting | code-review runs them and does not repeat them; offline-docs owns only how to ask any tool about itself |
| `reveal_type` and reading an inferred type | navigation | linting owns what a checker error means |
| `pyproject.toml` | packaging owns `[project]`, `[build-system]`, dependency groups and `[tool.uv]`, including `[[tool.uv.index]]` | each tool's own table belongs to its skill (ruff, mypy, pyright: linting; pytest: pytest); deployment's `gitlab/python.md` points to packaging for index settings |
| a formatting-only commit, `.git-blame-ignore-revs` | linting decides | git performs |
| commit message, branch and tag conventions; tidying unpushed history | git | deployment owns GitLab push rules and squash-on-merge settings, read through the API; packaging owns the version a tag carries; code-review may comment on commits but never rewrites them |
| the step-by-step change procedure | refactoring | code-review may suggest a refactoring; it does not perform one |
| proving every reference to a name was found | navigation owns the searches | refactoring owns deciding a rename is complete |
| a bug found during a refactoring | debugging | refactoring stops the step; it never fixes and restructures in one step |
| reading history (log, blame, pickaxe) | navigation | git owns changing state: branches, merges, conflicts, rebase, bisect, reflog, bundles |
| looking things up in installed packages and tools | offline-docs | navigation owns finding code in the repository and which interpreter runs |
| the hypothesis loop, reading the first error, breaking a loop | seniority | debugging adds reproduction, shrinking, proof of the fix, tracebacks and tools |
| the generic debugging loop | debugging | pytest, deployment, observability and mongodb keep their domain ladders |
| flaky tests (order, seeds, xdist) | pytest | debugging owns timing bugs in the code under test |
| building a Python distribution and cutting a release | packaging | deployment owns container images, Helm charts and the CI job that publishes |
| a monorepo's packages: its kind, the workspace, one lock or several, bounds on siblings, member versions | packaging | deployment owns building only what changed and one member per image; linting owns hooks per member |
| pre-commit: config, hook types and stages, offline hooks, monorepos, running in CI | linting | each hook's check stays with its owner (commit-msg format: git; `uv lock --locked`: packaging; tests at `pre-push`: pytest); git owns `core.hooksPath` and never passing `--no-verify` unasked; deployment writes the CI job |
| GitLab API access (tokens, certificates, PowerShell calls) | deployment | code-review uses only the merge request diff and note endpoints |

## 6. Decisions for the whole family

### R1. offline-docs as its own skill or a folder of navigation

*Recommended, and the offline-docs plan agrees:* its own small skill. It
starts from navigation's Environment answer and does not repeat it;
navigation gets one pointer line in `tools/terminal-probes.md`.

### R2. Versions to pin

The plans agree where they overlap. Every one was read from the public
index on 2026-09-25 and must be confirmed against the internal mirror,
along with the versions the team's services actually run.

| Package | Version | Used by |
| --- | --- | --- |
| Python | 3.12 | all |
| uv, uv_build | 0.12.19 | packaging (same uv as deployment) |
| pydantic | 2.13.5 | pydantic, api, linting |
| pydantic-settings | 2.15.0 | pydantic |
| pydantic-partial | 0.11.1 | pydantic |
| FastAPI, Starlette | 0.141.1, 1.7.0 | api, architecture |
| Beanie | 2.2.0 (1.30.0 for reading old code) | mongodb, architecture |
| PyMongo | 4.18.2 | mongodb, architecture |
| MongoDB server | 8.0 | mongodb |
| SQLAlchemy | 2.1.1 | architecture |
| ruff, mypy, pyright | 0.16.9, 2.3.1, 1.1.414 | linting |
| hatchling | 1.32.4 | packaging |

Open: Beanie's own test setup pins FastAPI below 0.130; the pairing with
0.141 is to verify in the lab before architecture's recipes are written.

### R3. Where the plans merge

Each plan branch starts from `claude/ai-air-gapped-skills-cv1bws`, which
carries this file. A plan is merged back into it once agreed; the skill is
then built on its own branch.

### R4. The PATCH flow

The pydantic plan found, on pydantic 2.13.5 and pydantic-partial 0.11.1,
that a partial model drops length constraints, passes `None` into the
full model's validators (an `AttributeError`, so a 500), and does not
reach nested models without the mixin (all to reconfirm in the lab). It
recommends validating the merged result with the full model. The mongodb
plan recommends writing a patch as a dotted `$set`. They fit together:

1. Parse the body with the partial model (pydantic).
2. Read the stored document with its revision.
3. Apply the patch in memory and validate the result with the full model
   (pydantic), which also catches rules across fields.
4. Write only the fields that changed as a dotted `$set`, filtered on the
   revision read in step 2 (mongodb). Lists are replaced whole; `null`
   is `$set: null`, never `$unset`. A revision mismatch is a 409 or a
   retry (api).

*Recommended:* this flow, with the pydantic, api and mongodb skills each
teaching their own steps and naming the others.

### R5. SQL and migrations have no owner

architecture carries SQLAlchemy repository and session facts, and nothing
owns schema migrations (Alembic) or SQL query efficiency. *Recommended:*
architecture keeps the SQLAlchemy shapes it needs; a later sql skill
(SQLAlchemy, Alembic, `EXPLAIN`) takes the rest if SQL services matter.
Stored-field changes in Mongo stay with mongodb.

### R6. Calling other APIs has no owner

HTTP clients (httpx), timeouts, retries and backoff are out of the api
plan's scope. *Recommended:* leave them out until a service needs them,
then add a `clients/` folder to api.

### R7. seniority's change check and refactorings

`harness/seniority-checks/check_change.py` builds the public API from
top-level `def` and `class` only (`public_api`, line 107). A function
moved to another module and kept importable with `from new import f`
therefore counts as removed, and a module split counts as a deleted file.
Both would fail a correct refactoring. *Recommended:* count imported
names as part of a module's public API, and let a split name the module
that replaced it; a separate change to the harness, reviewed against its
fixtures, before refactoring's evals run.

*Done:* `check_change.py` now follows a `from x import name` re-export to
the module that defines the name and compares its signature there, and
compares a module that became a package with its `__init__.py`. The
`fixtures/move/` pair (a correct move and split, and a move that changed
a default and dropped a method) is in `run_fixtures.sh`; the harness
passes. After the refactoring lab, it also follows aliases (`old = new`),
method aliases, `mod.name` and star-import shims, looks under every
`src` folder up to three levels down, treats a module-level
`__getattr__` as unreadable rather than removed, fails a shim that
points at a missing module of the project, and gives a function moved
into an existing file its old error-handler count (`fixtures/move2/`).

## 7. What the plans changed in this roadmap

- Dependencies found that the first draft missed: navigation is touched
  by nine of the eleven; offline-docs relies on navigation; debugging
  relies on git and packaging; code-review relies on offline-docs and
  git; pydantic relies on linting, api and mongodb.
- Wave 4 no longer claims to stand on git: git is relied on by name, not
  needed. Most of refactoring moves to wave 2; only its `recipes/` wait
  for architecture.
- Section 5 is split in two and gained seventeen rows, among them PATCH,
  pagination, validation errors, transactions, `pyproject.toml` and
  seniority's hypothesis loop.
- Four gaps now have decisions: R4 to R7.
