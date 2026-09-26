from users.models import User, UserPatch


def patch_user(stored: User, body: dict) -> User:
    """PATCH /users/{id}: change only what the body sends."""
    patch = UserPatch.model_validate(body)
    return stored.model_copy(update=patch.model_dump())
