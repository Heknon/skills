"""Builds API responses from stored user records."""

from app.schemas import UserOut


def user_response(record: dict[str, object]) -> str:
    """The JSON body for GET /users/{id}."""
    out = UserOut(
        id=int(str(record["_id"])),
        user_name=str(record["login"]),
        display_name=str(record["name"]),
        email=str(record["email"]),
    )
    return out.model_dump_json()


def greeting(out: UserOut) -> str:
    return f"Hello, {out.display_name} ({out.user_name})"
