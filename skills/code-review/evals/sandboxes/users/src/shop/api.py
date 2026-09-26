"""HTTP routes for users. Routes call the service; only the repository queries."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from beanie import PydanticObjectId, init_beanie
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from pymongo import AsyncMongoClient

from shop.models import User
from shop.repository import UserRepository
from shop.schemas import UserOut
from shop.service import UserService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    client: AsyncMongoClient[dict[str, object]] = AsyncMongoClient(
        os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
    )
    await init_beanie(database=client["shop"], document_models=[User])
    yield
    await client.close()


def get_user_service() -> UserService:
    return UserService(UserRepository())


router = APIRouter()


@router.get("/users/{user_id}")
async def read_user(
    user_id: PydanticObjectId,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserOut:
    user = await service.profile(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return user


app = FastAPI(lifespan=lifespan)
app.include_router(router)
