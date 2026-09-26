from users.models import User, UserPatch


def patch_user(stored: User, body: dict) -> User:
    """PATCH /users/{id}: change only what the body sends; nested objects too."""
    patch = UserPatch.model_validate(body)
    merged = stored.model_dump()
    merged.update(patch.model_dump(exclude_unset=True))
    return User.model_validate(merged)
