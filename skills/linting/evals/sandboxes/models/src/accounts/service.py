from accounts.models import User


def from_row(row: tuple[int, str, str]) -> User:
    """Build a User from a database row (id, display name, email)."""
    user_id, name, email = row
    return User(id=user_id, display_name=name, email=email)


def from_wire(payload: dict[str, object]) -> User:
    return User.model_validate(payload)
