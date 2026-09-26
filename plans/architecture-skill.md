# Plan: the architecture skill

Status: built on `claude/skill-architecture` (`skills/architecture/`).
The decisions below were taken as their recommended defaults (section
10); sections 11 and 12 record how it was verified and what the lab
changed.

## 1. What it is

How a Python backend service is put together, FastAPI first: the layers
(router, service, repository or DAL, then the ORM or ODM), what each may
and must not do, how they are wired, which model lives at each boundary,
who owns a transaction, and how an error changes shape on its way out.
It covers the common layouts (by layer, by feature, hexagonal or clean)
and, above all, how to recognise the structure a codebase already uses,
so new code follows that codebase and not a textbook.

It also works one level down: where a single new thing goes (an
exception, a constant, an enum, a helper, a type), whether it joins an
existing file or earns a new one, and when a custom exception is worth
defining at all, with which fields. The rule is the same at both levels:
precedent in the codebase first, defaults only where there is none.

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
| **Place a thing** | add one exception, constant, enum, helper, type or provider | its path; the precedent (`path:line` of its nearest sibling of the same kind) or "no precedent, default used, convention started"; the rule applied |
| **Models** | separate or map request, response, domain and database models | the classes, where mapping lives, a test that a hidden field stays hidden |
| **Wire** | inject or swap a service or repository, including in tests | the provider functions, the `Depends` chain, the override and its test |
| **Transaction** | make several writes atomic, or decide who commits | the owning layer, the unit of work, a test that shows the rollback |
| **Errors** | design custom exceptions, or turn database errors into domain errors and HTTP responses | whether a built-in fits; the hierarchy and where it lives; each class's fields; where each is raised and caught; a test per status code |
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
| **A new file per thing** | `order_not_found_error.py`; a new `errors.py` beside an existing `exceptions.py` |
| **Placed at first use** | the exception defined in the service that first raises it while the codebase keeps them in `errors.py`; the router then imports it from the service |
| **Grab-bag module** | a helper appended to a 900-line `utils.py`, or a new `helpers.py` or `common.py` |
| **Custom error for everything** | `InvalidInputError` where `ValueError` fits; one class per message rather than per handling |
| **Errors nobody can catch** | `raise Exception("not found")`; a caller parses `str(e)` to tell two cases apart |
| **Broken exception class** | `__init__` without `super().__init__`, so `str(e)` and the log line are empty; keyword-only fields, so it fails to pickle in a worker and the real error is lost |

## 5. Layout

