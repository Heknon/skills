# L8: a driver error translated once, in the repository

**End state:** the architecture skill's
`shapes/L8-untranslated-db-error.md`: the repository catches the
driver's error at the statement that raises it and raises a domain
error `from` it; one handler maps the category to a status. **Steps:**
the errors added unused, the handler registered, the repository
translating, then the route's `try` removed.

## Pins

The shape's test (a duplicate answers 409 with the same body), a probe
of both requests, the OpenAPI document. Search every `except` of the
driver's error above the repository (`except IntegrityError`,
`except DuplicateKeyError`): each one is removed in the last step.

## Steps

### 1. Add the domain errors, not raised yet

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -8,4 +8,17 @@ from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
 
 
+class ConflictError(Exception):
+    pass
+
+
+class DuplicateEmailError(ConflictError):
+    def __init__(self, email: str) -> None:
+        super().__init__(email)
+        self.email = email
+
+    def __str__(self) -> str:
+        return "email already registered"
+
+
 class Base(DeclarativeBase):
     pass
```

Commit: `Add ConflictError and DuplicateEmailError`

### 2. Register the handler, before anything raises the error

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -1,5 +1,6 @@
 import asyncio
 
-from fastapi import FastAPI, HTTPException
+from fastapi import FastAPI, HTTPException, Request
+from fastapi.responses import JSONResponse
 from pydantic import BaseModel
 from sqlalchemy.exc import IntegrityError
@@ -43,4 +44,9 @@ app = FastAPI()
 
 
+@app.exception_handler(ConflictError)
+async def conflict(request: Request, exc: ConflictError) -> JSONResponse:
+    return JSONResponse({"detail": str(exc)}, status_code=409)
+
+
 class UserIn(BaseModel):
     email: str
```

Commit: `Answer ConflictError with 409 and its message`

### 3. Translate the driver error in the repository

`from exc` keeps the driver's message in the log; without it ruff
reports `B904 Within an except clause, raise exceptions with raise ...
from err or raise ... from None`. The route's `except IntegrityError`
is now never reached; the handler answers the same 409.

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -58,5 +58,8 @@ class UserRepository:
             row = UserRow(email=email)
             s.add(row)
-            await s.flush()
+            try:
+                await s.flush()
+            except IntegrityError as exc:             # translated once, here
+                raise DuplicateEmailError(email) from exc
             return row.id
 
```

Commit: `Raise DuplicateEmailError from UserRepository.add`

### 4. Remove the route's `try`, which nothing reaches now

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -1,5 +1,5 @@
 import asyncio
 
-from fastapi import FastAPI, HTTPException, Request
+from fastapi import FastAPI, Request
 from fastapi.responses import JSONResponse
 from pydantic import BaseModel
@@ -67,6 +67,3 @@ class UserRepository:
 @app.post("/users", status_code=201)
 async def create_user(body: UserIn) -> dict[str, int]:
-    try:
-        return {"id": await UserRepository().add(body.email)}
-    except IntegrityError as exc:                     # driver error in the route
-        raise HTTPException(409, "email already registered") from exc
+    return {"id": await UserRepository().add(body.email)}
```

Commit: `Remove the IntegrityError handling from create_user`

## Traps seen in the lab

| Trap | What happened |
| --- | --- |
| step 3 done before step 2 | red: `FAILED test_shape.py::test_duplicate_email_is_409 - app.main.DuplicateEmailError`, a 500 to a client: the route caught only `IntegrityError`, and no handler knew the new error |
| the domain error raised without `from exc` | ruff `B904` on that line |
| seniority's change check | `OK` at every step: the new `except` re-raises |

## What the checks said (lab)

```
L8   start  tests 1 passed | ruff clean | mypy clean | import-all 2 ok, 0 failed, 0 skipped
L8   1. Add ConflictError and DuplicateEmailError
      tests 1 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names none lost | openapi same | change check OK
L8   2. Answer ConflictError with 409 and its message
      tests 1 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names none lost | openapi same | change check OK
L8   3. Raise DuplicateEmailError from UserRepository.add
      tests 1 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names none lost | openapi same | change check OK
L8   4. Remove the IntegrityError handling from create_user
      tests 1 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names lost or changed app.main.HTTPException | openapi same | change check OK
L8   end    identical to the shape's after (2 files)
```
