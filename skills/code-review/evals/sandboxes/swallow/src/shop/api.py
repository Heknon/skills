"""HTTP routes for order notes."""

from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from shop.notes import AUDIT, STORE, AuditLog, NoteStore

app = FastAPI()


def get_store() -> NoteStore:
    return STORE


def get_audit() -> AuditLog:
    return AUDIT


class NoteIn(BaseModel):
    text: str = Field(min_length=1, max_length=2_000)


class NoteOut(BaseModel):
    order_id: str
    saved: bool


@app.post("/orders/{order_id}/notes", status_code=201)
def add_note(
    order_id: str,
    body: NoteIn,
    store: Annotated[NoteStore, Depends(get_store)],
    audit: Annotated[AuditLog, Depends(get_audit)],
) -> NoteOut:
    store.add(order_id, body.text)
    audit.record(f"note added to {order_id}")
    return NoteOut(order_id=order_id, saved=True)
