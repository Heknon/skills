import os
from contextlib import asynccontextmanager
from typing import Annotated

from beanie import init_beanie
from fastapi import Depends, FastAPI
from pymongo import AsyncMongoClient

from app.models import User
from app.repository import UserRepository, get_user_repository
from app.schemas import UserCreate, UserOut
from app.security import hash_password


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncMongoClient(os.environ["MONGODB_URI"])
    await init_beanie(database=client[os.environ.get("MONGODB_DB", "users_sandbox")],
                      document_models=[User])
    yield
    await client.close()


app = FastAPI(lifespan=lifespan)
RepoDep = Annotated[UserRepository, Depends(get_user_repository)]


@app.post("/users", status_code=201)
async def create_user(body: UserCreate, repo: RepoDep) -> UserOut:
    user = await repo.add(body.email, body.display_name, hash_password(body.password))
    return UserOut.model_validate(user.model_dump())
