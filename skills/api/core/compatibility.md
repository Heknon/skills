# Breaking and non-breaking changes

**Verdict you produce** for every change to an API in use:

```
change:     <what changes, in the contract's words>
breaking:   yes | no, by rule <number below>
who breaks: <clients that send or read it; from CLIENTS files, logs, the person>
path:       <the additive way, or why none exists and which version gets it>
checked:    OpenAPI diff before and after (fastapi/openapi.md): <what it shows>
```

A change is breaking when a client that worked before fails, or keeps
working but does the wrong thing. Clients you cannot redeploy (mobile
apps in the field, firmware, other teams) run old code for months.

## The rules

| # | Change | Breaking? |
| --- | --- | --- |
| 1 | add an operation | no |
| 2 | add an optional request field or parameter | no |
| 3 | add a response field | no, if clients ignore unknown fields; say so in the API description from day one |
| 4 | remove or rename a request field, parameter, path or operation | **yes** |
| 5 | remove or rename a response field | **yes** |
| 6 | make an optional input required, or add a required one | **yes** |
| 7 | tighten validation: shorter maximum, narrower pattern, fewer allowed values in a request | **yes** |
| 8 | loosen validation of a request | no |
| 9 | add a value to an enum the client **sends** | no |
| 10 | add a value to an enum the client **receives** | **yes** for clients that switch on it; announce it, or document from day one that unknown values must be handled |
| 11 | change a default | **yes**: clients that omit the field get new behaviour |
| 12 | change a type (`"7"` to `7`), a format, a unit, a time zone | **yes** |
| 13 | change a status code or the error shape | **yes**: clients branch on them |
| 14 | change the sort order or page size default | **yes** for clients that rely on them; a tie-breaker added to fix duplicates is a fix, not a break |
| 15 | start requiring a header (`If-Match`, `Idempotency-Key`) | **yes** |
| 16 | reject unknown fields or parameters that were ignored | **yes** |

"A small cleanup" is not a category. Class each change by the table.

## The additive path

Most breaks have an additive route. The rename of `qty` to `quantity`
(*lab,* sandbox rename-field):

1. Add `quantity` beside `qty`. Accept either on input; reject both
   when they differ. Return both.
2. Mark `qty` deprecated in the schema, without runtime warnings in your
   own code: `Field(description="Deprecated: use quantity.",
   json_schema_extra={"deprecated": True})`. *lab:* pydantic's
   `Field(deprecated=...)` also marks it, but reading the field in your
   own validator raised `DeprecationWarning` (pydantic 2.13.5; field
   options are the pydantic skill's ground).
3. Tell clients, with a removal date; watch logs until no request sends
   `qty`; remove it in the next major version.

The OpenAPI diff of step 1 showed `quantity` added to both schemas,
`qty` still present with `"deprecated": true`, and `qty` gone from the
request's `required` list (loosening: rule 8). No field removed, none
newly required.

Making `note` required has no additive path: old clients omit it. Keep
it optional; if the business needs it, require it in a new version, or
default it on the server and say so.

## Versioning

Decision A4 (default): **additive change first; a path prefix
(`/v1`, `/v2`) only for a break that cannot be avoided. No header or
media type versioning.**

- `/v2` runs beside `/v1` until `/v1` traffic stops; both are served by
  one app (`app.include_router(v2_router, prefix="/v2")`,
  `fastapi/routing.md`).
- Only the operations that change get a `/v2` form; clients mix them.
- Deprecate `/v1` operations in the OpenAPI document
  (`@router.get(..., deprecated=True)` sets `"deprecated": true` on the
  operation) and give a date.

## Before you say "not breaking"

1. Dump the OpenAPI document on the old code and the new
   (`recipes/tools/openapi_dump.py`), diff them, and read every `-`
   line: a removed property, a new entry in `required`, a changed
   `type`, `enum`, `maximum` or `pattern`, a removed status code.
2. Run the old tests against the new code unchanged. A test you had to
   edit is a client you broke.
3. Name the clients from the repository (`CLIENTS.md`, README, the
   callers the person names). If you cannot, say "clients unknown".
