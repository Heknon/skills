"""A stand-in for the database: records are plain dicts, as a driver returns them."""

MEMBERS: dict[int, dict] = {
    1: {"id": 1, "email": "ann@example.com", "name": "Ann", "password_hash": "pbkdf2$1$ab12cd34", "failed_logins": 0},
    2: {"id": 2, "email": "bea@example.com", "name": "Bea", "password_hash": "pbkdf2$1$ef56ab78", "failed_logins": 3},
}


def find_member(member_id: int) -> dict | None:
    return MEMBERS.get(member_id)


def list_members() -> list[dict]:
    return list(MEMBERS.values())
