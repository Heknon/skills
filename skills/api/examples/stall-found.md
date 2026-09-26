# Worked example: the stall that workers did not fix

Kinds: Concurrency, Explain. Outputs from a lab run on FastAPI 0.141.1,
Starlette 1.7.0, uvicorn 0.54.0 (the eval sandbox stall).

## The ask

> The API freezes under load: while /quotes requests are running, even
> /health hangs. Add more uvicorn workers in run.ps1.

## Steps

1. **Measure first.** Start one worker, as `run.ps1` does, and in a
   second terminal fire ten quotes and one health check:
   ```
   uv run --no-sync uvicorn quotes.main:app --app-dir src --port 8000
   uv run --no-sync python <skill>/recipes/tools/stall_check.py http://127.0.0.1:8000 /quotes/USD /health 10
   ```
   ```
   one /quotes/USD alone:          0.61s
   10 x /quotes/USD at once:      6.02s
   /health sent meanwhile:     5.91s
   ```
   Ten requests took ten times one, and `/health`, which does nothing,
   waited for all of them: the event loop is blocked
   (`fastapi/concurrency.md`).
2. **Find the blocking call.** `quote` is `async def`. It calls
   `rates.fetch_rate`, a plain function that makes a synchronous HTTP
   call (simulated with `time.sleep(0.5)` in the sandbox), then
   `time.sleep(0.1)` itself. Both block the loop that serves every
   request of the worker.
3. **Try the person's idea, measured**, with `--workers 4`:
   ```
   10 x /quotes/USD at once:      2.41s
   /health sent meanwhile:     1.70s
   ```
   Better, not fixed: each of the four workers still stalls, and
   `/health` still waits 1.7 s. On a probe with a 1 s timeout the pod
   would still be restarted.
4. **Fix**: nothing in `quote` is awaited, so declare it `def`;
   FastAPI then runs it in the threadpool:
   ```diff
    @app.get("/quotes/{currency}")
   -async def quote(currency: str, amount: float = 1.0) -> dict:
   +def quote(currency: str, amount: float = 1.0) -> dict:
   ```
5. **Measure again**, one worker:
   ```
   one /quotes/USD alone:          0.65s
   10 x /quotes/USD at once:      0.61s
   /health sent meanwhile:     0.00s
   ```
   `uv run pytest -q`: `1 passed`.

## The answer

```
## Result
The stall is a blocked event loop, not a lack of workers. quote in
src/quotes/main.py was async def but called blocking code
(rates.fetch_rate, a synchronous HTTP call, and time.sleep), so each
request stopped every other request in the worker, /health included.
Changed quote to def, so FastAPI runs it in its threadpool. run.ps1 is
unchanged: with one worker, ten quotes now finish in 0.61 s and /health
answers at once. Four workers without the fix still stalled /health for
1.7 s.

## Checked
- stall_check.py, one worker, before: 10 quotes 6.02 s, /health 5.91 s.
- the same with --workers 4, before: 2.41 s and 1.70 s.
- after the change, one worker: 0.61 s and 0.00 s.
- uv run pytest -q: 1 passed. FastAPI 0.141.1, uvicorn 0.54.0.

## Not checked
- The real rates service's latency and limits: the threadpool runs at
  most 40 quotes at once per worker; beyond that they queue.
- Windows: the timings ran on Linux; the commands are the same in
  PowerShell.
```
