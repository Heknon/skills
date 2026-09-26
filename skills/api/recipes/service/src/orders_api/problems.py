"""Every error as RFC 9457 problem details (application/problem+json).

Handlers are registered on Starlette's HTTPException, not FastAPI's: the
router raises Starlette's for an unknown path (404) and a wrong method
(405), and FastAPI's HTTPException is a subclass, so one handler sees both.
"""

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM = "application/problem+json"
# RFC 9110 names; Python 3.12's HTTPStatus still has the older phrases.
TITLES = {413: "Content Too Large", 414: "URI Too Long",
          422: "Unprocessable Content"}
log = logging.getLogger(__name__)


def problem(status: int, detail: str | None = None, headers: dict[str, str] | None = None,
            **extensions: Any) -> JSONResponse:
    title = TITLES.get(status, HTTPStatus(status).phrase)
    body: dict[str, Any] = {"type": "about:blank", "title": title, "status": status}
    if detail is not None:
        body["detail"] = detail
    body.update(extensions)
    return JSONResponse(jsonable_encoder(body), status_code=status, headers=headers,
                        media_type=PROBLEM)


async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # keep the exception's headers: Allow on a 405, WWW-Authenticate on a 401
    detail = exc.detail if isinstance(exc.detail, str) else None
    return problem(exc.status_code, detail, headers=exc.headers)


async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [{"loc": list(e["loc"]), "type": e["type"], "msg": e["msg"]} for e in exc.errors()]
    return problem(422, "The request is not valid.", errors=errors)


async def unhandled(request: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled error on %s %s", request.method, request.url.path)
    return problem(500)  # never the exception text: it may hold secrets


def install(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_error)
    app.add_exception_handler(RequestValidationError, validation_error)
    app.add_exception_handler(Exception, unhandled)
