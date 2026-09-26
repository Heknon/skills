"""Find a user in whichever source is configured: the users module or a cache."""

from types import ModuleType
from typing import Any

from app import users


def resolve(user_id: int, source: Any | ModuleType = users) -> dict[str, object]:
    finder = getattr(source, "get_user", None)
    if finder is None:
        # a source without a finder knows nobody
        return {"id": user_id, "name": "unknown"}
    found = finder(user_id)
    return found if found is not None else {"id": user_id, "name": "unknown"}
