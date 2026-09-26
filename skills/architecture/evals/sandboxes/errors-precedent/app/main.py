from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.billing.repository import InvoiceRepository
from app.billing.router import router as billing_router
from app.core import handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.invoices = InvoiceRepository()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(billing_router)
handlers.install(app)
