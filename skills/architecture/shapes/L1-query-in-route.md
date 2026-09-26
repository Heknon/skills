# L1: the route queries the database

**Rule.** A path operation parses the request, calls one function of the
layer below, and maps the result to a response model. It never builds a
query (`Model.find(...)`, `session.execute(select(...))`, a store call
with a filter) itself.

**Why.** A query in a route cannot be reused by a worker or a CLI, is
tested only through HTTP, and hides a data access pattern (an index, an
N+1) from the file where readers look for queries.

**Target.** The query moves into the data layer the card names: the
feature's `repository.py`, or `crud.py` in a crud-by-feature codebase.
The route calls it through a provider. Add no service if the card has
none (`core/layers.md`).

## Before

```python file=before/app/main.py
from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()
app.state.rows = [
    {"id": 1, "title": "Draft", "published": False},
    {"id": 2, "title": "Launch", "published": True},
]


class PostOut(BaseModel):
    id: int
    title: str


@app.get("/posts")
def published_posts(request: Request) -> list[PostOut]:
    rows = [r for r in request.app.state.rows if r["published"]]   # the query
    return [PostOut(id=r["id"], title=r["title"]) for r in rows]
```

## After

```python file=after/app/repository.py
from pydantic import BaseModel


class Post(BaseModel):
    id: int
    title: str
    published: bool


class PostRepository:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def published(self) -> list[Post]:
        return [Post(**r) for r in self._rows if r["published"]]
```

```python file=after/app/main.py
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel

from app.repository import PostRepository

app = FastAPI()
app.state.rows = [
    {"id": 1, "title": "Draft", "published": False},
    {"id": 2, "title": "Launch", "published": True},
]


def get_posts(request: Request) -> PostRepository:
    return PostRepository(request.app.state.rows)


class PostOut(BaseModel):
    id: int
    title: str


@app.get("/posts")
def published_posts(posts: Annotated[PostRepository, Depends(get_posts)]) -> list[PostOut]:
    return [PostOut(id=p.id, title=p.title) for p in posts.published()]
```

## The test both pass

```python file=test_shape.py
from fastapi.testclient import TestClient

from app.main import app


def test_only_published_posts_are_listed():
    assert TestClient(app).get("/posts").json() == [{"id": 2, "title": "Launch"}]
```

After only: the query is testable without HTTP.

```python file=after/test_repository.py
from app.repository import PostRepository


def test_published_filters_drafts():
    rows = [{"id": 1, "title": "a", "published": False}]
    assert PostRepository(rows).published() == []
```

Checked with `uv run python check_shapes.py L1`: before 1 passed,
after 2 passed. The steps from before to after are refactoring's recipe
`L1`.
