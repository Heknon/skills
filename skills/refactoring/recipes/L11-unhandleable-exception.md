# L11: an exception callers can catch by type

**End state:** the architecture skill's
`shapes/L11-unhandleable-exception.md`: a class under the codebase's
category, its fields passed to `super().__init__`, its message built in
`__str__`; callers catch the class, not the message. **Steps:** the
classes added unused, the raise changed, then each caller.

## Pins

The shape's tests (the message is kept), and a probe that prints the
type, the message and `e.args` of each error. Search every place that
reads the message (`in str(e)`, `str(exc) ==`, `match=`), and every
`except Exception` and `e.args` around the function.

## Steps

### 1. Add the error classes, not raised yet

With the shape's pickle test: the class is pinned before anything
raises it.

```diff
diff --git a/app/orders.py b/app/orders.py
--- a/app/orders.py
+++ b/app/orders.py
@@ -2,4 +2,19 @@ ORDERS = {1: "open"}
 
 
+class NotFoundError(Exception):
+    pass
+
+
+class OrderNotFoundError(NotFoundError):
+    code = "order_not_found"
+
+    def __init__(self, order_id: int) -> None:
+        super().__init__(order_id)
+        self.order_id = order_id
+
+    def __str__(self) -> str:
+        return f"order {self.order_id} not found"
+
+
 def order_status(order_id: int) -> str:
     if order_id not in ORDERS:
diff --git a/test_pickle.py b/test_pickle.py
new file mode 100644
--- /dev/null
+++ b/test_pickle.py
@@ -0,0 +1,8 @@
+import pickle
+
+from app.orders import OrderNotFoundError
+
+
+def test_round_trip():
+    e = pickle.loads(pickle.dumps(OrderNotFoundError(7)))
+    assert (type(e), e.order_id, str(e)) == (OrderNotFoundError, 7, "order 7 not found")
```

Commit: `Add NotFoundError and OrderNotFoundError`

### 2. Raise the class instead of `Exception`, with the same message

This changes what an in-process caller sees, and the commit body says
so: the type becomes a subclass of `Exception` (every `except
Exception` still catches it), `str(e)` is the same, and `e.args` goes
from `('order 7 not found',)` to `(7,)` (probe). Search showed no
caller of `e.args`; with one, stop and ask.

```diff
diff --git a/app/orders.py b/app/orders.py
--- a/app/orders.py
+++ b/app/orders.py
@@ -19,5 +19,5 @@ class OrderNotFoundError(NotFoundError):
 def order_status(order_id: int) -> str:
     if order_id not in ORDERS:
-        raise Exception(f"order {order_id} not found")
+        raise OrderNotFoundError(order_id)
     return ORDERS[order_id]
 
```

Commit: `Raise OrderNotFoundError for an unknown order`

### 3. Catch the class instead of reading the message

The same answers for every input the probe tried: `status_or_none(1)`
is `'open'`, `status_or_none(7)` is `None`.

```diff
diff --git a/app/orders.py b/app/orders.py
--- a/app/orders.py
+++ b/app/orders.py
@@ -26,6 +26,4 @@ def status_or_none(order_id: int) -> str | None:
     try:
         return order_status(order_id)
-    except Exception as e:
-        if "not found" in str(e):              # parses the message
-            return None
-        raise
+    except OrderNotFoundError:
+        return None
```

Commit: `Catch OrderNotFoundError in status_or_none`

## Traps seen in the lab

| Trap | What happened |
| --- | --- |
| the class without `__str__` | the message became `'7'`: the pickle test failed with `'7' != 'order 7 not found'`, and so would any caller that logs or shows it |
| seniority's change check | step 3: `swallowed-errors: status_or_none has 1 new except block(s) that do not re-raise`. The old handler swallowed the same case and re-raised the rest; the new one catches only that case. Cite both handlers in the answer |

## What the checks said (lab)

```
L11  start  tests 2 passed | ruff {'TRY002': 1} | mypy clean | import-all 2 ok, 0 failed, 0 skipped
L11  1. Add NotFoundError and OrderNotFoundError
      tests 3 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names none lost | change check OK
L11  2. Raise OrderNotFoundError for an unknown order
      tests 3 passed | ruff -TRY002 | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names none lost | change check OK
L11  3. Catch OrderNotFoundError in status_or_none
      tests 3 passed | ruff -TRY002 | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names none lost | change check FAIL swallowed-errors; app/orders.py: status_or_none has 1 new except block(s) that do not re-raise; an error that used to stop the program is now hidden
L11  end    identical to the shape's after (3 files)
```
