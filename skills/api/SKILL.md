---
name: api
description: Design HTTP APIs and build them with FastAPI. Name resources and choose methods and status codes, PUT against PATCH (merge patch, omitted against null), one error shape (RFC 9457 problem details), pagination with stable cursors, filtering and sorting, idempotency keys, ETag and If-Match against lost updates, breaking and non-breaking changes, deprecation and versioning, reviewing an API or an OpenAPI diff. In FastAPI: where a parameter comes from (path, query, header, body, embed), response_model and return types that filter output, APIRouter and route order, Depends (sub-dependencies, the per-request cache, yield teardown and scope, dependency_overrides), lifespan and app.state, exception handlers and validation errors, middleware order, BackgroundTasks, async def against def and blocking calls, reading /openapi.json offline when /docs is blank, testing with TestClient and httpx. Explain an unexpected 422, a missing field or a handler that is not called. Verified on FastAPI 0.141.1 and 0.118.0, Starlette 1.7.0 and 0.48.0, pydantic 2.13.5.
---

# API

This skill knows how an HTTP API should behave (the contract, in
`core/`, framework agnostic) and how FastAPI and Starlette actually
behave (`fastapi/`). Every FastAPI name, default, status and message in
it was run in a lab on FastAPI 0.141.1 with Starlette 1.7.0, and on
0.118.0 with Starlette 0.48.0 where they differ. Contract rules quote
the RFCs. Nothing is written from memory: FastAPI changes between
minor releases. Find the fact here, in the app's own `/openapi.json`,
or in the installed source (the offline-docs skill says how to read it).

Read this file, then load only what the task needs.

## Read the versions first

```
uv pip show fastapi starlette pydantic httpx httpx2 uvicorn
```

It prints `Name:` and `Version:` for each and a warning line for any not
installed. FastAPI does not pin Starlette's upper bound from 0.133, so
read both. `fastapi/versions.md` lists what differs between the two
lines this skill ran; check it before writing anything version shaped
(`Depends(scope=...)`, `strict_content_type`, security status codes).
Run everything through uv (`uv run --no-sync python`, `uv run pytest`).

## The kinds of task

| Kind | You were asked to | Load |
| --- | --- | --- |
| **Design** | design an endpoint or a resource | `core/design.md`, then the `core/` files it names |
| **Evolve** | rename, add, remove, tighten, version | `core/compatibility.md`, `fastapi/openapi.md` |
| **Lists** | paginate, filter or sort a collection | `core/pagination.md`, `core/filtering-sorting.md` |
| **Errors** | an error shape, handlers, validation errors | `core/errors.md`, `fastapi/errors.md` |
| **Retries** | make a write safe to retry, stop duplicates or lost updates | `core/idempotency.md`, `core/put-and-patch.md` |
| **Update** | write or fix a PUT or PATCH | `core/put-and-patch.md`, `fastapi/parameters.md` |
| **Endpoint** | write or change a FastAPI route | `fastapi/parameters.md`, `fastapi/responses.md`, `fastapi/routing.md` |
| **Depends** | write, share, cache, tear down or override a dependency | `fastapi/dependencies.md` |
| **Lifecycle** | lifespan, middleware, background tasks | `fastapi/lifespan.md`, `fastapi/middleware.md`, `fastapi/background.md` |
| **Concurrency** | an endpoint stalls; `async def` or `def` | `fastapi/concurrency.md` |
| **Test** | test an API | `fastapi/testing.md` |
| **Explain** | an unexpected 422, a missing field, a handler not called, a blank `/docs` | `fastapi/debug.md` |
| **Review** | review an API, an endpoint or an OpenAPI diff | `core/review.md` |
| **Structure** | services, repositories, a DAL, dependency injection as wiring, Beanie | not here: see below |

**Structure** belongs to other skills. Where a service or repository
goes, how layers are wired and swapped, and keeping request models apart
from domain and database models are the architecture skill's; Beanie and
queries are the mongodb skill's. Load them. If they are not installed,
say so, keep the HTTP contract unchanged, and answer only the api part.

## Where the facts are

| Folder | Holds |
| --- | --- |
| `core/` | the contract: design and review procedures, naming, methods and status codes, PUT and PATCH, errors, pagination, filtering and sorting, idempotency, compatibility |
| `fastapi/` | parameters, responses, routing, dependencies, lifespan, errors, middleware, background tasks, concurrency, OpenAPI, testing, debugging, versions |
| `recipes/` | `service/`: a small complete service (problem details, cursor pages, an idempotent POST, a PATCH with If-Match, tests); `tools/`: `openapi_dump.py` and `stall_check.py`. All ran. |
| `examples/` | three finished tasks: a PATCH that reset fields (`patch-that-reset.md`), a breaking rename avoided (`breaking-rename.md`), a stall found (`stall-found.md`) |

`glossary.md` fixes the words. Other skills own neighbouring ground:
pydantic (models, `ValidationError`, partial models and `apply_patch`),
mongodb (the stored write, keyset queries, indexes), architecture
(layers, what is injected), pytest (running tests, fixtures),
observability (whether a 404 is an error in a trace), deployment
(probes, workers, shutdown timeouts), navigation (finding the app and
its routes), linting (ruff's `FAST` rules), offline-docs (reading
installed source).

## Invariants

1. **The status code carries the outcome.** Never 200 with an error in
   the body; a client error is 4xx, a 5xx is never the answer to bad
   input (`core/methods-and-status.md`).
2. **Every response is declared.** A return annotation or
   `response_model` names a model; a stored record is never returned
   raw (`fastapi/responses.md`).
3. **PUT replaces, PATCH merges.** In a PATCH an omitted field stays and
   `null` clears it; the body is dumped with `exclude_unset=True` and the
   merged result is validated with the full model
   (`core/put-and-patch.md`).
4. **A change a client can notice breaks it** unless it only adds.
   Additive first; a new version only for a break that cannot be avoided
   (`core/compatibility.md`).
5. **A list has a stable order and a limit**: a unique tie-breaker in the
   sort, a maximum page size, an opaque cursor (`core/pagination.md`).
6. **A write that may be retried is safe to retry**: an idempotent
   method, an `Idempotency-Key`, or `If-Match`. "Tell clients not to
   retry" is never the fix (`core/idempotency.md`).
7. **Where a parameter comes from is read, not guessed**: in
   `/openapi.json` or `app.openapi()` (`fastapi/parameters.md`).
8. **Nothing blocks inside `async def`**: a blocking call goes in a
   `def` endpoint or a thread (`fastapi/concurrency.md`).
9. **Tests run the lifespan and clean up**: `with TestClient(app)`, and
   `app.dependency_overrides` cleared after each test
   (`fastapi/testing.md`).
10. **FastAPI names come from the installed version**: `lifespan`, not
    `on_event`; `HTTP_422_UNPROCESSABLE_CONTENT`, not `..._ENTITY`
    (`fastapi/versions.md`).
11. **A test must be able to fail.** Break the behaviour, watch the test
    fail, restore it.

## What you say when you finish

End with these headings, each with `none` when empty. If another skill
is loaded, its headings come first and these after.

```
## Result
<what changed, or the answer, with paths; for a design, the contract
table; for a change to an API, breaking or not and why>

## Checked
<each test run, request or app.openapi() read, and the lines that show
the verdict, with the FastAPI and Starlette versions>

## Not checked
<versions, clients, platforms (Windows PowerShell 5.1) or a real server
not tried>
```

The `evals/` folder is for people testing this skill. Never open it
while doing a task.
