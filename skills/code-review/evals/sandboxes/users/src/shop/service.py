"""Use cases for users."""

from beanie import PydanticObjectId

from shop.repository import UserRepository
from shop.schemas import UserOut


class UserService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def profile(self, user_id: PydanticObjectId) -> UserOut | None:
        user = await self.users.get(user_id)
        if user is None:
            return None
        return UserOut(id=str(user.id), email=user.email, name=user.name)
