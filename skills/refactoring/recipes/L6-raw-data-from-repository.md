# L6: domain models out of a repository

**End state:** the architecture skill's
`shapes/L6-raw-data-from-repository.md`: the repository maps each raw
row to a small domain model inside itself; the route answers with a
response schema. **Steps:** the model added unused, the repository and
its callers changed together, then the response schema.

## Pins

The shape's test, a probe of the route, and the OpenAPI document.
Search every caller of the repository method (`\.open_totals\(`) and
every stored key they read (`\["_id"\]`): a changed return type breaks
each one, so all of them change in step 2. Many callers, or callers
outside the repository: add a new method beside the old one instead
(`steps/change-signature.md`, parallel change) and move them a group
per step.

## Steps

### 1. Add the domain model, not used yet

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -1,3 +1,4 @@
 from fastapi import FastAPI
+from pydantic import BaseModel
 
 app = FastAPI()
@@ -9,4 +10,9 @@ INVOICES = [
 
 
+class CustomerTotal(BaseModel):              # domain model
+    customer_id: str
+    open_cents: int
+
+
 class InvoiceRepository:
     def open_totals(self) -> list[dict]:
```

Commit: `Add the CustomerTotal domain model`

### 2. Return domain models from the repository, and change its one caller with it

New finding: mypy `arg-type`

mypy reports `Argument "customer_id" to "CustomerTotal" has incompatible
type "object"; expected "str"` on the mapping line: the raw rows are
`dict[str, object]`, and this line is where the untyped data meets the
model. pydantic checks the values at run time (the test passes). It
was already there in another form: the before has two mypy errors on
the same raw data (`index`, `call-overload`). Report it; the fix is a
typed row, not an ignore.

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -16,14 +16,15 @@ class CustomerTotal(BaseModel):              # domain model
 
 class InvoiceRepository:
-    def open_totals(self) -> list[dict]:
+    def open_totals(self) -> list[CustomerTotal]:
         totals: dict[str, int] = {}
         for inv in INVOICES:
             if not inv["paid"]:
                 totals[inv["customer_id"]] = totals.get(inv["customer_id"], 0) + inv["amount_cents"]
-        return [{"_id": c, "open_cents": t} for c, t in totals.items()]   # aggregation-shaped rows
+        rows = [{"_id": c, "open_cents": t} for c, t in totals.items()]
+        return [CustomerTotal(customer_id=r["_id"], open_cents=r["open_cents"]) for r in rows]
 
 
 @app.get("/open-totals")
 def open_totals() -> list[dict]:
-    return [{"customer_id": r["_id"], "open_cents": r["open_cents"]}
-            for r in InvoiceRepository().open_totals()]
+    return [{"customer_id": t.customer_id, "open_cents": t.open_cents}
+            for t in InvoiceRepository().open_totals()]
```

Commit: `Return CustomerTotal from InvoiceRepository.open_totals`

### 3. Answer with a response schema

The body is the same; the OpenAPI document is not. The response went
from `"items": {"additionalProperties": true, "type": "object"}` to
`"items": {"$ref": "#/components/schemas/CustomerTotalOut"}`, a new
schema with both fields `required`. That is a documented promise the
before did not make; whether clients care is the api skill's
(`core/compatibility.md`). Name it in the commit body.

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -25,6 +25,10 @@ class InvoiceRepository:
 
 
+class CustomerTotalOut(BaseModel):           # response schema
+    customer_id: str
+    open_cents: int
+
+
 @app.get("/open-totals")
-def open_totals() -> list[dict]:
-    return [{"customer_id": t.customer_id, "open_cents": t.open_cents}
-            for t in InvoiceRepository().open_totals()]
+def open_totals() -> list[CustomerTotalOut]:
+    return [CustomerTotalOut(**t.model_dump()) for t in InvoiceRepository().open_totals()]
```

Commit: `Answer /open-totals with CustomerTotalOut`

## Traps seen in the lab

| Trap | What happened |
| --- | --- |
| the repository changed, its caller not | red: `TypeError: 'CustomerTotal' object is not subscriptable` in the route, a 500. The caller changes in the same step |
| seniority's change check | `OK` at every step: a changed return type is not a signature change to it. `tools/public_names.py` shows the line of `open_totals` changed |

## What the checks said (lab)

```
L6   start  tests 1 passed | ruff clean | mypy {'index': 1, 'call-overload': 1} | import-all 2 ok, 0 failed, 0 skipped
L6   1. Add the CustomerTotal domain model
      tests 1 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names none lost | openapi same | change check OK
L6   2. Return CustomerTotal from InvoiceRepository.open_totals
      tests 1 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped | new finding, declared: mypy arg-type
      names lost or changed app.main.InvoiceRepository.open_totals | openapi same | change check OK
L6   3. Answer /open-totals with CustomerTotalOut
      tests 1 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names lost or changed app.main.InvoiceRepository.open_totals, app.main.open_totals | openapi CHANGED | change check OK
L6   end    identical to the shape's after (2 files)
```
