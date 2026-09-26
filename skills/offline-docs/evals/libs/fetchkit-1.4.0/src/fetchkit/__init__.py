"""fetchkit: a small HTTP helper."""

import urllib.parse
import urllib.request

__version__ = "1.4.0"


def get(url, timeout=10, params=None, headers=None):
    """Fetch url with an optional query dict. timeout is in seconds."""
    return _send("GET", url, params=params, headers=headers, timeout=timeout)


def _send(method, url, params=None, headers=None, timeout=10):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()
