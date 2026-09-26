# async def or def, and finding the blocking call

**Verdict you produce** for "the API stalls":

```
blocking call: <file:line, the call>, inside async def <endpoint or dependency>
before:        <fast path> took <s> while <n> x <slow path> ran
fix:           <def endpoint | await run_in_threadpool(...) | an async client>
after:         <fast path> took <s>; <n> x <slow path> took <s>
```

## How FastAPI runs an endpoint

| Declared | Runs on | A blocking call inside it |
| --- | --- | --- |
| `async def` | the event loop, one per worker process | **stops every request in that worker** until it returns |
| `def` | a thread from the threadpool | stops only that thread |

The same holds for dependencies (`fastapi/dependencies.md`). The
threadpool is anyio's default limiter: *lab:* `anyio.to_thread.current_default_thread_limiter().total_tokens`
was `40` (anyio 4.15.1; `CapacityLimiter(40)` in anyio's source). The
41st concurrent `def` call waits for a free thread.

## What it looks like (*lab*, uvicorn 0.54.0, one worker)

Each endpoint below takes 1 s; ten requests at once, and one `/health`
(an `async def` returning at once) sent 0.2 s later:

| Endpoint | 10 at once took | `/health` took |
| --- | --- | --- |
| `async def` with `time.sleep(1)` | **10.05 s** | **9.82 s** |
| `async def` with `await asyncio.sleep(1)` | 1.02 s | 0.00 s |
| `def` with `time.sleep(1)` | 1.03 s | 0.00 s |
| `async def` with `await anyio.to_thread.run_sync(time.sleep, 1)` | 1.02 s | 0.00 s |
| `def` with `time.sleep(1)`, **50** at once | 2.05 s: 40 threads, then 10 more | |

More workers do not fix it: *lab:* with `--workers 4`, the ten
`async def` + `time.sleep` requests still took 4.04 s instead of 1 s.
Each worker still stalls; there are just four of them.

## Find the blocking call

Blocking means: waits on I/O or sleeps without `await`. Look inside
every `async def` endpoint and dependency, and the functions they call,
for:

- `time.sleep(...)`
- a synchronous HTTP client: `requests.*`, `urllib.request`, an
  `httpx.Client` (not `AsyncClient`)
- a synchronous database driver or ORM session (`pymongo`, a
  SQLAlchemy `Session`), file reads of large files, `subprocess.run`
- CPU-heavy work (hashing passwords, big JSON, image work): it holds
  the loop the same way

Then prove it with a timing before changing anything. Start the app
with one worker, and in a second terminal:

```
uv run --no-sync uvicorn quotes.main:app --app-dir src --port 8000
uv run --no-sync python <skill>/recipes/tools/stall_check.py http://127.0.0.1:8000 /quotes/USD /health 10
```

*lab,* sandbox stall (a blocking `fetch_rate` and `time.sleep(0.1)` in
`async def quote`):

```
one /quotes/USD alone:          0.61s
10 x /quotes/USD at once:      6.02s
/health sent meanwhile:     5.91s
```

The fast path taking as long as all the slow ones together is the
signature of a blocked event loop.

## Fix it

| Situation | Fix |
| --- | --- |
| the endpoint only calls blocking code | declare it `def`; FastAPI runs it in the threadpool |
| the endpoint mixes `await` calls with one blocking call | keep `async def`, and `await run_in_threadpool(fetch_rate, currency)` (`from fastapi.concurrency import run_in_threadpool`) or `await anyio.to_thread.run_sync(...)` |
| `time.sleep` in `async def` | `await asyncio.sleep(...)` |
| an async client exists and is installed | use it (`httpx.AsyncClient`, an async driver); do not add a package to do so, air gapped |

*lab,* the stall sandbox after changing `async def quote` to `def
quote`: ten quotes took 0.64 s and `/health` 0.00 s.

The threadpool is the next ceiling: 40 blocking calls at a time per
worker. If the slow call is slow because the service behind it is, more
threads only queue more work there. Calling other services (timeouts,
retries, clients) has no owner skill yet (roadmap R6).

## Never

- Never answer a stall with more workers or more replicas before the
  timing shows no blocked loop.
- Never turn every endpoint into `async def` "for speed": an `async
  def` that calls blocking code is slower than a `def`.
