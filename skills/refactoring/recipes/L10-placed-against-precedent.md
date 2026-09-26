# L10: a thing moved to where its kind lives

**End state:** the architecture skill's
`shapes/L10-placed-against-precedent.md`: the error class in the
errors module, beside its siblings. **Step:** `steps/move-function.md`,
for a class. One step, because the old module still imports the class
it raises, which keeps the old import path working.

## Pins

The shape's test. Search the class name in all files: imports of the
old path (`from app.service import OrderNotFoundError`), `except`
clauses, patch targets, and anything pickled or queued with it
(`core/public-surface.md`).

## Steps

### 1. Move function (a class): `OrderNotFoundError` to `app/errors.py`

`app.service` imports it to raise it, so `from app.service import
OrderNotFoundError` still gives the same class. If the old module stops
using a moved name, write the import as `from app.errors import
OrderNotFoundError as OrderNotFoundError`: a plain unused import is
ruff `F401 [*]`, which `--fix` deletes (lab: `F401 [*]
app.errors.NotFoundError imported but unused` for an unused one).

```diff
diff --git a/app/errors.py b/app/errors.py
--- a/app/errors.py
+++ b/app/errors.py
@@ -11,2 +11,8 @@ class CustomerNotFoundError(NotFoundError):
         super().__init__(customer_id)
         self.customer_id = customer_id
+
+
+class OrderNotFoundError(NotFoundError):
+    def __init__(self, order_id: int) -> None:
+        super().__init__(order_id)
+        self.order_id = order_id
diff --git a/app/service.py b/app/service.py
--- a/app/service.py
+++ b/app/service.py
@@ -1,13 +1,7 @@
-from app.errors import NotFoundError
+from app.errors import OrderNotFoundError
 
 ORDERS = {1: "open"}
 
 
-class OrderNotFoundError(NotFoundError):      # defined where it is first raised
-    def __init__(self, order_id: int) -> None:
-        super().__init__(order_id)
-        self.order_id = order_id
-
-
 def order_status(order_id: int) -> str:
     if order_id not in ORDERS:
```

Commit: `Move OrderNotFoundError to app.errors`

## Traps seen in the lab

| Trap | What happened |
| --- | --- |
| an error pickled before the move | it loaded after the move, as `app.errors.OrderNotFoundError`, with `order_id` 7; the old path gave the same object (`same object: True`). New pickles name `app.errors` |
| seniority's change check | `OK`: it follows the import to the class's new place |

## What the checks said (lab)

```
L10  start  tests 1 passed | ruff clean | mypy clean | import-all 4 ok, 0 failed, 0 skipped
L10  1. Move OrderNotFoundError to app.errors
      tests 1 passed | ruff same | mypy same | import-all 4 ok, 0 failed, 0 skipped
      names lost or changed app.service.NotFoundError | openapi same | change check OK
L10  end    identical to the shape's after (4 files)
```
