"""What the API documents for PATCH /users/{id}."""

from users.models import UserPatch


def patch_body_schema() -> dict:
    return UserPatch.model_json_schema()
