# L3: a database row off the HTTP boundary

**End state:** the architecture skill's
`shapes/L3-db-model-at-boundary.md`: the repository maps the row to a
domain model while the session is open; the route maps the domain model
to the response schema. **Steps from the catalogue:** extract class
(domain model and repository, unused), the route switched, then what
nothing uses removed (`core/dead-code.md`).

## Pins

The shape's test, a probe of a found and a missing user, and the
OpenAPI document. If the before leaks a field or lets a client set one,
stop: that is a bug to fix first, as a behaviour change (architecture's
`core/boundary-models.md`). Search `dependency_overrides` for the
session provider (`get_session`): it decides step 2.

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

The shape's provider opens its own session. Where tests override the
session provider, write it as `get_users(s: Annotated[AsyncSession,
Depends(get_session)])` returning `UserRepository(s)` instead, so the
override still reaches the route (Traps), and keep `get_session`.

New finding: mypy `union-attr`

mypy now reports `Item "None" of "User | None" has no attribute "id"`
twice. It names a bug the before had and the shape leaves out: a
missing user is a 500 on both sides (probe: `2 500 Internal Server
Error` before and after; inside, `ResponseValidationError` before,
`AttributeError: 'NoneType' object has no attribute 'id'` after). The
step keeps the behaviour; the finding goes in the answer, with the fix
(a 404 through a domain error, architecture's `core/errors.md`) as its
own commit after the reshape. No `# type: ignore`.

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -56,4 +56,9 @@ async def get_session():
 
 
+async def get_users():
+    async with Session() as s:
+        yield UserRepository(s)
+
+
 class UserOut(BaseModel):
     model_config = ConfigDict(from_attributes=True)
@@ -62,5 +67,6 @@ class UserOut(BaseModel):
 
 
-@app.get("/users/{user_id}", response_model=UserOut)
-async def get_user(user_id: int, s: Annotated[AsyncSession, Depends(get_session)]):
-    return await s.scalar(select(UserRow).where(UserRow.id == user_id))   # the row itself
+@app.get("/users/{user_id}")
+async def get_user(user_id: int, users: Annotated[UserRepository, Depends(get_users)]) -> UserOut:
+    user = await users.get(user_id)
+    return UserOut(id=user.id, email=user.email)
```

Commit: `Map users to UserOut in the route, through UserRepository`

### 3. Remove what nothing uses now: `get_session` and `from_attributes`

A search for `get_session` and `from_attributes` in all files found
only these lines. Removing a provider is a removal: other code may
override or depend on it (`core/dead-code.md`).

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
@@ -51,9 +51,4 @@ app = FastAPI()
 
 
-async def get_session():
-    async with Session() as s:
-        yield s
-
-
 async def get_users():
     async with Session() as s:
@@ -61,6 +56,5 @@ async def get_users():
 
 
-class UserOut(BaseModel):
-    model_config = ConfigDict(from_attributes=True)
+class UserOut(BaseModel):                    # response schema
     id: int
     email: str
```

Commit: `Remove get_session and from_attributes, now unused`

## Traps seen in the lab

| Trap | What happened |
| --- | --- |
| a test overrode `get_session` with a session on its own database | green at step 1; after step 2 the override was silently unused and the route read the app's database: `assert {'id': 1, 'email': 'ada@example.com'} == {'id': 1, 'email': 'test@example.com'}`. With `get_users` taking `Depends(get_session)`: 2 passed |
| `response_model=UserOut` replaced by the return annotation `-> UserOut` | the OpenAPI document was identical |
| seniority's change check | step 2: `get_user parameter 's' became 'users'`, a route parameter FastAPI fills; step 3: `get_session was removed or renamed`, which is real and named in the commit |

## What the checks said (lab)

```
L3   start  tests 1 passed | ruff clean | mypy clean | import-all 2 ok, 0 failed, 0 skipped
L3   1. Add the User domain model and UserRepository
      tests 1 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names none lost | openapi same | change check OK
L3   2. Map users to UserOut in the route, through UserRepository
      tests 1 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped | new finding, declared: mypy union-attr
      names lost or changed app.main.get_user | openapi same | change check FAIL public-signature; app/main.py: get_user parameter 's' became 'users'; a caller passing it by name breaks
L3   3. Remove get_session and from_attributes, now unused
      tests 1 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names lost or changed app.main.ConfigDict, app.main.get_session, app.main.get_user | openapi same | change check FAIL public-signature; app/main.py: get_session was removed or renamed; app/main.py: get_user parameter 's' became 'users'; a caller passing it by name breaks
L3   end    identical to the shape's after (2 files)
```
