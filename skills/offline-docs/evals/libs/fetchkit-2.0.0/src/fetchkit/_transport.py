"""The one place fetchkit talks to the network."""

import urllib.parse
import urllib.request


def _send(method, url, *, body=None, query=None, headers=None, timeout=None):
    if query:
        url = url + "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()
