# API contract

Run when the change touches a route, a request or response model, or a
status code (`core/checklist.md`). The api skill owns the contract and
its per-operation checklist (`core/review.md`); this pass runs that
checklist on the changed operations and ranks its findings on this
skill's scale: api's **blocking** is a blocker or a major by the
scenario (`core/rank.md`), **should** is minor, **note** is a nit.

### API1 A change breaks existing clients

- **Ask:** is a response field removed, renamed or retyped, a request
  field made required, a default page size or sort changed, an error
  status changed?
- **Facts:** api (`core/compatibility.md`: what breaks, the additive
  path); `app.openapi()` before and after (`fastapi/openapi.md`).
- **Severity:** major; blocker when clients lose or corrupt data.

### API2 The status says the wrong thing

- **Ask:** 200 on failure, 500 on bad input, 201 without a created
  resource, 404 against 403?
- **Facts:** api (`core/methods-and-status.md`, `core/errors.md`).

### API3 The response is not declared

- **Ask:** does each changed route declare what it returns (a return
  annotation or `response_model`), and is it a response model, not a
  stored document? See security SEC2 and architecture L3.

### API4 PUT and PATCH do what they mean

- **Ask:** does a PATCH change only the fields sent? Does `null` clear?
- **Facts:** api (`core/put-and-patch.md`), pydantic
  (`partial/unset-and-none.md`), mongodb (`core/patch-to-set.md`).

### API5 Lists are bounded and stable

- **Ask:** is there a maximum page size, a tie-breaker in the sort, a
  way to the next page that survives inserts?
- **Facts:** api (`core/pagination.md`), mongodb (`core/pagination.md`).

### API6 A retried POST creates or charges twice

- **Ask:** what happens when the client repeats the request after a
  timeout?
- **Facts:** api (`core/idempotency.md`).

## Signs

```
API1  -  ^\s{4}\w+\s*:\s*[\w\[\], |.]+(\s*=.*)?$
API2  +  status_code\s*=|HTTPException\(|status\.HTTP_\d+
API4  +  exclude_unset|exclude_none|@\w+\.(patch|put)\(
API5  +  \b(page|size|limit|offset|skip)\b\s*:\s*(Annotated\[)?int
API6  +  @\w+\.post\(
```
