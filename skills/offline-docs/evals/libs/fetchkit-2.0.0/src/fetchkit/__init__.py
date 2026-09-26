"""fetchkit: a small HTTP helper."""

from fetchkit._transport import _send

__version__ = "2.0.0"
__all__ = ["get", "post"]


def get(url, **kw):
    """Fetch url.

    Keyword arguments are passed on to the transport.
    """
    return _send("GET", url, **kw)


def post(url, body, **kw):
    """Send body to url with POST."""
    return _send("POST", url, body=body, **kw)
