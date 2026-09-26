"""Database documents."""

from beanie import Document, Indexed


class User(Document):
    email: Indexed(str, unique=True)  # type: ignore[valid-type]
    name: str
    password_hash: str

    class Settings:
        name = "users"
