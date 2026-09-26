from fastapi import FastAPI

from app.routes import router

app = FastAPI(title="Orders")
app.include_router(router)
