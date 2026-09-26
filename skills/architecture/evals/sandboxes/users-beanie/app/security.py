import hashlib
from typing import Annotated

from beanie import PydanticObjectId
from fastapi import Depends, Header, HTTPException

from app.repository import UserRepository, get_user_repository


def hash_password(password: str) -> str:
    return hashlib.sha256(b"demo-salt" + password.encode()).hexdigest()


async def current_user(
    x_user_id: Annotated[PydanticObjectId, Header()],
    repo: Annotated[UserRepository, Depends(get_user_repository)],
):
    """Demo authentication: the caller's id in a header. Real login is out of scope."""
    user = await repo.get(x_user_id)
    if user is None:
        raise HTTPException(401, "unknown user")
    return user
