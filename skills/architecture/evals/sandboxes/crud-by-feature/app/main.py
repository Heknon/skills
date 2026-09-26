from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import Database
from app.projects.router import router as projects_router
from app.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = Database()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(users_router)
app.include_router(projects_router)
