def can_delete(user: dict) -> bool:
    return user.get("role") == "admin"
