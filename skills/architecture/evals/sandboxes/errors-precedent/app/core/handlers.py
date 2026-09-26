from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.errors import AppError, ConflictError, NotFoundError

STATUS = {NotFoundError: 404, ConflictError: 409}


async def app_error(request: Request, exc: AppError) -> JSONResponse:
    status = next((s for cls, s in STATUS.items() if isinstance(exc, cls)), 500)
    return JSONResponse({"code": exc.code, "detail": str(exc)}, status_code=status)


def install(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error)
