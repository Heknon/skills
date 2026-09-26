# Tools

Two scripts, standard library only apart from the app being inspected.
Run them from the project root with the project's environment.

| Script | Does | Used by |
| --- | --- | --- |
| `openapi_dump.py` | imports `<module>:<app>`, writes `app.openapi()` as sorted, indented UTF-8 JSON, without a server | `fastapi/openapi.md`, `core/compatibility.md`, `core/review.md` |
| `stall_check.py` | fires N slow requests at a running server and times a fast one sent meanwhile | `fastapi/concurrency.md` |

```
uv run --no-sync python <skill>/recipes/tools/openapi_dump.py orders_api.main:app openapi.json
uv run --no-sync python <skill>/recipes/tools/stall_check.py http://127.0.0.1:8000 /quotes/USD /health 10
```

*lab* (Python 3.12, FastAPI 0.141.1, uvicorn 0.54.0):

- `openapi_dump.py` on the service recipe: `wrote openapi.json: OpenAPI
  3.1.0, 4 paths, 6 operations`; on the rename-field sandbox before and
  after a change, the two files diffed cleanly with `git diff
  --no-index`.
- `stall_check.py` on the stall sandbox: `/health sent meanwhile:
  5.91s` with a blocking `async def`, `0.00s` after the fix.

Notes:

- `openapi_dump.py` puts `./src` and `.` on `sys.path`, so it works for
  src and flat layouts that are not installed. Importing the app runs
  module-level code (never the lifespan); an app that connects to a
  database at import will try to here too, which is a finding in itself
  (`fastapi/lifespan.md`).
- `stall_check.py` bypasses any proxy settings, so it reaches
  `127.0.0.1` even where `HTTP_PROXY` is set. Point it at one worker:
  with several, the stall is divided, not gone.
