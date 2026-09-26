from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from app.repository import NoteRepository, get_repo

app = FastAPI()


class NoteOut(BaseModel):
    id: int
    title: str


@app.get("/notes/{note_id}")
def read_note(note_id: int, repo: Annotated[NoteRepository, Depends(get_repo)]) -> NoteOut:
    note = repo.get(note_id)
    if note is None:
        raise HTTPException(404, f"note {note_id} not found")
    return NoteOut(**note)
