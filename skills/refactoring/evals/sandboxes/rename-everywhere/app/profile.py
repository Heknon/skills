from app import users


def display_name(user_id: int) -> str:
    user = users.get_user(user_id)
    if user is None:
        return "unknown"
    return str(user["name"])
