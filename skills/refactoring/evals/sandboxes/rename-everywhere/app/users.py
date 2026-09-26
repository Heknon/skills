"""Users, read from the in-memory store."""

__all__ = ["get_user", "list_users"]

_STORE: dict[int, dict[str, object]] = {
    1: {"id": 1, "name": "Ada", "active": True},
    2: {"id": 2, "name": "Linus", "active": False},
}


def get_user(user_id: int) -> dict[str, object] | None:
    """Return the user with this id, or None."""
    return _STORE.get(user_id)


def list_users(active_only: bool = False) -> list[dict[str, object]]:
    users = [get_user(key) for key in sorted(_STORE)]
    return [u for u in users if u is not None and (u["active"] or not active_only)]
