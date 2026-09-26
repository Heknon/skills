"""fetchkit: a small HTTP helper."""

import urllib.parse
import urllib.request

__version__ = "1.5.0"


def get(url, *, query=None, headers=None, timeout=10):
    """Fetch url with an optional query dict. timeout is in seconds."""
    return _send("GET", url, query=query, headers=headers, timeout=timeout)


def _send(method, url, *, query=None, headers=None, timeout=10):
    if query:
        url = url + "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()
