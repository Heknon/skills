# L4: HTTP out of a service

**End state:** the architecture skill's
`shapes/L4-service-knows-http.md`: the service raises a domain error;
one handler per category turns it into the same response at the edge.
**Steps:** the errors added unused, the handler registered, then the
raise changed; each keeps every response the same.

## Pins

The shape's test, a probe of the success and the refused request that
prints status, headers and body, and the OpenAPI document. Search every
caller of the service that catches `HTTPException` (`except
HTTPException`, `except Exception`): step 3 changes what they get.

## Steps

### 1. Add the domain errors, not raised yet

Where the codebase keeps its errors (architecture's
`placement/custom-errors.md`); the fields go to `super().__init__`.

```diff
diff --git a/app/errors.py b/app/errors.py
new file mode 100644
--- /dev/null
+++ b/app/errors.py
@@ -0,0 +1,16 @@
+class AppError(Exception):
+    pass
+
+
+class ConflictError(AppError):
+    pass
+
+
+class OutOfStockError(ConflictError):
+    def __init__(self, sku: str, available: int) -> None:
+        super().__init__(sku, available)
+        self.sku = sku
+        self.available = available
+
+    def __str__(self) -> str:
+        return f"only {self.available} of {self.sku} left"
```

Commit: `Add AppError, ConflictError and OutOfStockError`

### 2. Register one handler for the category, before anything raises it

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -1,3 +1,6 @@
-from fastapi import FastAPI, HTTPException
+from fastapi import FastAPI, HTTPException, Request
+from fastapi.responses import JSONResponse
+
+from app.errors import ConflictError
 
 app = FastAPI()
@@ -13,4 +16,9 @@ class StockService:
 
 
+@app.exception_handler(ConflictError)
+async def conflict(request: Request, exc: ConflictError) -> JSONResponse:
+    return JSONResponse({"detail": str(exc)}, status_code=409)
+
+
 @app.post("/reservations/{sku}/{quantity}")
 def reserve(sku: str, quantity: int) -> dict[str, int]:
```

Commit: `Answer ConflictError with 409 and its message`

### 3. Raise the domain error in the service instead of `HTTPException`

The response is the same, headers included (probe identical:
`409 {'content-length': '33', 'content-type': 'application/json'}
{"detail":"only 1 of apple left"}`). Callers outside HTTP now get
`OutOfStockError`: change in this step every caller the search found
that catches `HTTPException` around the service, and say so in the
commit body.

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -1,6 +1,6 @@
-from fastapi import FastAPI, HTTPException, Request
+from fastapi import FastAPI, Request
 from fastapi.responses import JSONResponse
 
-from app.errors import ConflictError
+from app.errors import ConflictError, OutOfStockError
 
 app = FastAPI()
@@ -11,5 +11,5 @@ class StockService:
     def reserve(self, sku: str, quantity: int) -> int:
         if STOCK.get(sku, 0) < quantity:
-            raise HTTPException(409, f"only {STOCK.get(sku, 0)} of {sku} left")
+            raise OutOfStockError(sku, STOCK.get(sku, 0))
         STOCK[sku] -= quantity
         return STOCK[sku]
```

Commit: `Raise OutOfStockError from StockService`

### 4. Add a test of the service without HTTP

```diff
diff --git a/test_worker_caller.py b/test_worker_caller.py
new file mode 100644
--- /dev/null
+++ b/test_worker_caller.py
@@ -0,0 +1,11 @@
+import pytest
+
+from app.errors import AppError
+from app.main import STOCK, StockService
+
+
+def test_worker_can_catch_the_domain_error():
+    STOCK["pear"] = 0
+    with pytest.raises(AppError) as info:
+        StockService().reserve("pear", 1)
+    assert info.value.available == 0
```

Commit: `Test that a worker can catch the stock error by type`

## Traps seen in the lab

| Trap | What happened |
| --- | --- |
| step 3 done before step 2 | red: the test failed with `app.errors.OutOfStockError: only 1 of apple left` raised through TestClient; a client got 500. Undo, register the handler first |
| a worker that caught `HTTPException` around the service | before step 3 it skipped the row (`worker skipped the row: only 0 of pear left`); after it stopped with `app.errors.OutOfStockError: only 0 of pear left`. It is a caller of the service and changes in step 3 |
| seniority's change check | `OK` at every step |

## What the checks said (lab)

```
L4   start  tests 1 passed | ruff clean | mypy clean | import-all 2 ok, 0 failed, 0 skipped
L4   1. Add AppError, ConflictError and OutOfStockError
      tests 1 passed | ruff same | mypy same | import-all 3 ok, 0 failed, 0 skipped
      names none lost | openapi same | change check OK
L4   2. Answer ConflictError with 409 and its message
      tests 1 passed | ruff same | mypy same | import-all 3 ok, 0 failed, 0 skipped
      names none lost | openapi same | change check OK
L4   3. Raise OutOfStockError from StockService
      tests 1 passed | ruff same | mypy same | import-all 3 ok, 0 failed, 0 skipped
      names lost or changed app.main.HTTPException | openapi same | change check OK
L4   4. Test that a worker can catch the stock error by type
      tests 2 passed | ruff same | mypy same | import-all 3 ok, 0 failed, 0 skipped
      names lost or changed app.main.HTTPException | openapi same | change check OK
L4   end    identical to the shape's after (4 files)
```
