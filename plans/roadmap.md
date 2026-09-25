# Roadmap: the next eleven skills

Status: plans being written, one branch each. Nothing is built yet.

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
| **architecture** | `plans/architecture-skill.md` | `claude/plan-architecture` | backend structure: router, service, repository/DAL, the models at each boundary |
| **mongodb** | `plans/mongodb-skill.md` | `claude/plan-mongodb` | efficient queries, indexes, `explain`, aggregation, schema design, Beanie |
| **packaging** | `plans/packaging-skill.md` | `claude/plan-packaging` | `pyproject.toml`, build backends, wheels, entry points, internal indexes |
| **linting** | `plans/linting-skill.md` | `claude/plan-linting` | ruff, mypy and pyright: read, fix, configure, suppress |
| **git** | `plans/git-skill.md` | `claude/plan-git` | everyday git, conflicts, bisect, recovery, bundles across the air gap |
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
| debugging | none | offline-docs | pytest, navigation, observability, deployment |
| offline-docs | none | none | navigation |
| pydantic | none | offline-docs | deployment (where config values come from) |
| packaging | none | offline-docs | deployment (uv, mirrors, images) |
| linting | none | pydantic (checker errors on models) | pytest (config in `pyproject.toml`) |
| git | none | none | navigation (the History question) |
| api | pydantic | pydantic, offline-docs | pytest (`TestClient`) |
| mongodb | pydantic | pydantic | observability (slow queries) |
| architecture | pydantic, api, mongodb | api, mongodb, pydantic | pytest (swapping dependencies in tests) |
| refactoring | architecture | architecture, linting, git | pytest (characterization tests) |
| code-review | architecture, linting | architecture, linting, pydantic, api, mongodb | pytest, seniority |

The "Needs" column as a graph:

```
pydantic ──┬──> api ──────┐
           ├──> mongodb ──┼──> architecture ──┬──> refactoring
           └──────────────┘                   └──> code-review <── linting

debugging, offline-docs, packaging, git: need nothing new
```

## 4. Build order

Plans can all be written in parallel: a plan only needs to know the
boundaries in section 5. Building cannot:

| Wave | Build | Because |
| --- | --- | --- |
| 1 | debugging, offline-docs, pydantic, packaging, linting, git | need nothing new |
| 2 | api, mongodb | stand on pydantic |
| 3 | architecture | stands on api and mongodb |
| 4 | refactoring, code-review | stand on architecture, linting and git |

Inside wave 1, pydantic comes first: it is the only one others wait on.

## 5. Boundaries: who owns what

Where two skills touch the same ground, one owns the facts and the other
points at it.

| Ground | Owner | The other side |
| --- | --- | --- |
| partial models (`pydantic-partial`, `exclude_unset`, unset vs `None`) | pydantic | api owns PUT vs PATCH semantics; mongodb owns turning a patch into a dotted `$set` |
| settings and config management (pydantic-settings, `.env`, layering, tracing a value) | pydantic | deployment owns where values are injected (CI variables, ConfigMaps, Secrets) |
| what pydantic types mean (`Annotated`, generics, discriminated unions, `Optional` vs default) | pydantic | linting owns running the checkers, their config and the pydantic mypy plugin setting; pydantic explains why a checker complains about a model |
| FastAPI `Depends` mechanics | api | architecture owns dependency injection as the way layers are wired and swapped |
| request and response models | api | architecture owns keeping them apart from domain and database models |
| Beanie (`Document`, `Link`, `init_beanie`, queries) | mongodb | architecture owns the repository pattern around it and relies on mongodb for Mongo facts |
| layering rules (what a router, service, repository may do) | architecture | code-review turns them into checklist items; refactoring into recipes that fix them |
| what ruff, mypy and pyright catch | linting | code-review does not repeat what a tool already flags; it runs the tool and reads the output |
| the step-by-step change procedure | refactoring | code-review may suggest a refactoring; it does not perform one |
| reading history (log, blame, pickaxe) | navigation | git owns changing history and state: branches, merges, conflicts, rebase, bisect, reflog, bundles |
| looking things up in installed packages and the environment | offline-docs | navigation keeps finding code in the repository and which interpreter runs it |
| the generic debugging loop | debugging | pytest, deployment and observability keep their domain ladders (read a test failure, a failing pod, a trace) |
| building and publishing Python distributions | packaging | deployment owns container images and Helm charts; both use the same internal mirror |

## 6. Decisions for the whole family

### R1. offline-docs as its own skill or a folder of navigation

navigation already has `environment.md` and `terminal-probes.md`.
*Recommended:* its own skill, because "how does this library work" is a
different question from "where is this in our code", and every domain
skill needs it. The offline-docs plan argues it either way.

### R2. Versions to pin

Each plan proposes the versions it will be verified on. They should agree
where they overlap: one pydantic, one FastAPI, one Beanie, one MongoDB
server, one Python.

### R3. Where the plans merge

Each plan branch starts from `claude/ai-air-gapped-skills-cv1bws`, which
carries this file. A plan is merged back into it once agreed; the skill is
then built on its own branch.
