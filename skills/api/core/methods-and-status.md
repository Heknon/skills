# Methods and status codes

The status code is the part of the answer every client, proxy, cache,
retry library and dashboard reads. The body explains; the status
decides. Quotes are from RFC 9110 unless another RFC is named.

## Methods

| Method | Safe | Idempotent | Use for |
| --- | --- | --- | --- |
| GET | yes | yes | read one member or a page of a collection |
| HEAD | yes | yes | GET without the body; *lab:* a FastAPI `@get` route answers HEAD with 405 unless HEAD is declared too |
| POST | no | no | create a member (server picks the id); run an action |
| PUT | no | yes | replace a member with the full body, or create it at a client-chosen id |
| PATCH | no | no (RFC 5789) | change some fields; `core/put-and-patch.md` |
| DELETE | no | yes | remove a member |

"Safe" (9.2.1): "the client does not request, and does not expect, any
state change on the origin server". "Idempotent" (9.2.2): "the intended
effect on the server of multiple identical requests with that method is
the same as the effect for a single such request. Of the request methods
defined by this specification, PUT, DELETE, and safe request methods are
idempotent." Only those may be retried blindly
(`core/idempotency.md`).

## Status codes used, and when

| Code | When | Body |
| --- | --- | --- |
| 200 OK | a read, or a write that returns the resource | the resource |
| 201 Created | POST created a member; PUT created one | the resource; header `Location: /orders/7` |
| 202 Accepted | work queued, not done | a link to its status |
| 204 No Content | success with nothing to return (DELETE) | empty; *lab:* FastAPI with `status_code=204` and `return None` sent `b''` |
| 400 Bad Request | a request that cannot be read at all | problem |
| 401 Unauthorized | no or bad credentials; "MUST send a WWW-Authenticate header field" (15.5.2) | problem |
| 403 Forbidden | known caller, not allowed | problem |
| 404 Not Found | no such resource, or one this caller may not know exists | problem |
| 405 Method Not Allowed | the path exists, the method does not; "MUST generate an Allow header field" (15.5.6) | problem |
| 409 Conflict | the current state forbids it (cancel a shipped order); a write lost a race | problem saying what conflicts |
| 412 Precondition Failed | `If-Match` did not match (13.1.1) | problem |
| 415 Unsupported Media Type | a body in a format the operation does not take | problem |
| 422 Unprocessable Content | the body or a parameter parsed but broke a rule; FastAPI's validation status | problem with the errors |
| 428 Precondition Required | the operation requires `If-Match` and it was missing (RFC 6585) | problem |
| 429 Too Many Requests | rate limited; "MAY include a Retry-After header" (RFC 6585) | problem |
| 500 Internal Server Error | a bug; never for bad input | problem without internals |
| 503 Service Unavailable | a dependency is down, try later | problem, `Retry-After` |

Decisions that go wrong most often:

- **200 with `{"ok": false}`** tells every generic client the call
  worked: retries do not fire, monitoring counts a success, caches may
  keep it. Use the 4xx or 5xx that fits. In an API that already does
  this, a new endpoint uses real statuses and the old ones are left
  alone unless the person asks; changing them breaks their clients.
- **401 or 403.** 401: "lacks valid authentication credentials". 403:
  "understood the request but refuses to fulfill it". *lab:* FastAPI's
  `HTTPBearer` and `APIKeyHeader` answer a missing credential with 401 and
  `WWW-Authenticate: Bearer` from 0.122.0; 0.118 to 0.121 answered 403
  (`fastapi/versions.md`).
- **404 or 403** for a resource the caller may not see: 15.5.4 says "An
  origin server that wishes to "hide" the current existence of a
  forbidden target resource MAY instead respond with a status code of
  404". Ask what a 403 would leak (that order 7 exists); for ids a
  caller can guess, 404.
- **409, 412 or 422.** 422: the body itself is wrong, whatever the state
  ("syntax of the request content is correct, but it was unable to
  process the contained instructions", 15.5.21). 409: the body is fine
  but the resource's current state forbids it. 412: the client's own
  precondition (`If-Match`) is false.
- **400 or 422.** FastAPI answers 422 for every parameter or body that
  fails validation, and for malformed JSON (*lab:* `json_invalid` at
  `['body', 9]`). Keep 422 for anything the model rejects; 400 only for
  what never reached validation.
- **POST is 200 in FastAPI unless you say 201.** *lab:* `@app.post` with
  no `status_code` answered 200. Write `status_code=201` on creating
  routes and set `Location` (`fastapi/responses.md`).

## Names in code

Write the number or the constant from `starlette.status` (re-exported as
`fastapi.status`). *lab, Starlette 1.7.0:* `status.HTTP_422_UNPROCESSABLE_ENTITY`
still returns 422 but warns `'HTTP_422_UNPROCESSABLE_ENTITY' is
deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.`; the same
for `HTTP_413_REQUEST_ENTITY_TOO_LARGE`, `HTTP_414_REQUEST_URI_TOO_LONG`
and `HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE`. Python 3.12's
`HTTPStatus(422).phrase` is `'Unprocessable Entity'`; 3.13 and later
say `'Unprocessable Content'` (*lab*).
