# Plan: the api skill

Status: draft for decision. Nothing is built yet.

## 1. What it is

Two layers of HTTP API knowledge in one skill:

1. **The contract** (`core/`), framework agnostic: naming, methods and
   status codes, PUT versus PATCH, errors, pagination, filtering and
   sorting, idempotency and retries, versioning, breaking changes.
2. **FastAPI** (`fastapi/`), the mechanics: `APIRouter`, `Depends`, how
   type hints become parameters, `response_model`, lifespan, handlers,
   middleware, background tasks, `async def` versus `def`, OpenAPI, and
   testing with `TestClient` or httpx.

It stops at the endpoint's edge. Request and response models and how
`Depends` works are api's. Services, repositories (the DAL) and DI as the
way layers are wired and swapped are architecture's; Beanie is mongodb's.
The router says so, so "add a service layer" is sent there.

## 2. The environment it is written for

- **A weak model in Zed on Windows with PowerShell**, air gapped, Python
  through uv, packages only from the internal mirror, no web.
- **No FastAPI documentation site.** The skill carries the facts. For the
  rest it points, through offline-docs, at the installed source (FastAPI
  parameters carry long `Doc(...)` texts in `fastapi/param_functions.py`
  and `fastapi/applications.py`) and at the app's own `app.openapi()`.
- **`/docs` is blank.** FastAPI 0.141.1 loads Swagger UI from
  `cdn.jsdelivr.net` by default (read in `fastapi/openapi/docs.py`). A
  blank page is not a broken app; read `/openapi.json` instead.
- **Local calls** use `curl.exe` or `Invoke-RestMethod`. A body without
  `Content-Type` is not read as JSON (`strict_content_type=True` in
  0.141.1; since which version: to verify in the lab).

## 3. The kinds of task

| Kind | Asked to | Answer shape |
| --- | --- | --- |
| **Design** | design an endpoint or a resource | a contract table: method, path, request, each response with status and body, errors; code if asked |
| **Evolve** | rename, add, remove, tighten, version | each change classed breaking or not, with the rule; the additive path; the OpenAPI diff |
| **Lists** | paginate, filter or sort a collection | the query parameters, the envelope, the stable order, a test across a page boundary |
| **Errors** | an error shape, handlers, validation errors | the handler code and the bodies a test received for each error |
| **Retries** | make a write safe to retry, stop duplicates | which methods are idempotent, the idempotency key or `If-Match` design, a test that repeats the request |
| **Endpoint** | write or change a FastAPI route | the code, its entry in `/openapi.json`, a `TestClient` test |
| **Depends** | write, share, cache, tear down or override a dependency | the code, and the setup and teardown order a test recorded |
| **Lifecycle** | lifespan, middleware, background tasks | the code and the order it runs in, observed |
| **Concurrency** | an endpoint stalls; `async def` or `def` | the blocking call, the choice, a timing that shows it |
| **Test** | test an API | tests that use `with TestClient(app)`, clear overrides, and fail when the endpoint breaks |
| **Explain** | an unexpected 422, a missing field, a handler not called | the cause, with the OpenAPI entry, the body or the source line |
| **Structure** | services, repositories, DAL, Beanie | a pointer to architecture or mongodb; only the api part is answered |

## 4. The failures it targets

| Failure | What it looks like |
| --- | --- |
| **Verbs and POST everywhere** | `/getUser`, `POST /orders/create`, `POST /orders/{id}/delete`; a GET that changes state |
| **Status as decoration** | 200 with `{"success": false}`; 500 for bad input; 401 and 403 swapped; 404 or 403 chosen without asking what it leaks |
| **PUT as partial, PATCH as reset** | a PUT that keeps omitted fields; a PATCH that writes `model_dump()` and so resets every omitted field |
| **Breaking change called compatible** | a renamed field, an optional field made required, a new enum value in a response, a changed default, tighter validation, shipped as "a small cleanup" |
| **Unstable pages** | offset pages sorted by a column with ties, so rows repeat or vanish; no maximum page size; a cursor that is just the offset |
| **Blind retries** | a POST retried after a timeout creates two orders; the fix offered is "tell clients not to retry" |
| **Body or query guessed** | a plain `str` on a POST, meant as body, read as a query parameter; a second model nests the body under parameter names |
| **Leaky response** | a handler returns the stored record with no `response_model` or return type, and `password_hash` goes out |
| **Blocking in `async def`** | `time.sleep`, a sync HTTP client or a sync driver in `async def` stalls every request; the fix offered is more workers |
| **`Depends` misused** | `Depends(get_db())` with parentheses; a dependency assumed to run twice in one request when it is cached; a yield dependency that swallows the error |
| **Overrides that leak** | `app.dependency_overrides` set and never cleared, so a later test fails only in some orders; the override keyed on a different function from the one in `Depends` |
| **Lifespan skipped in tests** | `TestClient(app)` without `with`, so lifespan never runs and `app.state` is empty; the model moves setup to import time |
| **Handler that misses** | a handler for `fastapi.HTTPException` does not see the router's 404 and 405, which raise Starlette's `HTTPException` |
| **API from memory** | `@app.on_event` (deprecated for lifespan); `HTTP_422_UNPROCESSABLE_ENTITY`, a deprecated alias of `HTTP_422_UNPROCESSABLE_CONTENT` in Starlette 1.7.0; middleware order assumed backwards |
| **Structure answered here** | asked for a service layer, the model invents one instead of loading architecture |

