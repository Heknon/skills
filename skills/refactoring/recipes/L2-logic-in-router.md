# L2: rules out of a route

**End state:** the architecture skill's `shapes/L2-logic-in-router.md`:
the rule in a function of its own module, called once by the route; in
a codebase with a service layer, a method of the feature's service.
**Steps from the catalogue:** `steps/extract-function.md`, then
`steps/move-function.md`.

## Pins

The shape's test (3 cases: at the threshold, just under, another tier),
a probe that posts each and prints status, headers and body, and the
OpenAPI document. Search the names the rule reads (`TIERS`) in all files:
tests that patch or fill them are references of the move.

## Steps

### 1. Extract function: the rule into `quote_total`, in the same module

The same statements, with the route's local `total` turned into
returns. Nothing moves yet.

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -11,8 +11,12 @@ class QuoteIn(BaseModel):
 
 
+def quote_total(customer: str, subtotal_cents: int) -> int:
+    """Gold customers get 10% off orders of 100.00 or more."""
+    if TIERS.get(customer) == "gold" and subtotal_cents >= 10_000:
+        return subtotal_cents * 90 // 100
+    return subtotal_cents
+
+
 @app.post("/quotes")
 def quote(body: QuoteIn) -> dict[str, int]:
-    total = body.subtotal_cents
-    if TIERS.get(body.customer) == "gold" and total >= 10_000:
-        total = total * 90 // 100
-    return {"total_cents": total}
+    return {"total_cents": quote_total(body.customer, body.subtotal_cents)}
```

Commit: `Extract the gold discount into quote_total`

### 2. Move function: `quote_total` and `TIERS` to `app/pricing.py`

`TIERS` goes with it: only the rule reads it. `public_names.py` then
shows `app.main.TIERS` gone. Nothing imported it from `app.main` here;
where something does, keep `from app.pricing import TIERS as TIERS` in
`app/main.py` and read the Traps.

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -2,6 +2,7 @@ from fastapi import FastAPI
 from pydantic import BaseModel
 
+from app.pricing import quote_total
+
 app = FastAPI()
-TIERS = {"ada": "gold", "bob": "basic"}
 
 
@@ -11,11 +12,4 @@ class QuoteIn(BaseModel):
 
 
-def quote_total(customer: str, subtotal_cents: int) -> int:
-    """Gold customers get 10% off orders of 100.00 or more."""
-    if TIERS.get(customer) == "gold" and subtotal_cents >= 10_000:
-        return subtotal_cents * 90 // 100
-    return subtotal_cents
-
-
 @app.post("/quotes")
 def quote(body: QuoteIn) -> dict[str, int]:
diff --git a/app/pricing.py b/app/pricing.py
new file mode 100644
--- /dev/null
+++ b/app/pricing.py
@@ -0,0 +1,8 @@
+TIERS = {"ada": "gold", "bob": "basic"}
+
+
+def quote_total(customer: str, subtotal_cents: int) -> int:
+    """Gold customers get 10% off orders of 100.00 or more."""
+    if TIERS.get(customer) == "gold" and subtotal_cents >= 10_000:
+        return subtotal_cents * 90 // 100
+    return subtotal_cents
```

Commit: `Move quote_total and TIERS to app.pricing`

### 3. Add a test of the rule without HTTP

```diff
diff --git a/test_pricing.py b/test_pricing.py
new file mode 100644
--- /dev/null
+++ b/test_pricing.py
@@ -0,0 +1,5 @@
+from app.pricing import quote_total
+
+
+def test_gold_threshold():
+    assert quote_total("ada", 10_000) == 9_000
```

Commit: `Test quote_total without HTTP`

## When the codebase has services

The shape has no service layer, so the rule became a function. Where
the structure card shows services and providers (architecture's
`core/wiring.md`), the same route runs in three steps, each green:

1. the domain errors and their handlers, added before anything raises
   them (`L4-service-knows-http.md`);
2. the service class and its provider, unused; the provider takes the
   repository through the provider the tests already override:

   ```python
   def get_order_service(repo: Annotated[OrderRepository, Depends(get_repo)]) -> OrderService:
       return OrderService(repo)
   ```

3. the route calls the service through `Depends(get_order_service)`,
   and raises nothing itself.

*lab,* an orders route whose tests set
`app.dependency_overrides[get_repo]`: with the provider above, 4 passed
at every step, the tests unchanged, and a probe of status, headers and
body identical. With `OrderService(OrderRepository())` inside the
provider, the override no longer reached the repository: 3 of 4 tests
failed against the real data (409 where 201 was expected, 404 where 409
was). Overriding the new provider in `conftest.py` made them pass again,
which is patching forward: the route's real wiring was then untested.
With the `HTTPException` lines moved into the service, every test
passed, while a non-HTTP caller got `fastapi.exceptions.HTTPException:
409: credit limit exceeded: 1500 > 1000`.

## Traps seen in the lab

| Trap | What happened |
| --- | --- |
| a test patched the moved global: `monkeypatch.setattr(main, "TIERS", {...})` | after step 2: `AttributeError: ... has no attribute 'TIERS'`. With the re-export kept, it passed silently wrong: `{'total_cents': 10000}` instead of 9000, because the rule reads `app.pricing.TIERS`. Move the patch target to `app.pricing` in step 2. `monkeypatch.setitem(main.TIERS, ...)` kept working through the re-export: it changes the shared dict |
| seniority's change check | `OK` at every step: it does not report `TIERS` gone from `app.main`, a public module constant; the public-names comparison does |

## What the checks said (lab)

```
L2   start  tests 3 passed | ruff clean | mypy clean | import-all 2 ok, 0 failed, 0 skipped
L2   1. Extract the gold discount into quote_total
      tests 3 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names none lost | openapi same | change check OK
L2   2. Move quote_total and TIERS to app.pricing
      tests 3 passed | ruff same | mypy same | import-all 3 ok, 0 failed, 0 skipped
      names lost or changed app.main.TIERS | openapi same | change check OK
L2   3. Test quote_total without HTTP
      tests 4 passed | ruff same | mypy same | import-all 3 ok, 0 failed, 0 skipped
      names lost or changed app.main.TIERS | openapi same | change check OK
L2   end    identical to the shape's after (4 files)
```
