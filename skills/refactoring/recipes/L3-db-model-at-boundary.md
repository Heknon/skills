# L3: a database row off the HTTP boundary

**End state:** the architecture skill's
`shapes/L3-db-model-at-boundary.md`: the repository maps the row to a
domain model while the session is open; the route maps the domain model
to the response schema. **Steps from the catalogue:** extract class
(domain model and repository, unused), the route switched through a
provider chained on `get_session`, then what nothing uses removed
(`core/dead-code.md`).

## Pins

The shape's test, a probe of a found and a missing user, and the
OpenAPI document. If the before leaks a field or lets a client set one,
stop: that is a bug to fix first, as a behaviour change (architecture's
`core/boundary-models.md`). Search `dependency_overrides` for the
session provider (`get_session`): each hit is a test that step 2 must
keep reaching the route. The shape's second test is one.

## Steps

### 1. Add the domain model and the repository, not used yet

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -20,4 +20,21 @@ class UserRow(Base):
 
 
+class User(BaseModel):                       # domain model
+    id: int
+    email: str
+    password_hash: str
+
+
+class UserRepository:
+    def __init__(self, session: AsyncSession) -> None:
+        self.session = session
+
+    async def get(self, user_id: int) -> User | None:
+        row = await self.session.scalar(select(UserRow).where(UserRow.id == user_id))
+        if row is None:
+            return None
+        return User(id=row.id, email=row.email, password_hash=row.password_hash)
+
+
 engine = create_async_engine("sqlite+aiosqlite://")
 Session = async_sessionmaker(engine, expire_on_commit=False)
```

Commit: `Add the User domain model and UserRepository`

### 2. Route through the repository and map to the response schema

The new provider takes `get_session` through `Depends` and builds the
repository on that session; it never opens its own. A test's override
of `get_session` then still reaches the route (Traps).

The route checks for `None` before it reads the user. Without that
line, mypy reports `Item "None" of "User | None" has no attribute
"id"` (`union-attr`), twice. It names a bug the before had: a missing
user is a 500 on both sides (probe: `/users/2 500`, headers and body
`Internal Server Error` identical; inside, `ResponseValidationError`
before, `LookupError: user 2 not found` after). The `raise` keeps that
behaviour and says so; a `# type: ignore` or a `cast` would hide it
(`core/checks.md`). The bug goes in the answer, with its fix (a 404
through a domain error, architecture's `core/errors.md`) as its own
commit after the reshape.

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -56,4 +56,8 @@ async def get_session():
 
 
+async def get_users(s: Annotated[AsyncSession, Depends(get_session)]) -> UserRepository:
+    return UserRepository(s)
+
+
 class UserOut(BaseModel):
     model_config = ConfigDict(from_attributes=True)
@@ -62,5 +66,8 @@ class UserOut(BaseModel):
 
 
-@app.get("/users/{user_id}", response_model=UserOut)
-async def get_user(user_id: int, s: Annotated[AsyncSession, Depends(get_session)]):
-    return await s.scalar(select(UserRow).where(UserRow.id == user_id))   # the row itself
+@app.get("/users/{user_id}")
+async def get_user(user_id: int, users: Annotated[UserRepository, Depends(get_users)]) -> UserOut:
+    user = await users.get(user_id)
+    if user is None:   # a 500 before the reshape too: a bug kept, fixed apart
+        raise LookupError(f"user {user_id} not found")
+    return UserOut(id=user.id, email=user.email)
```

Commit: `Map users to UserOut in the route, through UserRepository`

### 3. Remove what nothing uses now: `from_attributes`

A search for `from_attributes` and `ConfigDict` in all files found
only these lines. `get_session` stays: `get_users` and the tests'
overrides use it.

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -3,5 +3,5 @@ from typing import Annotated
 
 from fastapi import Depends, FastAPI
-from pydantic import BaseModel, ConfigDict
+from pydantic import BaseModel
 from sqlalchemy import select
 from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
@@ -60,6 +60,5 @@ async def get_users(s: Annotated[AsyncSession, Depends(get_session)]) -> UserRep
 
 
-class UserOut(BaseModel):
-    model_config = ConfigDict(from_attributes=True)
+class UserOut(BaseModel):                    # response schema
     id: int
     email: str
```

Commit: `Remove from_attributes, now unused`

## Traps seen in the lab

| Trap | What happened |
| --- | --- |
| a `get_users` that opened its own session | the shape's override test: green at step 1; after step 2 the override was silently unused and the route read the app's database: `{'email': 'ada@example.com'} != {'email': 'test@example.com'}`. With `get_users` taking `Depends(get_session)`: 2 passed |
| `get_session` removed as unused once the route no longer named it | the override test stopped at collection: `ImportError: cannot import name 'get_session' from 'app.main'`. Removing it is a removal (`core/dead-code.md`), and here it had users |
| `response_model=UserOut` replaced by the return annotation `-> UserOut` | the OpenAPI document was identical |
| seniority's change check | steps 2 and 3: `get_user parameter 's' became 'users'`, a route parameter FastAPI fills; nothing removed is reported, since `get_session` stays |

## What the checks said (lab)

```
L3   start  tests 2 passed | ruff clean | mypy clean | import-all 2 ok, 0 failed, 0 skipped
L3   1. Add the User domain model and UserRepository
      tests 2 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names none lost | openapi same | change check OK
L3   2. Map users to UserOut in the route, through UserRepository
      tests 2 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names lost or changed app.main.get_user | openapi same | change check FAIL public-signature; app/main.py: get_user parameter 's' became 'users'; a caller passing it by name breaks
L3   3. Remove from_attributes, now unused
      tests 2 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names lost or changed app.main.ConfigDict, app.main.get_user | openapi same | change check FAIL public-signature; app/main.py: get_user parameter 's' became 'users'; a caller passing it by name breaks
L3   end    identical to the shape's after (2 files)
```
