"""fetchkit: a small HTTP helper."""

import urllib.request

__version__ = "1.2.0"


def get(url, timeout=30, headers=None):
    """Fetch url. timeout is in seconds and defaults to 30."""
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()
