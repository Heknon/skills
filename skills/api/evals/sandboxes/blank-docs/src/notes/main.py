from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Notes API", version="0.3.0")


class Note(BaseModel):
    id: int
    text: str


NOTES = [Note(id=1, text="Air gapped")]


@app.get("/notes")
def list_notes() -> list[Note]:
    return NOTES
