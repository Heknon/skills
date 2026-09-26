# Glossary

One sentence per term. Use these words and no synonyms.

| Term | Meaning |
| --- | --- |
| resource | A thing the API names with a URL, such as one order (`/orders/7`) or the collection of orders (`/orders`). |
| collection | A resource that lists other resources and usually accepts POST to create one. |
| contract | What a client may rely on: paths, methods, parameters, bodies, status codes, headers, error shapes and their meaning. |
| operation | One method on one path, such as `PATCH /orders/{order_id}`; one entry in the OpenAPI document. |
| safe method | A method that asks for no change on the server: GET, HEAD, OPTIONS, TRACE (RFC 9110 section 9.2.1). |
| idempotent method | A method whose effect is the same when sent once or many times: PUT, DELETE and the safe methods (RFC 9110 section 9.2.2). |
| replace | What PUT does: the stored resource becomes the body; fields the body leaves out take their defaults or are rejected. |
| merge patch | What PATCH does in this skill: fields the body leaves out stay, `null` clears, anything else is set (RFC 7396). |
| omitted | A field absent from a request body; in pydantic, not in `model_fields_set`. |
| revision | A number the store increments on every write to a record, used to detect that someone else wrote first. |
| ETag | A response header naming the version of what was returned; here the quoted revision, such as `"3"`. |
| precondition | A request header that makes the request conditional, such as `If-Match: "3"`; false gives 412. |
| lost update | Two clients read the same version, both write, and the second silently overwrites the first. |
| idempotency key | A client-chosen `Idempotency-Key` header that lets the server recognise a retry of a POST and replay the first answer. |
| problem details | The RFC 9457 error body (`type`, `title`, `status`, `detail`, `instance`, extensions) sent as `application/problem+json`. |
| breaking change | A change after which a client that worked before fails or silently misbehaves. |
| additive change | A change that only adds something clients may ignore: an operation, an optional input, a response field. |
| deprecation | Marking a part of the contract as going away, while it still works, with a date or version for removal. |
| page | One slice of a collection, with a way to ask for the next one. |
| cursor | An opaque string in a page that tells the server where the next page starts. |
| keyset pagination | Pages that start after the last seen sort key, not after a count of rows; what a cursor encodes. |
| tie-breaker | A unique field (usually the id) added to the sort so that no two rows compare equal. |
| path operation | FastAPI's name for a decorated endpoint function, such as `@router.get(...)`. |
| dependency | A callable named in `Depends(...)` that FastAPI calls for a request and whose result it passes in. |
| yield dependency | A dependency written as a generator: code before `yield` runs first, code after runs at teardown. |
| dependency override | An entry in `app.dependency_overrides` that replaces one dependency callable with another, keyed by the original callable. |
| lifespan | The async context manager given to `FastAPI(lifespan=...)`; code before its `yield` runs at startup, after it at shutdown. |
| exception handler | A function registered with `@app.exception_handler(cls)` that turns an exception into a response. |
| request validation error | FastAPI's `RequestValidationError`, raised when a request's parameters or body fail validation; a 422 by default. |
| response model | The model FastAPI validates and filters a return value through: from `response_model=` or the return annotation. |
| event loop | The single thread that runs every `async def` endpoint of one worker; a blocking call there stops them all. |
| threadpool | The threads (40 by default, anyio) where FastAPI runs `def` endpoints and `def` dependencies. |
| OpenAPI document | The JSON description of the API that FastAPI generates, at `/openapi.json` or from `app.openapi()`. |
