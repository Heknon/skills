# Plan: the architecture skill

Status: draft for decision. Nothing is built yet.

## 1. What it is

How a Python backend service is put together, FastAPI first: the layers
(router, service, repository or DAL, then the ORM or ODM), what each may
and must not do, how they are wired, which model lives at each boundary,
who owns a transaction, and how an error changes shape on its way out.
It covers the common layouts (by layer, by feature, hexagonal or clean)
and, above all, how to recognise the structure a codebase already uses,
so new code follows that codebase and not a textbook.

It hands code-review a checklist of layering violations with stable IDs,
and refactoring a target shape per violation. `beanie/` and
`sqlalchemy/` hold the repository pattern for each. It carries knowledge
and judgement, not enforcement.

## 2. The environment it is written for

- **A weak model in Zed's agent on Windows**, PowerShell locally, air
  gapped, Python through uv, packages only from the internal mirror, no
  web. Every class, argument and default is stamped with its version.
- **Existing codebases first.** Most tasks land in a service someone else
  structured, often unevenly. The skill reads before it prescribes.
- **No new packages.** Layers are built from FastAPI, pydantic, Beanie or
  SQLAlchemy. import-linter is used only if the project already has it.
- **Tests without a database where possible**: a fake repository for a
  service, an override for a route. A real database may be out of reach.

## 3. The kinds of task

| Kind | Asked to | Answer shape |
| --- | --- | --- |
| **Recognise** | explain how this service is structured; also the first step of any change | a structure card: layout style, one request traced router to database as `path:line` hops, where models, wiring, transactions and error translation live |
| **Place** | add an endpoint or feature | the files added or changed, each placed by a line of the card, and the tests run |
| **Models** | separate or map request, response, domain and database models | the classes, where mapping lives, a test that a hidden field stays hidden |
| **Wire** | inject or swap a service or repository, including in tests | the provider functions, the `Depends` chain, the override and its test |
| **Transaction** | make several writes atomic, or decide who commits | the owning layer, the unit of work, a test that shows the rollback |
| **Errors** | turn database errors into domain errors and HTTP responses | the exception classes, where each is raised and caught, a test per status code |
| **Repository** | write or fix a repository over Beanie or SQLAlchemy | the repository, what it returns, its tests with a fake and a real database |
| **Check** | check a change or codebase for layering violations | findings by checklist ID with `path:line`, what the card allows, a verdict |
| **Shape** | describe the target structure for moving some code | the shape from `shapes/` and the test both sides pass; the steps are refactoring's |
| **Design** | lay out a new service | the smallest layout that fits, the reason, what would change it |

## 4. The failures it targets

| Failure | What it looks like |
| --- | --- |
| **Textbook over codebase** | adds `services/` and `repositories/` to a project that uses `crud.py` per feature, or ports and adapters to a three-file app |
| **Query in the route** | `await User.find_one(...)` or `session.execute(select(...))` inside the path operation |
| **Logic in the router** | discount rules or state checks in the route; the CLI then copies them |
| **Database model in the response** | returns a Beanie `Document` or ORM row, so `password_hash` reaches the client; a `Document` as request body lets a client set `is_admin` |
| **Service knows HTTP** | imports `fastapi`, raises `HTTPException`, takes a `Request`; a worker cannot call it |
| **Split transaction** | every repository method commits, the route commits too; a transfer half applies when the second write fails |
| **Session per call** | a repository opens its own session per method, so two calls cannot share a transaction |
| **Raw data from the repository** | returns `dict`, a Mongo document with `_id`, a cursor or a `Select`; callers index by string keys |
| **Untranslated errors** | a duplicate key becomes a 500; a broad `except Exception` becomes a 404; the repository raises `HTTPException` |
| **Unswappable dependency** | a repository built at module level or in the route; tests patch a global, or override a key the route never uses |
| **Circular layers** | `models` imports `schemas` imports `services`; "fixed" by moving imports into functions |
| **Async loading after commit** | an ORM row serialised after commit, or a lazy relationship, raises `MissingGreenlet` (text to verify in the lab); "fixed" by a sync route |
| **Layers for their own sake** | a generic `BaseRepository[T]` nobody needs; a forwarding service layer the codebase never had |

## 5. Layout

