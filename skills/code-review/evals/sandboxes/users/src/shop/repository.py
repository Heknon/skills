"""Reads and writes of users. The only module that queries User."""

from beanie import PydanticObjectId

from shop.models import User


class UserRepository:
    async def get(self, user_id: PydanticObjectId) -> User | None:
        return await User.get(user_id)
