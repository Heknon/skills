# PUT and PATCH

**Verdict you produce** for an update endpoint:

```
method:     PUT (replace) | PATCH (merge patch)
omitted:    <reset to default or rejected (PUT) | unchanged (PATCH)>
null:       <cleared, or 422 for a field that cannot be null>
validated:  body with <model>; merged result with <full model>
races:      <If-Match -> 412 | revision write -> retry, then 409 | none, and why>
checked:    <each case run: omitted, null, invalid, stale tag> -> <status>
```

## What each method means

RFC 9110 section 9.3.4, PUT: "requests that the state of the target
resource be created or replaced with the state defined by the
representation enclosed in the request message content."

RFC 5789, PATCH: "With PATCH, however, the enclosed entity contains a
set of instructions describing how a resource currently residing on the
origin server should be modified to produce a new version." And: "PATCH
is neither safe nor idempotent". And: "The server MUST apply the entire
set of changes atomically ... If the entire patch document cannot be
successfully applied, then the server MUST NOT apply any of the
changes."

So:

| Body sends | PUT | PATCH (merge patch) |
| --- | --- | --- |
| a field with a value | set | set |
| a field as `null` | set to null (or 422) | cleared (or 422 if it cannot be null) |
| nothing for a field | default, or 422 if required | **unchanged** |
| a server-owned field (`id`, `revision`) | 422 | 422 |
| a misspelt field | 422 with `extra="forbid"` | 422 with `extra="forbid"`; ignored silently otherwise, so the PATCH does nothing |

A request that changes one field is a PATCH. A "PUT" that keeps omitted
fields is a PATCH with the wrong name: clients and proxies may retry a
PUT as idempotent, and a later full PUT client will expect a reset.

## The merge patch format (RFC 7396)

This skill's PATCH bodies follow RFC 7396's meaning over plain
`application/json`: "If the patch is anything other than an object, the
result will always be to replace the entire target", nested objects
merge key by key, a member with value `null` is removed, and "it is not
possible to patch part of a target that is not an object, such as to
replace just some of the values in an array": a list is replaced whole.
Its example:

```
ORIGINAL        PATCH            RESULT
{"a":"b"}       {"a":null}      {}
{"a": {"b": "c"}}  {"a": {"b": "d", "c": null}}  {"a": {"b": "d"}}
{"a":[{"b":"c"}]}  {"a": [1]}    {"a": [1]}
```

One difference: RFC 7396 removes a member set to `null`; here `null`
stores null for a nullable field and is a 422 for a field that cannot be
null. The mongodb skill writes it as `$set: null`, never `$unset`
(roadmap R4). *lab:* FastAPI 0.141.1 and 0.118.0 parse a body sent as
`Content-Type: application/merge-patch+json` as JSON (any `+json`
subtype), so accept both. JSON Patch (RFC 6902, a list of `op` objects)
is for reading other APIs, not for new endpoints here.

## The PATCH flow (roadmap R4), and who owns each step

| Step | What | Owner |
| --- | --- | --- |
| 1 | parse the body with the partial model, `context={"partial": True}` | pydantic: `skills/pydantic/partial/handoff.md` |
| 2 | read the stored record and its revision | mongodb (store) |
| 3 | merge the body onto the stored data, validate with the **full** model | pydantic: `apply_patch` in `skills/pydantic/recipes/patch/src/app/patching.py` |
| 4 | write only the changed fields, filtered on the revision read in step 2 | mongodb (a dotted `$set`) |
| - | the meaning above; 404, 409, 412, 422; `If-Match` and `ETag`; retry on a lost race | api (this file) |

What the endpoint does with `apply_patch`, from
`recipes/service/src/orders_api/routes.py`:

```python
@router.patch("/{order_id}")
def patch_order(order_id: int,
                body: Annotated[dict[str, Any], Body(description="JSON merge patch ...")],
                store: StoreDep, response: Response,
                if_match: Annotated[str | None, Header()] = None) -> Order:
    for _ in range(WRITE_RETRIES):
        stored = found(store, order_id)                                   # 404
        if if_match is not None and not if_match_holds(if_match, etag(stored)):
            raise HTTPException(412, "The order changed since you read it; GET it again")
        if stored["status"] == "cancelled":
            raise HTTPException(409, "A cancelled order cannot be changed")
        try:
            result = apply_patch(Order.model_validate(stored), OrderPatch, body)
        except ValidationError as e:                                      # 422, not 500
            raise RequestValidationError(
                [{**err, "loc": ("body", *err["loc"])} for err in e.errors(include_url=False)]
            ) from e
        saved = store.update_if_revision(order_id, result.changes, stored["revision"])
        if saved is not None:
            response.headers["ETag"] = etag(saved)
            return saved
    raise HTTPException(409, "The order kept changing; try again")
```

Three FastAPI facts shape it (*lab*, 0.141.1 and 0.118.0):

1. **The body parameter is a `dict`, not the partial model.** FastAPI
   validates a model parameter with no validation context, so a model
   validator that returns early on `context={"partial": True}` runs on
   the partial's defaults: *lab:* `body: UserPatch` answered a valid
   `{"min_items": 15}` with 422 `min_items must not be above max_items`.
   The cost of the `dict`: `/openapi.json` shows the body as `object`;
   say what it accepts in `Body(description=...)`.
2. **A `ValidationError` raised inside the endpoint is a 500.** Only
   FastAPI's own parameter validation becomes a 422. *lab:* `{"name":
   "Al"}` through `apply_patch` without the `except` gave `500 Internal
   Server Error`. Re-raise as `RequestValidationError`, with `"body"`
   put in front of each `loc` so the error looks like every other body
   error.
3. **`model_copy(update=...)` validates nothing, and FastAPI does not
   catch it on the way out.** *lab:* the patch-resets sandbox's
   `stored.model_copy(update=body.model_dump())` turned `{"bio":
   "Runner"}` into `display_name: None` and FastAPI returned it with 200,
   although `Profile.display_name` has `min_length=1`: a returned
   instance of the response model's own class was not validated again.

## Races

A PATCH is read, merge, write. Two clients that read revision 1 and
both write lose one update. Two defences, used together:

- **Client side, `If-Match`.** GET returns `ETag: "<revision>"`; the
  client sends it back in `If-Match`; a stale tag is 412. Accept `*` and
  a list of tags; compare strongly, so a weak `W/"3"` never matches
  (13.1.1: "An origin server MUST use the strong comparison function").
  Requiring `If-Match` (428 when missing) breaks clients that do not
  send it: add it as optional first (`core/compatibility.md`).
- **Server side, the revision write.** Step 4 writes only if the stored
  revision is still the one read. If not, someone wrote in between:
  without `If-Match`, read and merge again (a merge patch re-applies
  cleanly) a few times, then 409; with `If-Match`, the next loop sees
  the new tag and answers 412.

The recipe tests both: two PATCHes with the same tag give 200 then 412;
a forced lost race is retried and keeps the other writer's change; a
store that always loses gives 409.

## PUT in code

The body is the full input model (`OrderIn`), validated by FastAPI; no
partial, no merge; omitted fields take their defaults. *lab,* sandbox
put-partial: `PUT {"email": ...}` alone gave 422 `['body', 'name']`,
and a full body without `locale` reset it to `"en"`.

## Never

- Never dump a PATCH body with `model_dump()`, `exclude_none` or
  `exclude_defaults`; only `exclude_unset=True`
  (`skills/pydantic/partial/unset-and-none.md`).
- Never call a partial update PUT.
- Never let a PATCH change server-owned fields (`id`, `status` set by an
  action, `revision`, timestamps): keep them out of the input model.
