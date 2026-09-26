# One error shape: problem details

Decision A2 (default): **new APIs answer every error with RFC 9457
problem details, media type `application/problem+json`, and put
validation errors in an `errors` extension member.** An existing API
keeps its shape; changing it is a breaking change
(`core/compatibility.md`). FastAPI's own default is different
(`{"detail": ...}`, below); `fastapi/errors.md` has the handlers.

## The members (RFC 9457 section 3.1)

| Member | Holds | Rule quoted |
| --- | --- | --- |
| `type` | a URI naming the problem type | default `about:blank`: "the problem has no additional semantics beyond that of the HTTP status code" |
| `title` | a short summary of the type | with `about:blank`, "the title SHOULD be the same as the recommended HTTP status phrase for that code (e.g., "Not Found" for 404" |
| `status` | the status code, as a number | "Generators MUST use the same status code in the actual HTTP response" |
| `detail` | this occurrence, for a person | "ought to focus on helping the client correct the problem, rather than giving debugging information"; "Consumers SHOULD NOT parse the "detail" member" |
| `instance` | a URI for this occurrence | optional |
| extensions | anything else, such as `errors` | "Clients consuming problem details MUST ignore any such extensions that they don't recognize" |

The RFC's own validation example (section 3):

```
HTTP/1.1 422 Unprocessable Content
Content-Type: application/problem+json

{"type": "https://example.net/validation-error",
 "title": "Your request is not valid.",
 "errors": [{"detail": "must be a positive integer", "pointer": "#/age"}, ...]}
```

## The shape this skill uses

From the recipe (`recipes/service/src/orders_api/problems.py`), as a
test received it:

```json
{"type": "about:blank", "title": "Unprocessable Content", "status": 422,
 "detail": "The request is not valid.",
 "errors": [{"loc": ["body", "status"], "type": "extra_forbidden",
             "msg": "Extra inputs are not permitted"}]}
```

```json
{"type": "about:blank", "title": "Not Found", "status": 404,
 "detail": "Order 999 not found"}
```

- `about:blank` until the API documents its own problem types; then a
  stable URI per type (`https://errors.example.internal/out-of-stock`)
  that clients switch on, never on `title` or `detail`.
- `errors` keeps pydantic's `loc`, `type` and `msg` (`type` is stable
  across versions, `msg` is not: `skills/pydantic/reference/errors.md`).
  Leave out `input`: it echoes what the client sent, which may be a
  password. Leave out `ctx` and `url`.
- The 500 body says nothing about the cause. The exception goes to the
  log, never to the client (*lab:* the recipe's test raises
  `RuntimeError("password=hunter2")` and asserts `hunter2` is absent).

## Which status (summary; `core/methods-and-status.md` has the rules)

| Situation | Status | `detail` says |
| --- | --- | --- |
| body or parameter fails validation | 422 | "The request is not valid." plus `errors` |
| unknown id | 404 | which resource |
| state forbids it | 409 | what state, what to do |
| stale `If-Match` | 412 | GET it again |
| not authenticated / not allowed | 401 (with `WWW-Authenticate`) / 403 | nothing that helps an attacker |
| a bug | 500 | nothing |

## Errors from other layers

Custom exception classes (when to define one, where it lives, its
fields) are the architecture skill's ground; so is translating errors
layer by layer. This skill owns the last step: the handler that turns
an exception into a status and a problem body. A `ValidationError`
raised by your own code, not by FastAPI, is a 500 until you convert it
(`core/put-and-patch.md`).

## Never

- Never answer an error with 200 (`core/methods-and-status.md`).
- Never put a stack trace, SQL, a file path or a secret in any member.
- Never mix shapes in one API: `{"detail": ...}` from some routes and
  problem details from others. When moving an API to problem details,
  every handler moves together (`fastapi/errors.md`), and it is a
  breaking change for clients that read `detail`.
