from beanie import Document
from pymongo import IndexModel


class User(Document):
    email: str
    display_name: str
    bio: str = ""
    password_hash: str
    is_admin: bool = False
    failed_logins: int = 0

    class Settings:
        name = "users"
        indexes = [IndexModel("email", unique=True)]
