from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Shop API", version="1.4.0")


class LineIn(BaseModel):
    sku: str
    qty: int = Field(ge=1)
    note: str | None = None


class Line(LineIn):
    id: int


LINES: dict[int, Line] = {1: Line(id=1, sku="bolt", qty=3)}


@app.post("/lines", status_code=201)
def add_line(body: LineIn) -> Line:
    line = Line(id=max(LINES) + 1, **body.model_dump())
    LINES[line.id] = line
    return line


@app.get("/lines/{line_id}")
def get_line(line_id: int) -> Line:
    if line_id not in LINES:
        raise HTTPException(status_code=404, detail="Line not found")
    return LINES[line_id]