## 5. Layout

```
skills/api/
  SKILL.md, glossary.md   router over the twelve kinds, invariants, headings; words
  core/                   the contract; no framework in it
    design.md             procedure: from a need to a contract table, ends in a verdict
    naming.md             nouns, plurals, nesting depth, actions that are not CRUD
    methods-and-status.md safe and idempotent methods; the status codes used and when
    put-and-patch.md      replace or partial update; omitted versus null
    errors.md             one error shape (RFC 9457 problem details); validation errors
    pagination.md         offset or cursor (keyset); stable order; limits; cost of a total
    filtering-sorting.md  parameter conventions, allow lists, sort keys
    idempotency.md        what may be retried; idempotency keys; ETag and If-Match
    compatibility.md      breaking and non-breaking changes; deprecation; versioning
    review.md             procedure: review an API or an OpenAPI diff, ends in a verdict
  fastapi/
    parameters.md         how hints become path, query, header, body; Annotated; embed
    responses.md          response_model, return annotations, filtering, status codes
    routing.md            APIRouter, include_router, route order, trailing slashes
    dependencies.md       sub-dependencies, per-request cache, yield and scope, overrides
    lifespan.md           lifespan, app.state, why not on_event
    errors.md             HTTPException, handlers, RequestValidationError, problem details
    middleware.md         order, pure ASGI or BaseHTTPMiddleware, CORS
    background.md         BackgroundTasks: when they run; not a queue
    concurrency.md        async def or def, the threadpool, finding the blocking call
    openapi.md            reading the document offline, operation ids, diffing versions
    testing.md            TestClient, httpx AsyncClient, clearing overrides
    debug.md              procedure: 422, missing field, wrong source, handler not called
    versions.md           differences between the pinned versions; renamed names
  recipes/service/        a small complete service: routers, dependencies, lifespan,
                          problem details, cursor pages, idempotent POST, tests;
                          in-memory store, flat on purpose (structure is architecture's)
  examples/               a PATCH fixed, a breaking change avoided, a stall found
  evals/                  evals.json and sandboxes
```

## 6. Dependencies and boundaries

| Skill | Needs | Relies on by name | Existing skills it touches |
| --- | --- | --- | --- |
| api | pydantic | pydantic, offline-docs | pytest (`TestClient`) |

- **Needs pydantic**: what `response_model` filters and what a 422 holds
  are pydantic facts. api builds in wave 2.
- **pydantic by name**: partial models (`exclude_unset`, unset versus
  `None`), validators, settings. api owns what PUT and PATCH mean;
  pydantic owns telling omitted from null; mongodb owns `$set`.
- **offline-docs by name**: reading installed FastAPI and Starlette source.
- **pytest** owns running, fixtures and mocking; api owns `TestClient`,
  lifespan in tests and `dependency_overrides`.
- **architecture** (which needs api) owns DI as layer wiring and keeping
  request and response models apart from domain and database models; api
  owns `Depends` mechanics and those models. Beanie is mongodb's.
  code-review relies on api by name.

Found while planning:

- **observability** has a FastAPI example (`examples/web-api.md`) and owns
  whether a 404 is an error in a trace; api owns which status to return.
- **deployment** owns probes, workers and shutdown timeouts; api owns the
  health endpoint and what lifespan does on shutdown.
- **navigation** finds the app and decorator routes
  (`languages/python/entry-points.md`); api points there.
- **linting** owns ruff's FastAPI rules (`FAST`; to verify in the lab).

### Proposed changes to the roadmap

1. Add observability, deployment and navigation to api's "Existing skills
   it touches".
2. New boundary row, **validation errors**: pydantic owns
   `ValidationError` and `errors()`; api owns the HTTP response built
   from it.
3. New boundary row, **pagination**: api owns the contract (cursor, order,
   page size); mongodb owns the query and index that serve it.
4. New boundary row, **dependency overrides in tests**: api owns
   `app.dependency_overrides`, architecture what is swapped, pytest the
   fixtures.
5. **Calling other APIs** (httpx clients, timeouts, backoff) has no owner
   (A8).

## 7. How it will be verified

