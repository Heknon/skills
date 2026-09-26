"""A small job runner with the same contract as the team's task queue.

The job runs in a worker process. Its result, or the exception it raised,
travels back to the caller pickled, as it does through the queue's result
backend.
"""

from concurrent.futures import ProcessPoolExecutor
from typing import Any, Callable


def _run_and_capture(job: Callable[..., Any], args: tuple) -> tuple[str, Any]:
    try:
        return ("ok", job(*args))
    except Exception as exc:  # the queue ships the job's exception back to the caller
        return ("error", exc)


def run(job: Callable[..., Any], *args: Any) -> Any:
    with ProcessPoolExecutor(max_workers=1) as pool:
        status, value = pool.submit(_run_and_capture, job, args).result()
    if status == "error":
        raise value
    return value