```
skills/architecture/
  SKILL.md              router over the eleven kinds, invariants, answer headings
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
  placement/
    place-a-thing.md       name the kind, find the precedent, else the default
    new-or-existing.md     when a new file earns its place; names to avoid
    defaults.md            the table for a codebase with no precedent
    custom-errors.md       when to define one, the hierarchy, where, its fields
    constants-and-enums.md module constants, StrEnum, when a value is a setting
    helpers.md             private first, then a module named for what it does
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

## 5a. Placement: where one new thing goes, and custom errors

Layers decide the folder; placement decides the file. Asked to add an
exception, a constant or a helper, a weak model either makes a new file
for it or defines it where it first needs it, whatever the codebase
already does. `placement/` answers one thing at a time.

**The procedure (`place-a-thing.md`).**

1. Name the kind: exception, constant, enum, type alias or Protocol,
   helper, settings field, schema, dependency provider.
2. Find the precedent: search for siblings of that kind (for example
   `class \w+(Error|Exception)\(`, `^[A-Z][A-Z0-9_]+ =`,
   `class \w+\((Str)?Enum\)`) and note where they live and how the files
   are named (`errors.py` or `exceptions.py`; one per feature or one per
   package).
3. Precedent wins over the defaults, even when the default is better.
   Say so in the answer when it matters; do not migrate unasked.
4. No precedent: use the default table, and say a convention was started.
5. Answer with the path, the precedent's `path:line` or "no precedent",
   and the rule used.

**New file or existing file (`new-or-existing.md`).** Join the existing
file when one already holds this kind at this level (the feature or the
package). A new file earns its place only when the kind has no home at
this level and the codebase gives kinds their own files, or when joining
would mix two layers or two features in one file. Never: one file per
class; a new `utils.py`, `helpers.py` or `common.py`; a second home for a
kind that has one (`errors.py` beside `exceptions.py`). A circular import
after placing something is a sign it was placed in the wrong layer, not a
reason for a local import.

**Defaults, with no precedent (`defaults.md`).**

| Kind | Default home | Moves when |
| --- | --- | --- |
| exception | the feature's `errors.py`; base and categories in the package's `errors.py` (or `core/errors.py`) | never next to its first raiser |
| constant | module level, `UPPER_CASE`, in the one module that uses it | a second module needs it: the feature's `constants.py`; it differs by environment: it is a setting (pydantic) |
| enum | the feature's domain or schemas module; `StrEnum` when it crosses the wire | two features share it: the shared package |
| type alias, Protocol | beside the code that depends on it (a repository Protocol beside its service) | two consumers: the shared package |
| helper | private (`_name`) in the module that uses it | a caller in another module: a module named for what it does (`money.py`, `slugs.py`) |
| provider for `Depends` | the feature's `dependencies.py` | shared by features: the shared package |

**Custom errors (`custom-errors.md`, with `core/errors.md`).**

*When to define one.* Only when something will catch it by type or
translate it: a caller handles it differently from other failures (404 or
409, retry or give up); it crosses a layer boundary and is translated
once there (L8); or its handler needs data from it (which id, which
limit). Otherwise raise a built-in: `ValueError` for a bad argument,
`TypeError`, `LookupError` or `KeyError`, `NotImplementedError`,
`PermissionError`, `TimeoutError`. Never bare `Exception`. One class per
distinct handling, not one per message.

*The hierarchy.* One base per application or library (`AppError`); a few
categories the HTTP edge maps to a status (`NotFoundError` 404,
`ConflictError` 409, `PermissionDeniedError` 403); specific classes only
where a caller needs them (`OrderNotFoundError(NotFoundError)`). api
registers one handler per category, so a new specific error needs no new
handler (a handler for a base class catching subclasses: to verify in the
lab on FastAPI 0.141.1). Domain errors never subclass `HTTPException`.
Names end in `Error` (PEP 8) unless the codebase says otherwise.

*Where.* Base and categories in one shared module; specific errors in
their feature's `errors.py`, or the domain layer's in a layered layout; a
library re-exports its public errors from `__init__.py`. Driver errors
(`DuplicateKeyError`, `IntegrityError`) never leave the repository.

*Its fields.* Structured attributes for what a handler needs
(`order_id`, `limit`), and a readable `str(e)` for logs. Checked while
planning, on Python 3.11.15 and 3.12.3:

- `__init__` without `super().__init__(...)`: `str(e)` is `''` and
  `args` is empty, so the log line says nothing.
- `__init__` whose signature does not match `self.args` (keyword-only
  fields with a formatted message is the usual way): `pickle` and
  `copy.deepcopy` raise `TypeError`, so the error breaks in
  multiprocessing, `ProcessPoolExecutor` or a task queue, and the real
  error is lost.
- Positional fields passed to `super().__init__(*fields)`, with the
  message built in `__str__`, pickle, copy and print correctly.
- A `@dataclass` exception pickles, but is unhashable (`eq=True` sets
  `__hash__` to `None`).

A class-level `code = "order_not_found"` gives a stable machine-readable
code that api can put in a problem-details `type`. No secrets or personal
data in fields or messages: they reach logs. The message is built inside
the class, not at every raise site.

*Raising.* `raise DomainError(...) from exc` at a translation point;
`from None` only when the cause would leak internals; catch the narrowest
class; `except Exception` only at the outermost edge; `e.add_note(...)`
(3.11 and later) to add context without a new class.

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
- **Custom errors** are architecture's: when to define one, the
  hierarchy, where it lives, its fields. **api** owns the handlers, the
  status code and the response body. **pydantic** owns errors raised
  inside validators and `ValidationError`. **linting** owns the ruff
  rules that catch some of this (N818, TRY002, TRY003, EM101, EM102,
  B904, BLE001; all present in ruff 0.15.8), and runs them only where the
  project enables them; architecture never enables a rule unasked.
- **Constants that differ by environment** are settings, owned by
  pydantic's settings part; architecture only says when a constant has
  become one.

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
| L10 | thing placed against precedent | a new definition of a kind in a file where no sibling of that kind lives, while one exists elsewhere; a second `errors.py`, `utils.py` or `constants.py` |
| L11 | exception that cannot be handled well | `raise Exception(`; `except` blocks that test `str(e)`; `__init__` without `super().__init__`; keyword-only fields; `HTTPException` subclassed in the domain |

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
4. A boundary row for custom exceptions: architecture owns when, the
   hierarchy, placement and fields; api the handler and response; pydantic
   validator errors; linting the rules that flag them.

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
- Rerun the exception probes of section 5a on the pinned Python and
  record the output in `custom-errors.md`; record that a FastAPI handler
  registered for a base class catches a subclass, and in what order two
  matching handlers are chosen; check each ruff rule named in section 6
  exists in the pinned ruff.
- Run each placement search on the recipes and sandboxes, and record the
  kinds it misses (errors defined inside functions, re-exported names).
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
| `errors-precedent` | return 404 when an invoice is missing | the project has `billing/errors.py` under a shared `AppError` and one 404 handler; a new `exceptions.py`, an error in the service, or a new handler |
| `builtin-fits` | reject a negative quantity in `parse_quantity()` | a pure function; a new `InvalidQuantityError` hierarchy where `ValueError` fits |
| `worker-pickle` | a worker logs `TypeError: __init__() missing 1 required keyword-only argument` | a custom exception with keyword-only fields fails to unpickle; "fixed" by catching `TypeError` |
| `utils-dump` | add a slug helper used by two features | a 900-line `utils.py` invites one more function |
| `no-precedent` | add the first custom error to a small app | must say there is no precedent, create one `errors.py` with a base and one category, and say a convention was started |
| `constant-or-setting` | make the page size 50 in production and 10 in tests | a module constant edited, or a second constant, where it has become a setting |

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

*Decided:* PostgreSQL with asyncpg for the recipes, aiosqlite for the
evals so they run anywhere. No PostgreSQL version is assumed: the
patterns here are SQLAlchemy's, and where a task depends on the server,
the skill reads it (`SELECT version()`, or the image tag in the compose
file or chart).

### AR7. Severity, and tools that enforce layers

*Recommended:* each checklist item suggests a severity on code-review's
scale, which code-review owns (to agree with its plan). The checklist's
searches are the default check; an import-linter contract appears in the
recipes as optional, for projects that already have the tool.

### AR8. Placement here, or a separate Python structure skill

Placement applies to CLIs and libraries too, not only backends.
*Recommended:* here, since it is the same recognise-then-follow rule at
file level, and custom errors already meet the error translation owned
here. The description widens to "code structure, from a single file to a
service"; a project without layers uses `placement/` and `layouts.md`
alone. Split it out only if non-backend projects become the common case.

### AR9. The form of an exception's fields

*Recommended:* positional fields passed to `super().__init__(*fields)`,
the message built in `__str__`, an optional class-level `code`. Taught
for reading: keyword-only fields with a `__reduce__`, and `@dataclass`
exceptions (fine to pickle, unhashable). *Decided:* in a codebase that
already defines exceptions, the form its nearest sibling uses wins
(placement's precedent rule); the recommended form is only for a
codebase with none, or for fixing one that breaks pickling.

### AR10. Error file names and granularity

*Recommended, with no precedent:* `errors.py`, one per feature, with the
base and categories in the package's shared `errors.py`. With a
precedent, the precedent, including `exceptions.py` or one central file.

## 10. Decisions taken as defaults

- **AR1.** One skill; folders `beanie/` and `sqlalchemy/`.
- **AR2.** By feature for a new service (`core/design.md`), with a
  smaller flat layout when the requirements allow; by layer taught for
  recognising; hexagonal only for a port with two adapters.
- **AR3.** Domain models as frozen pydantic models apart from the
  schemas in new code; a codebase that uses the `Document` or row as its
  domain model is a card exception, and the hard rule stays (L3).
- **AR4.** The service owns the transaction through a unit of work;
  commit-after-yield accepted where the card shows it, with
  `scope="function"` (the lab showed why, section 12).
- **AR5.** Verified on SQLAlchemy 2.1.1; the SQL recipe also passed on
  2.0.54. SQLModel gets a reading note (`sqlalchemy/sqlmodel.md`).
- **AR6.** PostgreSQL with asyncpg for the recipes, aiosqlite for the
  evals. No PostgreSQL server could be run in the lab (section 11), so
  the recipes ran on aiosqlite and every PostgreSQL fact is read in
  source and marked *not run on PostgreSQL*. No server version is
  assumed; a task that depends on it reads it.
- **AR7.** Each checklist item suggests a severity on code-review's
  scale (blocker, major, minor, nit, from its plan's CR1); the searches
  are the default check; import-linter contracts appear in the recipes
  as optional.
- **AR8.** Placement lives here; the description says "from one new
  file to a FastAPI service".
- **AR9.** Positional fields passed to `super().__init__(*fields)`, the
  message in `__str__`, an optional class-level `code`; keyword-only
  with `__reduce__` and `@dataclass` exceptions taught for reading. A
  codebase's own form, found by the precedent search, wins.
- **AR10.** `errors.py`, one per feature, base and categories in the
  package's shared `errors.py`; the precedent wins where one exists.

## 11. How it was verified

- **Versions.** Python 3.12.14 (exception probes also on 3.11.15;
  3.10.20 to confirm `StrEnum` and `add_note` are missing there),
  FastAPI 0.141.1 with Starlette 1.7.0, pydantic 2.13.5, pytest 9.1.1,
  Beanie 2.2.0 on PyMongo 4.18.2, SQLAlchemy 2.1.1 (and 2.0.54) with
  greenlet 3.5.6, aiosqlite 0.22.1, asyncpg 0.31.0 (installed, source
  read), ruff 0.16.9, import-linter 2.15, SQLModel 0.0.47 on SQLAlchemy
  2.0.54, httpx2 2.13.1. All installed with uv from the public index.
- **Servers.** MongoDB 8.0.32 as a single-node replica set on its own
  port and dbpath. PostgreSQL 16 packages were present, but the
  container's `/dev/null` is a regular file owned by root, so `initdb`
  run as the `postgres` user failed (`sh: 1: cannot create /dev/null:
  Permission denied`); repairing `/dev/null` or running PostgreSQL in a
  private mount namespace was refused by the session's permission
  policy. Nothing was run on PostgreSQL.
- **Recipes.** Both run in fresh copies: SQL 13 passed (SQLite); Beanie
  15 passed with the replica set, 9 passed and 6 skipped without it.
  Mutants (translation removed, a secret field in the response schema, a
  commit in the repository, the transaction removed from the service,
  from the unit of work, `session=` removed) each failed a test; two
  equivalent mutants are recorded in `recipes/README.md`. ruff (E, F, I,
  B, UP, N, TRY, EM, BLE, PLC0415) and `ruff format --check` clean;
  `lint-imports` 2 contracts kept, and broken as expected when a
  service imported `fastapi` or a repository imported a schema.
- **Shapes.** `shapes/check_shapes.py` ran all eleven: 22 of 22 sides
  passed; the after-only tests of L5 and L7 fail on their befores.
- **Checklist and placement searches.** Run with ripgrep (the same regex
  engine as Zed's `grep`) over both recipes and all fifteen sandboxes,
  and over baited copies of three sandboxes: the recipes had no hits
  except the Beanie unit of work's own `start_session(` (allowed); each
  bait line was hit; what each search misses is in
  `checklist/finding.md` and `placement/place-a-thing.md`.
- **Evals.** 16 scenarios over 15 sandboxes, written before the
  procedures. Each bait was reproduced and each intended fix passed
  (review-diff and new-service are judged from the answer: their baits
  were checked through the searches and the recipes' layout).
- **Not run.** PostgreSQL; Windows and PowerShell (commands written in
  PowerShell form are marked *not run on Windows*); Zed's own `grep`
  tool (the multiline route search ran with ripgrep `-U` only).

## 12. What the lab changed

Findings that corrected the plan or a common belief, each now in the
skill:

- **An `__init__` without `super().__init__` does not leave `str(e)`
  empty** when it takes positional arguments: `BaseException.__new__`
  stores them, so `str(e)` is `'7'` or `'(7, 100)'`, not the message.
  It is empty only with keyword-only fields. The plan's section 5a said
  otherwise (`placement/custom-errors.md`).
- **An unpicklable error does not just raise `TypeError`**: through
  `ProcessPoolExecutor` the caller got `BrokenProcessPool` and the real
  error was lost; through `multiprocessing.Pool.apply` the call never
  returned. Passing positional fields but only a formatted message to
  `super().__init__` fails too (`missing 1 required positional
  argument`).
- **A Beanie 2.2.0 `Document` cannot be built before `init_beanie`**
  (`CollectionWasNotInitialized`), so the plan's "most sandboxes need no
  database" does not hold for Beanie models: users-beanie needs a server,
  and fakes return domain models, which is the practical case for AR3.
- **A returned `Document` sends `_id`, and a missing one is `200
  null`**; a `Document` body lets a client set `_id` as well as
  `is_admin`.
- **`MissingGreenlet` arrives wrapped**: `StatementError` around it,
  and in a route a pydantic `get_attribute_error` inside
  `ValidationError` or `ResponseValidationError`, so `except
  MissingGreenlet` would not even catch it.
- **SQL writes need the unit of work even for one row**: without
  `transaction()` the insert was never committed; `begin()` after any
  read fails (`A transaction is already begun on this Session.`).
- **Commit-after-yield with the default scope answered 201 for a row
  that was not stored**, rerun with SQLAlchemy (the api skill's timing
  finding, applied to AR4).
- **A Mongo single-document use case should not open a transaction**,
  so the two recipes' services differ in which use cases call
  `transaction()`; the plan assumed one service shape for both.
- **A Beanie call without `session=` escapes the transaction**, while
  PyMongo 4.17's `AsyncClientSession.bind()` makes calls without it
  join; Beanie keeps a find's session for the chained update.
- **Handler choice**: a handler for a base class catches subclasses and
  the nearest class in the MRO wins regardless of registration order
  (Starlette 1.7.0), confirming "one handler per category".
- **ruff's `TRY003` and `EM101`/`EM102` fire on built-in exceptions
  too**: style rules, not a reason for a custom class.
- **SQLModel 0.0.47 cannot be installed with SQLAlchemy 2.1** (it pins
  `<2.1.0`), and a table model as body and response leaked
  `password_hash` and accepted `is_admin`.
- **import-linter's layer order matters**: with `schemas` listed below
  `repository`, a repository importing a schema passed; `"schemas |
  dependencies"` as the second layer caught it.
- **`pytest.skip(allow_module_level=True)` in a tests `conftest.py`
  aborts the run** (exit 1) on pytest 9.1.1; the Mongo skip moved into a
  fixture.
- **uv picked CPython 3.14.7** for a project with `requires-python =
  ">=3.12"`; both recipes passed there too.
- **The checklist grew no IDs**: L1 to L11 held for every bait; L10 and
  L11 are found partly by the placement searches and by reading.
- **An after must pass the linting checks too.** Refactoring's replay
  found the L3 and L6 afters added mypy findings (`union-attr` on the
  missing user, `arg-type` on `dict[str, object]` rows), and L3's after
  dropped `get_session`, so a test's override of it was silently unused.
  L3 now chains `get_users` on `get_session` and raises on a missing user
  (still a 500, said beside the shape); L6 types its raw rows with
  `TypedDict`s; `check_shapes: 22 of 22 sides passed`.

