from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI()


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        {"type": "about:blank", "title": str(exc.detail), "status": exc.status_code},
        status_code=exc.status_code,
        media_type="application/problem+json",
    )


class TicketIn(BaseModel):
    title: str = Field(min_length=3)
    priority: int = Field(ge=1, le=5)


TICKETS: dict[int, dict] = {1: {"id": 1, "title": "Printer on fire", "priority": 1}}


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int) -> dict:
    if ticket_id not in TICKETS:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TICKETS[ticket_id]


@app.post("/tickets", status_code=201)
def create_ticket(body: TicketIn) -> dict:
    ticket = {"id": max(TICKETS) + 1, **body.model_dump()}
    TICKETS[ticket["id"]] = ticket
    return ticket
