from fastapi import FastAPI
from pydantic import BaseModel

from members.store import list_members

app = FastAPI()


class MemberSummary(BaseModel):
    id: int
    name: str


@app.get("/members")
def get_members() -> list[MemberSummary]:
    return list_members()
