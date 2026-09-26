from typing import Annotated, Any

from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError

from articles import store

app = FastAPI()


class Article(BaseModel):
    id: int
    title: str = Field(min_length=1, max_length=120)
    body: str
    tags: list[str] = []
    revision: int


@app.get("/articles/{article_id}")
def get_article(article_id: int) -> Article:
    doc = store.get(article_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return Article(**doc)


@app.patch("/articles/{article_id}")
def patch_article(article_id: int, body: Annotated[dict[str, Any], Body()]) -> Article:
    doc = store.get(article_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Article not found")
    body.pop("id", None)
    body.pop("revision", None)
    try:
        merged = Article.model_validate({**doc, **body})
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors(include_url=False, include_context=False))
    saved = store.replace(article_id, merged.model_dump())
    return Article(**saved)
