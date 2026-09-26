---
name: architecture
description: Structure Python code, from one new file to a FastAPI service, by the codebase's own precedent first. Recognise how a service is laid out (by layer, by feature, crud modules, hexagonal) and trace a request through it; decide where a new endpoint, rule, query, mapping, provider, exception, constant, enum, type or helper goes, and whether it joins an existing file or earns a new one; routers, services, repositories and the DAL over Beanie or SQLAlchemy 2 async; request, response, domain and database models kept apart; dependency injection with Depends and dependency_overrides in tests; unit of work and who commits; custom exceptions (when to define one, hierarchy, where, fields, pickling) and database errors turned into domain errors and HTTP responses; circular imports between layers; MissingGreenlet after commit; a layering checklist L1 to L11 with before and after shapes, for review and refactoring. Verified on Python 3.12, FastAPI 0.141.1, pydantic 2.13.5, Beanie 2.2.0 on PyMongo 4.18.2 and MongoDB 8.0.32, SQLAlchemy 2.1.1 on aiosqlite.
---

# Architecture

This skill knows how a Python backend is put together and where one new
thing goes in it, and it reads the codebase before it prescribes. Every
behaviour, error message and API in it was run in a lab on Python
3.12.14, FastAPI 0.141.1 (Starlette 1.7.0), pydantic 2.13.5, pytest
9.1.1, Beanie 2.2.0 on PyMongo 4.18.2 with MongoDB 8.0.32, SQLAlchemy
2.1.1 on aiosqlite, ruff 0.16.9 and import-linter 2.15. PostgreSQL
facts were read in installed source and are marked *not run on
PostgreSQL*. Nothing is written from memory.

Read this file, then load only what the task needs.

## Read the versions first

```
uv pip show fastapi starlette pydantic beanie pymongo sqlalchemy
uv run --no-sync python -c "import sys; print(sys.version)"
```

A package shown as not found is not used. If a version differs from the
ones above by more than a patch release, check each fact you rely on in
the installed source (the offline-docs skill says how).

## The kinds of task

Most tasks start with **Recognise**. A task often needs several kinds in
turn, such as Recognise, then Place, then Errors.

| Kind | You were asked to | Load |
| --- | --- | --- |
| **Recognise** | explain how this service is structured; the first step of any change | `core/recognise.md`, `core/card.md`, `core/layouts.md` |
| **Place** | add an endpoint or a feature | `core/place.md`, `core/layers.md` |
| **Place a thing** | add one exception, constant, enum, helper, type or provider | `placement/place-a-thing.md`, then the `placement/` file it names |
| **Models** | separate or map request, response, domain and database models | `core/boundary-models.md` |
| **Wire** | inject or swap a service or repository, in the app or a test | `core/wiring.md` |
| **Transaction** | make several writes atomic; decide who commits | `core/transactions.md`, then `sqlalchemy/unit-of-work.md` or `beanie/sessions.md` |
| **Errors** | design custom exceptions; turn database errors into domain errors and responses | `placement/custom-errors.md`, `core/errors.md` |
| **Repository** | write or fix a repository over Beanie or SQLAlchemy | `beanie/repository.md` or `sqlalchemy/repository.md`, and `recipes/` |
| **Check** | check a change or a codebase for layering violations | `checklist/violations.md`, `checklist/finding.md` |
| **Shape** | describe the target structure for moving some code | `shapes/README.md` and the `shapes/L*.md` file of the ID |
| **Design** | lay out a new service | `core/design.md` |

## Where the facts are

| Folder | Holds |
| --- | --- |
| `core/` | the procedures: recognise and the structure card, place, design, layers, layouts, boundary models, wiring, transactions, errors |
| `placement/` | one new thing: the procedure, new file or existing, defaults with no precedent, custom errors, constants and enums, helpers |
| `checklist/` | violations L1 to L11 (stable IDs for code-review) and the search for each, with what it misses |
| `shapes/` | per ID, a before and an after with a test that passes on both (`check_shapes.py` runs them) |
| `beanie/` | the repository, sessions and transactions, errors, testing |
| `sqlalchemy/` | the async session, repository, unit of work, loading and `MissingGreenlet`, errors, a note on SQLModel |
| `recipes/` | `sqlalchemy_service/` and `beanie_service/`: the same accounts service, tested with fakes and a real database |
| `examples/` | three finished tasks: recognise a crud layout (`recognise-crud-layout.md`), check a leaky change (`check-a-leaky-change.md`), place an error (`place-an-error.md`) |

`glossary.md` fixes the words. Other skills own neighbouring ground:
api (`Depends` mechanics, overrides, handlers, status codes, the error
body, PATCH), pydantic (what a model does, settings), mongodb (Beanie
and every Mongo fact, transactions' cost), navigation (searching and
tracing), linting (running ruff and import-linter), refactoring (the
steps from a before to an after), pytest (fixtures).

## Invariants

1. **Recognise first, then follow the card.** No change before the
   structure card; every file you add or change is placed by a line of
   it (`core/card.md`).
2. **Precedent beats defaults.** Where the codebase keeps a kind of
   thing, the new one goes too, even when a default is better. Say so
   when it matters; never migrate unasked (`placement/place-a-thing.md`).
3. **Add no layer, file or abstraction the codebase lacks**, unless
   asked: no `services/` beside `crud.py`, no generic repository, no
   second `errors.py`.
4. **Imports point one way**, from the edge inwards. A cycle is fixed by
   moving code, never by a function-level import.
5. **No database model crosses the HTTP boundary**, in or out.
6. **Services know no HTTP**: no `fastapi` import, no `HTTPException`.
7. **One owner per transaction**: the service, through a unit of work.
   Repositories flush, never commit.
8. **One translation per boundary**: driver error to domain error in the
   repository, `from` the original; domain error to response in one
   handler per category.
9. **Wire with `Depends`, swap with overrides keyed by the provider the
   route names.** Never patch a global.
10. **A custom error only when something catches it by type.** Otherwise
    a built-in. Its fields go to `super().__init__` in order.
11. **Checked by running**: the tests, with a fake and, when one is
    reachable, a real database. Quote the summary line.

## What you say when you finish

End with these headings, each with `none` when empty. If another skill
is loaded, its headings come first and these after.

```
## Structure
<the card lines you relied on: layout, the traced request, where models,
wiring, transactions and errors live; for a placement, the precedent's
path:line or "no precedent, default used, convention started">

## Result
<files added or changed, each with the card line or rule that placed it;
for a check, findings by ID with path:line and a verdict>

## Checked
<each command run and its summary line, such as "13 passed in 1.5s";
which tests used a fake and which a real database>

## Not checked
<databases not reachable (PostgreSQL, a replica set), callers not
searched, versions not tried>
```

The `evals/` folder is for people testing this skill. Never open it
while doing a task.
