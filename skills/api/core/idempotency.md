# Idempotency and retries

Networks drop responses. A client that sent a request and got no answer
does not know whether it ran. Every write is designed for that moment.

**Verdict you produce:**

```
operation:   <method and path>
retry-safe:  <by method (PUT, DELETE) | by Idempotency-Key | by If-Match | no, and why that is acceptable>
repeat:      <what a repeat returns, and that it changes nothing>
checked:     a test that sends the request twice: <one record, one side effect>
```

## What may be retried

RFC 9110 section 9.2.2: idempotent methods "can be repeated
automatically if a communication failure occurs before the client is
able to read the server's response", and "A client SHOULD NOT
automatically retry a request with a non-idempotent method unless it
has some means to know that the request semantics are actually
idempotent, regardless of the method".

| Operation | Retry-safe as is | Make it safe with |
| --- | --- | --- |
| GET, HEAD | yes | nothing |
| PUT (full replace) | yes: the second write stores the same state | `If-Match` if others may write between |
| DELETE | yes: the second is a 404 or 204, the resource stays gone | answer 204 or 404 consistently; say which |
| PATCH (merge patch) | the same patch twice gives the same result, but not if another write came between | `If-Match` (`core/put-and-patch.md`) |
| POST that creates or charges | **no**: a repeat creates a second order or charges twice | `Idempotency-Key` |
| POST action (`/cancel`) | make it so: cancelling a cancelled order returns the same result, not an error | a state check |

"Tell clients not to retry" does not remove duplicates; it turns them
into lost writes: the request that timed out may never have arrived.

## Idempotency-Key

The header is an IETF draft, not an RFC:
`draft-ietf-httpapi-idempotency-key-header-07` (15 October 2025), a
working group document that expired on 18 April 2026 (datatracker,
read 2026-09-26). Its rules are sound and widely copied; cite it as a
draft.

What the server does (draft sections 2.6 and 2.7):

| Request | Draft says | Recipe answers |
| --- | --- | --- |
| first with this key | "process the request normally" | runs, stores the response under the key |
| same key, same body, first finished | "respond with the result of the previously completed operation, success or an error" | the stored response, same status, nothing runs |
| same key, first still running | "respond with a resource conflict error" | 409 |
| same key, different body | "reply with a HTTP 422 status code" | 422 |
| key missing where it is required | "reply with an HTTP 400 status code" | the recipe makes the key optional; see below |

Design points:

- **Scope** the key to the caller (a key from client A never replays
  client B's response) and to the operation.
- **Fingerprint** the body (a hash of the canonical JSON) to tell a true
  retry from a reused key.
- **Claim before the side effect.** Record the key as in flight before
  charging or inserting; a second request with the key then sees it
  (409) instead of running too. If the operation fails before anything
  changed, release the key so a retry can run.
- **Expiry.** Keep keys at least as long as clients retry (a day is
  common), and say so in the API description: the draft says "Resources
  MUST publish a idempotency related specification" including expiry.
- **Optional first.** Making the header required breaks every current
  client (`core/compatibility.md`). Add it as optional, have clients
  send it, then require it in a later version if needed.
- **Storage.** The record must survive a restart and be shared by all
  workers: a database table or collection with a unique index on the
  key (the mongodb skill's ground), never a Python dict in production.
  The recipe keeps it in memory only so it runs anywhere.

From `recipes/service/src/orders_api/routes.py`:

```python
if idempotency_key is not None:
    seen = store.claim_key(idempotency_key, fingerprint(fields))
    if seen is not None:
        if seen["fingerprint"] != fingerprint(fields):
            raise HTTPException(422, "This Idempotency-Key was used with a different body")
        if seen["response"] is None:
            raise HTTPException(409, "A request with this Idempotency-Key is in progress")
        response.headers["Location"] = f"/orders/{seen['response']['id']}"
        return seen["response"]           # the first answer, not a second order
```

*lab:* the recipe's tests send the same body twice with one key (one
order, the same response), a different body with the key (422) and a
request while the key is claimed (409). With the key check removed,
those three tests failed.

## Test that a repeat is harmless

Send the request twice and assert on the side effect, not only on the
status: one row in the store, one call to the charging function (patch
it where it is used: `skills/pytest/core/mocking.md`), the same body
both times.
