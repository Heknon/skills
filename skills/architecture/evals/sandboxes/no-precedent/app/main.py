from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from app.store import NoteStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.notes = NoteStore()
    yield


app = FastAPI(lifespan=lifespan)


def get_store(request: Request) -> NoteStore:
    return request.app.state.notes


StoreDep = Annotated[NoteStore, Depends(get_store)]


class NoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    body: str = ""


class NoteOut(BaseModel):
    id: int
    title: str
    body: str


@app.post("/notes", status_code=201)
def create_note(body: NoteIn, store: StoreDep) -> NoteOut:
    note = store.add(body.title, body.body)
    return NoteOut(id=note.id, title=note.title, body=note.body)


@app.get("/notes/{note_id}")
def get_note(note_id: int, store: StoreDep) -> NoteOut:
    note = store.get(note_id)
    if note is None:
        raise HTTPException(404, f"note {note_id} not found")
    return NoteOut(id=note.id, title=note.title, body=note.body)
