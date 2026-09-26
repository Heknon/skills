# L1: a query out of a route, into a repository

**End state:** the architecture skill's `shapes/L1-query-in-route.md`:
the query in the data layer the structure card names (a repository, or
`crud.py`), reached by the route through a provider. **Steps from the
catalogue:** extract class (the repository, added unused), then the
query replaced by a call.

## Pins

The shape's test (1 passed), a probe of `GET /posts`, the OpenAPI
document. Search the data the query reads (`app.state.rows` here; a
session, a collection) and every test that sets it.

## Steps

### 1. Add the repository beside the route, not used yet

With a test of the query without HTTP: the new place is pinned before
anything uses it.

```diff
diff --git a/app/repository.py b/app/repository.py
new file mode 100644
--- /dev/null
+++ b/app/repository.py
@@ -0,0 +1,15 @@
+from pydantic import BaseModel
+
+
+class Post(BaseModel):
+    id: int
+    title: str
+    published: bool
+
+
+class PostRepository:
+    def __init__(self, rows: list[dict]) -> None:
+        self._rows = rows
+
+    def published(self) -> list[Post]:
+        return [Post(**r) for r in self._rows if r["published"]]
diff --git a/test_repository.py b/test_repository.py
new file mode 100644
--- /dev/null
+++ b/test_repository.py
@@ -0,0 +1,6 @@
+from app.repository import PostRepository
+
+
+def test_published_filters_drafts():
+    rows = [{"id": 1, "title": "a", "published": False}]
+    assert PostRepository(rows).published() == []
```

Commit: `Add PostRepository beside the route`

### 2. Replace the query in the route with a call through a provider

The provider reads the data at request time (`request.app.state.rows`),
never at import (Traps).

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -1,5 +1,9 @@
-from fastapi import FastAPI, Request
+from typing import Annotated
+
+from fastapi import Depends, FastAPI, Request
 from pydantic import BaseModel
 
+from app.repository import PostRepository
+
 app = FastAPI()
 app.state.rows = [
@@ -9,4 +13,8 @@ app.state.rows = [
 
 
+def get_posts(request: Request) -> PostRepository:
+    return PostRepository(request.app.state.rows)
+
+
 class PostOut(BaseModel):
     id: int
@@ -15,5 +23,4 @@ class PostOut(BaseModel):
 
 @app.get("/posts")
-def published_posts(request: Request) -> list[PostOut]:
-    rows = [r for r in request.app.state.rows if r["published"]]   # the query
-    return [PostOut(id=r["id"], title=r["title"]) for r in rows]
+def published_posts(posts: Annotated[PostRepository, Depends(get_posts)]) -> list[PostOut]:
+    return [PostOut(id=p.id, title=p.title) for p in posts.published()]
```

Commit: `Read published posts through PostRepository`

## Traps seen in the lab

| Trap | What happened |
| --- | --- |
| the repository built at import: `posts_repo = PostRepository(app.state.rows)` | a test that set `app.state.rows = [...]` got the rows from import time: `assert [{'id': 2, 'title': 'Launch'}] == [{'id': 7, 'title': 'Other'}]`; with the provider, it passed |
| seniority's change check | `published_posts parameter 'request' became 'posts'; a caller passing it by name breaks`. FastAPI fills that parameter; no caller passes it. Say so in the answer |

## What the checks said (lab)

```
L1   start  tests 1 passed | ruff clean | mypy clean | import-all 2 ok, 0 failed, 0 skipped
L1   1. Add PostRepository beside the route
      tests 2 passed | ruff same | mypy same | import-all 3 ok, 0 failed, 0 skipped
      names none lost | openapi same | change check OK
L1   2. Read published posts through PostRepository
      tests 2 passed | ruff same | mypy same | import-all 3 ok, 0 failed, 0 skipped
      names lost or changed app.main.published_posts | openapi same | change check FAIL public-signature; app/main.py: published_posts parameter 'request' became 'posts'; a caller passing it by name breaks
L1   end    identical to the shape's after (4 files)
```
