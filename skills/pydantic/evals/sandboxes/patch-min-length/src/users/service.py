from pydantic import ValidationError  # noqa: F401  (raised to the web layer as a 422)

from users.models import User, UserPatch


def create_user(body: dict) -> User:
    return User.model_validate(body)


def patch_user(stored: User, body: dict) -> User:
    patch = UserPatch.model_validate(body)
    return stored.model_copy(update=patch.model_dump(exclude_unset=True))