```
skills/architecture/
  SKILL.md              router over the ten kinds, invariants, answer headings
  glossary.md           layer, repository, DAL, domain model, unit of work, port
  core/
    recognise.md card.md   read the codebase; the structure card and an example
    place.md design.md     where new code goes; a layout for a new service
    layers.md              what each layer may and must not do
    layouts.md             by layer, by feature, hexagonal, clean: signs, fit
    boundary-models.md     schema, domain, document or row; where mapping lives
    wiring.md              Depends as wiring; providers; swapping in tests
    transactions.md        who owns it; unit of work; one session per request
    errors.md              database to domain to HTTP; once per boundary
  checklist/
    violations.md          ID, rule, why, suggested severity, shape
    finding.md             a search per ID, what it misses, card exceptions
  shapes/                  per ID: before, after, and a test both pass
  beanie/                  repository.md sessions.md errors.md testing.md
  sqlalchemy/              session.md repository.md unit-of-work.md
                           loading.md errors.md sqlmodel.md (optional note)
  recipes/                one service over Beanie, one over SQLAlchemy, tested
  examples/                recognise a crud layout; check a leaky change
  evals/                   evals.json and sandboxes/
```

Invariants: recognise first and follow the card; imports point one way;
no database model crosses the HTTP boundary; services know no HTTP; one
owner per transaction; one error translation per boundary; wire with
`Depends`, swap with overrides, never patch globals; add no layer the
codebase lacks unless asked. Answers end with `## Structure` (the card
lines relied on), `## Result`, `## Checked`, `## Not checked`.

## 6. Dependencies and boundaries

From the roadmap:

| Skill | Needs | Relies on by name | Existing skills it touches |
| --- | --- | --- | --- |
| architecture | pydantic, api, mongodb | api, mongodb, pydantic | pytest (swapping dependencies in tests) |

- **pydantic** owns what a model means (`from_attributes`, `model_dump`);
  architecture decides which model sits at which boundary.
- **api** owns `Depends` mechanics and the request and response models;
  architecture owns injection as the wiring of layers, and keeping those
  models apart from domain and database models.
- **mongodb** owns Beanie and every Mongo fact; architecture owns the
  repository around it. **code-review** and **refactoring** turn the
  layering rules owned here into findings and recipes.

The checklist's first draft (the lab may split or merge items):

| ID | Violation | Found by, first try |
| --- | --- | --- |
| L1 | route queries the database | Beanie or `session.` calls in router files |
| L2 | business logic in a router | branches on domain state; several repositories in one route |
| L3 | database model in a response or request body | a route returns or accepts a `Document` or ORM class |
| L4 | service knows HTTP | `fastapi`, `starlette` or `HTTPException` imported in services |
| L5 | transaction split across layers | `commit(` outside the unit of work; a session per method |
| L6 | repository returns raw data | `-> dict`, aggregation output passed on, `get_pymongo_collection()`, a `Select` |
| L7 | imports point up or round | a lower layer imports a higher one; an import cycle |
| L8 | database error untranslated or translated twice | driver errors reach routes; `HTTPException` in a repository |
| L9 | dependency not swappable | a repository or client built at module level or in the route |

**Hand-off to code-review.** Code-review loads `checklist/violations.md`
and cites findings by ID with `path:line`. It runs `core/recognise.md`
first, so what the card allows (no service layer in a small app) is not
a finding. Each item suggests a severity; code-review owns the scale.
IDs are stable, and `violations.md` carries a version line.

**Hand-off to refactoring.** Each ID names one file in `shapes/`: before,
after, and a test that passes on both. Architecture states the end state,
never the steps; refactoring owns the steps, each checked, in recipes
named by the same IDs.

**Proposed changes to the roadmap** (not edited here):

1. Add navigation to "Existing skills it touches": `recognise.md` uses
   its Follow and Trace procedures and `python/entry-points.md`.
2. New boundary rows. *SQLAlchemy facts* (sessions, loading, errors):
   nothing owns them, so architecture does until a SQL skill exists;
   migrations (Alembic) have no owner. *Transactions*: mongodb owns Mongo
   mechanics (replica set, sessions); architecture owns which layer
   commits. *Error responses*: api owns handlers, status codes and the
   body; architecture owns the domain errors and where each is
   translated. *Layer contracts as tool config* (import-linter, ruff
   banned imports): architecture owns the rules; linting runs the tool.
3. Split the pytest touch: api owns `dependency_overrides` mechanics,
   architecture which layer a test fakes, pytest the fixture that sets
   and clears the override.

## 7. How it will be verified

