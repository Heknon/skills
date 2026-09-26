import time

from callagain._defaults import DEFAULT_DELAY, DEFAULT_RETRIES


def retry_call(fn, *args, retries=None, delay=None, **kwargs):
    """Call fn(*args, **kwargs) and retry it when it raises.

    By default a failing call is retried 3 times, waiting ``delay``
    seconds between attempts. Pass ``retries`` to change the count.
    """
    if retries is None:
        retries = DEFAULT_RETRIES
    if delay is None:
        delay = DEFAULT_DELAY
    attempt = 0
    while True:
        try:
            return fn(*args, **kwargs)
        except Exception:
            if attempt >= retries:
                raise
            attempt += 1
            time.sleep(delay)
