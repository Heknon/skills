# Review an API, an endpoint or an OpenAPI diff

**Verdict you produce:** findings ranked by what they cost a client,
each with its evidence, and one line of verdict.

```
verdict:  ready | ready after the blocking findings | not ready
blocking: <finding> - <evidence: file:line, an OpenAPI path, a request and its response>
should:   <finding> - <evidence>
note:     <finding> - <evidence>
checked:  <what you ran: the tests, app.openapi(), requests>
```

A finding is **blocking** when it breaks a client, loses or duplicates
data, or leaks something; **should** when it breaks an invariant of this
skill without harm yet; **note** for style. The code-review skill ranks
across a whole change; this file is the API part it relies on.

## Steps

1. **Get the contract as data**: dump the OpenAPI document
   (`recipes/tools/openapi_dump.py`). For a change, dump before and
   after and diff them (`fastapi/openapi.md`).
2. **Breaking changes first**: read every `-` line of the diff against
   `core/compatibility.md`. Any hit is blocking unless the person said
   the clients are updated together.
3. **Walk each operation** with the checklist below. Evidence is a line
   of the OpenAPI document, a line of code, or a request you sent with
   TestClient and its answer. Never a guess about what FastAPI does.
4. **Run the tests**, and for each status the contract promises, find
   the test that sees it. A promised status with no test is a finding.
5. **Write the verdict** with the ranked findings.

## Checklist per operation

| Check | Look at | Finding if |
| --- | --- | --- |
| path and method fit | the path, `core/naming.md` | a verb path for a CRUD action; GET that changes state (blocking) |
| status on success | `responses` in the OpenAPI entry; `status_code=` | POST creating a resource returns 200; DELETE returns a body nobody reads |
| errors are statuses | handlers, the tests | 200 with an error flag (should, blocking if new); 500 for bad input (blocking) |
| the error shape is the API's one | the handlers | a route that answers in another shape |
| response declared | the return annotation or `response_model`; the OpenAPI `schema` is not `{}` | `schema: {}` or a stored record returned raw (blocking if it holds secrets) |
| body where intended | `requestBody` in the OpenAPI entry | a scalar meant for the body listed under `parameters` with `"in": "query"` |
| inputs bounded | `maxLength`, `maximum`, `maxItems` in schemas; `le=` on `limit` | an unbounded string, list or page size |
| unknown keys | `extra` on the input models | ignored in a PATCH (a misspelt field silently does nothing) |
| PUT and PATCH meaning | the handler | PATCH dumping without `exclude_unset`; PUT keeping omitted fields (blocking) |
| lists | the sort, the page parameters | no tie-breaker, no maximum, offset over a changing set |
| retries | method and headers | a POST that charges or creates with no idempotency key (blocking for money) |
| races | ETag and `If-Match`, the store write | read-merge-write with no revision check where several clients edit |
| blocking calls | `async def` bodies | `time.sleep`, a sync client or driver inside `async def` (blocking under load) |
| tests | the test files | `TestClient(app)` without `with`, overrides never cleared, a test that cannot fail |
| names from memory | imports and decorators | `@app.on_event`, `HTTP_422_UNPROCESSABLE_ENTITY` (should) |

Structure findings (a route that talks to the database directly, logic
in the router) are the architecture skill's; name them and point there.

## Never

- Never approve a change as "compatible" without the OpenAPI diff.
- Never rank a style preference as blocking.
- Never fix while reviewing unless asked; list the fix with the finding.
