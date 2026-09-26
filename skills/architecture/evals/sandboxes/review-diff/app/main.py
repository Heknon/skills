import os
from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from pymongo import AsyncMongoClient

from app.invoices.models import Invoice
from app.invoices.router import router as invoices_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncMongoClient(os.environ["MONGODB_URI"])
    await init_beanie(database=client["billing"], document_models=[Invoice])
    yield
    await client.close()


app = FastAPI(lifespan=lifespan)
app.include_router(invoices_router)
