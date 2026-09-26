"""Show whether slow requests stall the others: fire N slow requests at
once, send one fast request while they run, and time both.

    uv run --no-sync python <skill>/recipes/tools/stall_check.py http://127.0.0.1:8000 /quotes/USD /health 10

Start the app first (uvicorn, one worker) in another terminal. Standard
library only; it never goes through a proxy. If the fast request takes
about as long as all the slow ones together, something blocks the event
loop (fastapi/concurrency.md).
"""

import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def timed(url: str) -> float:
    start = time.perf_counter()
    OPENER.open(url, timeout=120).read()
    return time.perf_counter() - start


def main() -> int:
    if len(sys.argv) not in (4, 5):
        print("usage: stall_check.py <base-url> <slow-path> <fast-path> [n]", file=sys.stderr)
        return 2
    base, slow, fast = sys.argv[1].rstrip("/"), sys.argv[2], sys.argv[3]
    n = int(sys.argv[4]) if len(sys.argv) == 5 else 10
    one = timed(base + slow)
    with ThreadPoolExecutor(max_workers=n + 1) as pool:
        start = time.perf_counter()
        slow_runs = [pool.submit(timed, base + slow) for _ in range(n)]
        time.sleep(0.1)
        fast_time = pool.submit(timed, base + fast).result()
        for run in slow_runs:
            run.result()
        total = time.perf_counter() - start
    print(f"one {slow} alone:          {one:.2f}s")
    print(f"{n} x {slow} at once:      {total:.2f}s")
    print(f"{fast} sent meanwhile:     {fast_time:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