Versions (to agree across plans, roadmap R2), found on the public index
while planning and to confirm in the mirror: Python 3.12, FastAPI
0.141.1, pydantic 2.13.5, pytest 9.1.1; Beanie 2.2.0 on PyMongo 4.18.2
(its wheel requires `pymongo`, not `motor`, and imports
`pymongo.asynchronous`; its test extra pins `fastapi<0.130`, so that it
works with 0.141 is to verify in the lab); SQLAlchemy 2.1.1 with the
`asyncio` extra (its metadata lists `greenlet` only there), asyncpg and
aiosqlite from the mirror; SQLModel 0.0.47 for the note only; MongoDB
and PostgreSQL servers as AR6 and the mongodb plan decide.

The lab must:
- Run both recipes' tests with fakes and overrides and no database, then
  their repositories against a real mongod (a single-node replica set,
  since Mongo transactions need one) and a real PostgreSQL.
- Run each checklist search on the recipes (no hits) and the sandboxes
  (a hit on each bait line), and record what each search misses. Run
  every shape's before and after against its test.
- Record, not recall: what a returned Beanie `Document` serialises to
  and whether `response_model` strips its extra fields;
  `Depends(scope=...)` (in 0.141.1, `"function"` or `"request"`): when a
  commit after `yield` runs relative to the response, and what the client
  sees if it fails; the `MissingGreenlet` message and the access that
  raises it; the exception classes for a duplicate key in PyMongo and a
  unique violation in SQLAlchemy on asyncpg and on aiosqlite.
- Reproduce every eval's bait and pass every intended fix.

## 8. Evals, written first

Sandboxes are uv projects with a FastAPI app and tests. Most need no
database; *sqlite* marks the ones that use aiosqlite.

| Sandbox | Task given | Bait |
| --- | --- | --- |
| `crud-by-feature` | add an endpoint to archive a project | the code uses `projects/{router,crud,schemas}.py`; a textbook adds `services/` |
| `leaky-user` | add `GET /users/{id}` | returning the Beanie `User` leaks `password_hash` |
| `mass-assign` | add `PATCH /users/me` | a body typed as the `User` document lets a client set `is_admin` |
| `credit-limit` | reject orders over the credit limit with 409 | `HTTPException` in a service that a worker also calls |
| `transfer` (*sqlite*) | a transfer sometimes loses money | each repository commits; a `try` in the route does not fix it |
| `wrong-override` | the route test hits the real repository | the test overrides the class; the route depends on `get_repo` |
| `lazy-after-commit` (*sqlite*) | `POST /orders` returns 500 | `MissingGreenlet`; "fixed" by a sync route or an `except` |
| `review-diff` | check this change's layering | L1, L6 and L8 are real; a forwarding service the card allows is not |
| `circular` | fix the `ImportError` at start-up | `models` and `schemas` import each other; a local import hides it |
| `new-service` | lay out a service with two endpoints | ports, adapters and a generic repository for two endpoints |

Graded from the answer and the diff: the card came first, the change
follows it, the test run is quoted, the answer ends with the headings.

## 9. Decisions needed

### AR1. One skill, and the folder names

*Recommended:* one skill, as the rules are shared; `beanie/`, not
`mongo/`, since Mongo itself belongs to the mongodb skill.

### AR2. Default layout for a new service

*Recommended:* by feature, each with `router.py`, `service.py`,
`repository.py` and `schemas.py`, and a shared `db/`. By layer is taught
for recognising; hexagonal only when one port has several adapters.

### AR3. What a repository returns, and what domain models are

*Recommended:* domain models in new code, as pydantic models kept apart
from the schemas (dataclasses are taught for reading). Where a codebase
uses the `Document` or row as its domain model, accept it and keep the
hard rule: no database model in a response or request body.

### AR4. Who owns the transaction

*Recommended:* the service, through a unit of work it enters explicitly.
A request-scoped session that commits after `yield` is accepted where the
codebase uses it, once the lab shows when that commit runs.

### AR5. SQLAlchemy 2.1 or 2.0, and SQLModel

The ask says "2.0", meaning the 2.0-style API, which 2.1 keeps.
*Recommended:* verify on 2.1.1 and note where 2.0.x differs, unless the
mirror has only 2.0. SQLModel gets a reading note, not a recipe: one
class as table and schema invites the leak L3 forbids.

### AR6. SQL database for the lab

*Recommended:* PostgreSQL with asyncpg for the recipes, aiosqlite for
the evals so they run anywhere. Which PostgreSQL version does the team
run?

### AR7. Severity, and tools that enforce layers

*Recommended:* each checklist item suggests a severity on code-review's
scale, which code-review owns (to agree with its plan). The checklist's
searches are the default check; an import-linter contract appears in the
recipes as optional, for projects that already have the tool.
