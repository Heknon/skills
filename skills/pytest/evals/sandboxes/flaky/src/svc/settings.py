import os

_cache: dict | None = None


def load() -> dict:
    """Settings from the environment, read once."""
    global _cache
    if _cache is None:
        _cache = {"timeout": int(os.environ.get("SVC_TIMEOUT", "30"))}
    return _cache
