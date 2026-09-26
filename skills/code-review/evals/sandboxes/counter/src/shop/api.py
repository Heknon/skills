"""HTTP routes for page views."""

import os
from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.collection import Collection

from shop.pages import PageDoc, record_view

app = FastAPI()
_mongo: MongoClient[PageDoc] | None = None


def get_pages() -> Collection[PageDoc]:
    global _mongo
    if _mongo is None:
        _mongo = MongoClient(os.environ.get("MONGODB_URL", "mongodb://localhost:27017"))
    return _mongo["shop"]["pages"]


class ViewsOut(BaseModel):
    slug: str
    views: int


@app.post("/pages/{slug}/views")
def count_view(
    slug: str, pages: Annotated[Collection[PageDoc], Depends(get_pages)]
) -> ViewsOut:
    return ViewsOut(slug=slug, views=record_view(pages, slug))
