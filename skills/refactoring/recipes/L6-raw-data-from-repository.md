# L6: domain models out of a repository

**End state:** the architecture skill's
`shapes/L6-raw-data-from-repository.md`: the repository maps each raw
row to a small domain model inside itself; the route answers with a
response schema. **Steps:** the raw data typed, the models added unused,
the repository and its callers changed together, then the response
schema.

## Pins

The shape's test, a probe of the route, and the OpenAPI document.
Search every caller of the repository method (`\.open_totals\(`) and
every stored key they read (`\["_id"\]`): a changed return type breaks
each one, so all of them change in step 3. Many callers, or callers
outside the repository: add a new method beside the old one instead
(`steps/change-signature.md`, parallel change) and move them a group
per step.

## Steps

### 1. Type the raw documents

The before's list is `list[dict[str, object]]` to mypy, so every value
read from it is `object`: mypy reports `index` and `call-overload` on
the totals line. A `TypedDict` states the stored document's keys; the
two findings go, and a mistyped key becomes a finding (`typeddict-item`).
Nothing runs differently.

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -1,6 +1,16 @@
+from typing import TypedDict
+
 from fastapi import FastAPI
 
 app = FastAPI()
-INVOICES = [
+
+
+class InvoiceDoc(TypedDict):                 # a stored document's keys
+    customer_id: str
+    amount_cents: int
+    paid: bool
+
+
+INVOICES: list[InvoiceDoc] = [
     {"customer_id": "c1", "amount_cents": 500, "paid": False},
     {"customer_id": "c1", "amount_cents": 200, "paid": False},
```

Commit: `Type the stored invoices as InvoiceDoc`

### 2. Add the domain model and the row type, not used yet

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -2,4 +2,5 @@ from typing import TypedDict
 
 from fastapi import FastAPI
+from pydantic import BaseModel
 
 app = FastAPI()
@@ -12,4 +13,9 @@ class InvoiceDoc(TypedDict):                 # a stored document's keys
 
 
+class OpenTotalRow(TypedDict):               # one row of the aggregation
+    _id: str
+    open_cents: int
+
+
 INVOICES: list[InvoiceDoc] = [
     {"customer_id": "c1", "amount_cents": 500, "paid": False},
@@ -19,4 +25,9 @@ INVOICES: list[InvoiceDoc] = [
 
 
+class CustomerTotal(BaseModel):              # domain model
+    customer_id: str
+    open_cents: int
+
+
 class InvoiceRepository:
     def open_totals(self) -> list[dict]:
```

Commit: `Add the CustomerTotal domain model and the OpenTotalRow type`

### 3. Return domain models from the repository, and change its one caller with it

The rows are typed as `OpenTotalRow`, so the mapping line reads typed
values. *lab:* with untyped rows, mypy reported `Argument "customer_id"
to "CustomerTotal" has incompatible type "object"; expected "str"`
(`arg-type`) on that line; not a bug (pydantic checks the values at run
time), and not a finding to silence: the fix is the type, steps 1 and 2.

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -31,14 +31,15 @@ class CustomerTotal(BaseModel):              # domain model
 
 class InvoiceRepository:
-    def open_totals(self) -> list[dict]:
+    def open_totals(self) -> list[CustomerTotal]:
         totals: dict[str, int] = {}
         for inv in INVOICES:
             if not inv["paid"]:
                 totals[inv["customer_id"]] = totals.get(inv["customer_id"], 0) + inv["amount_cents"]
-        return [{"_id": c, "open_cents": t} for c, t in totals.items()]   # aggregation-shaped rows
+        rows: list[OpenTotalRow] = [{"_id": c, "open_cents": t} for c, t in totals.items()]
+        return [CustomerTotal(customer_id=r["_id"], open_cents=r["open_cents"]) for r in rows]
 
 
 @app.get("/open-totals")
 def open_totals() -> list[dict]:
-    return [{"customer_id": r["_id"], "open_cents": r["open_cents"]}
-            for r in InvoiceRepository().open_totals()]
+    return [{"customer_id": t.customer_id, "open_cents": t.open_cents}
+            for t in InvoiceRepository().open_totals()]
```

Commit: `Return CustomerTotal from InvoiceRepository.open_totals`

### 4. Answer with a response schema

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
@@ -40,6 +40,10 @@ class InvoiceRepository:
 
 
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
L6   1. Type the stored invoices as InvoiceDoc
      tests 1 passed | ruff same | mypy -call-overload -index | import-all 2 ok, 0 failed, 0 skipped
      names none lost | openapi same | change check OK
L6   2. Add the CustomerTotal domain model and the OpenTotalRow type
      tests 1 passed | ruff same | mypy -call-overload -index | import-all 2 ok, 0 failed, 0 skipped
      names none lost | openapi same | change check OK
L6   3. Return CustomerTotal from InvoiceRepository.open_totals
      tests 1 passed | ruff same | mypy -call-overload -index | import-all 2 ok, 0 failed, 0 skipped
      names lost or changed app.main.InvoiceRepository.open_totals | openapi same | change check OK
L6   4. Answer /open-totals with CustomerTotalOut
      tests 1 passed | ruff same | mypy -call-overload -index | import-all 2 ok, 0 failed, 0 skipped
      names lost or changed app.main.InvoiceRepository.open_totals, app.main.open_totals | openapi CHANGED | change check OK
L6   end    identical to the shape's after (2 files)
```
