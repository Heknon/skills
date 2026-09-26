"""All MongoDB access for users goes through this class."""

from beanie import PydanticObjectId

from app.models import User


class UserRepository:
    async def add(self, email: str, display_name: str, password_hash: str) -> User:
        return await User(email=email, display_name=display_name,
                          password_hash=password_hash).insert()

    async def get(self, user_id: PydanticObjectId) -> User | None:
        return await User.get(user_id)


def get_user_repository() -> UserRepository:
    return UserRepository()
