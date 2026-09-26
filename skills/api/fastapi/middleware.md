# Middleware

Code that runs around every request: timing, request ids, CORS, gzip.
Tracing and metrics middleware are the observability skill's ground.
*lab* rows ran on FastAPI 0.141.1 with Starlette 1.7.0 and on 0.118.0
with Starlette 0.48.0, same results.

## Order: the last added is the outermost

`app.add_middleware(cls, **options)` inserts at the front of the list
(Starlette's `self.user_middleware.insert(0, ...)`, read in every wheel
from 0.44 to 1.7), and `@app.middleware("http")` does the same. *lab,*
three added in turn, then a decorator:

```python
app.add_middleware(Named, name="first-added")
app.add_middleware(PureASGI, name="second-added")
app.add_middleware(Named, name="third-added")
@app.middleware("http")
async def deco(request, call_next): ...
```

```
decorator in, third-added in, second-added in, first-added in, endpoint,
first-added out, third-added out, decorator out, background one, background two, second-added out
```

The request goes through the **last added first**. Add in the order
"innermost first": the middleware that must see everything (CORS,
request id) goes last.

**CORS must be outside anything that can answer early.** *lab:* with
an auth middleware that returns 401 without an `Authorization` header:

| Order | Preflight `OPTIONS` | 401 response |
| --- | --- | --- |
| CORS added first (inner), auth last (outer) | 401, no `access-control-allow-origin` | no CORS header: the browser hides the 401 from the page |
| auth first, CORS added last (outer) | 200 with `access-control-allow-origin: http://ui` | carries the CORS header |

```python
app.add_middleware(CORSMiddleware, allow_origins=["https://ui.example.internal"],
                   allow_methods=["*"], allow_headers=["*"])   # add it last
```

## `BaseHTTPMiddleware` or pure ASGI

| | `BaseHTTPMiddleware` / `@app.middleware("http")` | pure ASGI class (`__call__(scope, receive, send)`) |
| --- | --- | --- |
| writing it | `dispatch(request, call_next)`, returns a response | wraps `send` to see `http.response.start` |
| background tasks | *lab:* its code after `call_next` ran **before** the response's background tasks | *lab:* its "out" line ran **after** them |

For a request id, timing or a header on every response, either works.
For timing that must include background work, write pure ASGI. From the
lab:

```python
class PureASGI:
    def __init__(self, app, name):
        self.app, self.name = app, name

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).append((b"x-pure", b"1"))
            await send(message)

        await self.app(scope, receive, send_wrapper)
```

*lab:* the response carried `x-pure: 1`.

## Not for

- Authentication per route: a dependency (`fastapi/dependencies.md`)
  shows in the OpenAPI document and can be overridden in tests;
  middleware does neither.
- Turning exceptions into responses: exception handlers
  (`fastapi/errors.md`).