Pins proposed for R2 (newest on the index on 2026-09-25): FastAPI
0.141.1, Starlette 1.7.0, pydantic 2.13.5, uvicorn 0.54.0, httpx 0.28.1,
httpx2 2.13.1, Python 3.12, and one older FastAPI (A1). FastAPI requires
`starlette>=0.46.0` with no upper bound: every run records Starlette's.

The lab must run, on both FastAPI versions, and record:

- a matrix of endpoint signatures and each `/openapi.json` entry (the
  evidence for `fastapi/parameters.md`); `response_model` against return
  annotation, and what an extra field does;
- the per-request dependency cache, `use_cache=False`, yield teardown
  order for `scope="function"` and `"request"`, and an exception caught
  after `yield` and not re-raised;
- `TestClient` with and without `with`; handlers on Starlette's and
  FastAPI's `HTTPException` against an unknown route;
- middleware order (Starlette 1.7.0's `add_middleware` inserts at
  position 0, so the last added should be outermost);
- a blocking call in `async def` and in `def` under concurrent requests,
  and the threadpool size (anyio's default: to verify);
- `BackgroundTasks` timing and errors; trailing slash redirects;
- Starlette 1.7.0's `TestClient` imports `httpx2` first and warns on
  `httpx` (read in `starlette/testclient.py`): which the mirror has;
- the recipe's tests under `uv run pytest` in PowerShell on Windows.

Contract facts cite RFC 9110, 9457, 5789, 7396 and 8288, quoted from the
text in the lab. `Idempotency-Key` is an IETF draft (status to verify).

## 8. Evals, written first

Small uv projects with a FastAPI app and tests, each baiting one failure.

| Sandbox | Prompt, shortened | Bait |
| --- | --- | --- |
| `patch-resets` | add PATCH for a nickname, like the others | the existing PATCH writes `model_dump()`; copying it clears other fields |
| `put-partial` | add a PUT to update a user's email | a partial update called PUT |
| `leaky-user` | add `GET /users/{id}` | the store returns a dict with `password_hash` |
| `cancel-reason` | add `POST /orders/{id}/cancel` with a reason | `reason: str` is read as query; only `/openapi.json` shows it |
| `stall` | the API freezes under load; add workers | `time.sleep` and a sync client in `async def` |
| `override-leak` | a test fails only in CI; mark it flaky | an override set and never cleared in an earlier test |
| `lifespan-tests` | tests fail on `app.state.pool` | `TestClient(app)` without `with` |
| `duplicate-rows` | clients see repeats; raise the page size | offset pages ordered by `created_at`, which has ties |
| `rename-field` | rename `qty`, make `note` required; small cleanup | both break clients; an additive path exists |
| `double-payment` | payments are duplicated; tell clients not to retry | POST with no idempotency key |
| `ok-false` | add an endpoint in the style of the others | the others return 200 with `{"ok": false}`; do not copy it, do not change them unasked |
| `problem-details` | make every error `application/problem+json` | a handler on FastAPI's `HTTPException` misses the router's 404 |
| `blank-docs` | the Swagger page is blank; fix the app | the CDN is unreachable; the app is fine |
| `add-service-layer` | move the logic into a service and repository | architecture's; the model loads it or says so |

Expectations are listed as in `skills/pytest/evals/evals.json`; every
bait is reproduced on the pinned versions before the skill is written.

## 9. Decisions needed

### A1. Versions

*Recommended:* the latest in the mirror (FastAPI 0.141.1 today) and the
oldest a team service pins (a deployment sandbox pins 0.118.0), with
`fastapi/versions.md` listing the differences. Which versions run?

### A2. One error shape

*Recommended:* RFC 9457 problem details for new APIs, validation errors
in an `errors` extension member. An existing API keeps its shape.

### A3. Default pagination

*Recommended:* cursor (keyset), opaque, built from the sort key plus a
unique tie-breaker; offset only for small, stable lists; always a limit.

### A4. Versioning

*Recommended:* additive change first; a path prefix (`/v1`) only for an
unavoidable break. No header or media type versioning.

### A5. PATCH format

*Recommended:* merge patch meaning (omitted is unchanged, `null` clears)
over `application/json`; JSON Patch (RFC 6902) for reading only.

### A6. Parameter style and test client

*Recommended:* `Annotated[...]` everywhere, the default-value style for
reading old code; `with TestClient(app)`, and httpx `AsyncClient` with
`ASGITransport` only when the test must await something else.

### A7. Popular structures and other frameworks

*Recommended:* services, DAL and Beanie stay with architecture and
mongodb, and the recipe stays flat and says why. FastAPI only; `core/`
stays framework agnostic so a `flask/` folder can be added later.

### A8. Calling other APIs

*Recommended:* out of this skill, except which requests are safe to retry
(`core/idempotency.md`). Client timeouts and backoff need an owner.
