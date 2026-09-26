"""Database access for users. One function per operation; no HTTP here."""

from app.db import Database, UserRow


def create_user(db: Database, email: str, name: str) -> UserRow:
    row = UserRow(id=db.new_id(), email=email, name=name)
    db.users[row.id] = row
    return row


def get_user(db: Database, user_id: int) -> UserRow | None:
    return db.users.get(user_id)
