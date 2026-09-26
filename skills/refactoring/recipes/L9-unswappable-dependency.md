# L9: a module-level object made swappable

**End state:** the architecture skill's
`shapes/L9-unswappable-dependency.md`: a provider in `Depends`, built
per request, and tests that swap it by the provider's key. **Steps:** a
provider that returns the shared object, the route switched to it, then
the object built in the provider and the global removed.

## Pins

The shape's test and a probe. Search the global's name (`rates`) in all
files: every test that patches it (`monkeypatch.setattr(main, "rates",
...)`, `mock.patch("app.main.rates")`) and every writer of its state is
a reference of step 3.

## Steps

### 1. Add a provider that returns the shared object

It returns the same object, so nothing changes yet.

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -12,4 +12,8 @@ class RateRepository:
 
 rates = RateRepository()                     # built at import, shared by all
+
+
+def get_rates() -> RateRepository:
+    return rates
 app = FastAPI()
 
```

Commit: `Add get_rates, returning the shared RateRepository`

### 2. Take the repository through `Depends` in the route

A test that patches the global still works here: the provider reads the
module's `rates` at call time.

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -1,3 +1,5 @@
-from fastapi import FastAPI
+from typing import Annotated
+
+from fastapi import Depends, FastAPI
 from pydantic import BaseModel
 
@@ -25,4 +27,5 @@ class Price(BaseModel):
 
 @app.get("/convert/{currency}/{pence}")
-def convert(currency: str, pence: int) -> Price:
+def convert(currency: str, pence: int,
+            rates: Annotated[RateRepository, Depends(get_rates)]) -> Price:
     return Price(pence=pence, cents=pence * rates.rate(currency) // 100)
```

Commit: `Take the rates through Depends(get_rates) in convert`

### 3. Build it in the provider and remove the module-level object

Here a patch of the global stops working, and a write to the shared
object stops being shared between requests. Change each test found in
the search to `app.dependency_overrides[get_rates]`, cleared after the
test (the api skill's `fastapi/testing.md`), in this step.

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -13,9 +13,8 @@ class RateRepository:
 
 
-rates = RateRepository()                     # built at import, shared by all
+def get_rates() -> RateRepository:
+    return RateRepository()
 
 
-def get_rates() -> RateRepository:
-    return rates
 app = FastAPI()
 
```

Commit: `Build RateRepository per request in get_rates`

### 4. Add a test that swaps it by the provider's key

```diff
diff --git a/test_override.py b/test_override.py
new file mode 100644
--- /dev/null
+++ b/test_override.py
@@ -0,0 +1,16 @@
+from fastapi.testclient import TestClient
+
+from app.main import app, get_rates
+
+
+class FixedRates:
+    def rate(self, currency: str) -> int:
+        return 200
+
+
+def test_convert_with_a_fake():
+    app.dependency_overrides[get_rates] = FixedRates
+    try:
+        assert TestClient(app).get("/convert/EUR/10").json()["cents"] == 20
+    finally:
+        app.dependency_overrides.clear()
```

Commit: `Test convert with a fake behind get_rates`

## Traps seen in the lab

| Trap | What happened |
| --- | --- |
| a test with `monkeypatch.setattr(main, "rates", FixedRates())` | passed at the start and after steps 1 and 2; after step 3: `AttributeError: <module 'app.main' ...> has no attribute 'rates'`. Its patch is a reference of step 3 |
| seniority's change check | from step 2: `convert gained required parameter 'rates'; existing callers break`. FastAPI fills it; no caller passes it. From step 3 also `rates was removed or renamed`: real for a test that patches `app.main.rates`, which step 3's search moved to `app.dependency_overrides[get_rates]`. The answer names both findings and why each is safe |

## What the checks said (lab)

```
L9   start  tests 1 passed | ruff clean | mypy clean | import-all 2 ok, 0 failed, 0 skipped
L9   1. Add get_rates, returning the shared RateRepository
      tests 1 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names none lost | openapi same | change check OK
L9   2. Take the rates through Depends(get_rates) in convert
      tests 1 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names lost or changed app.main.convert | openapi same | change check FAIL public-signature; app/main.py: convert gained required parameter 'rates'; existing callers break
L9   3. Build RateRepository per request in get_rates
      tests 1 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names lost or changed app.main.convert, app.main.rates | openapi same | change check FAIL public-signature; app/main.py: rates was removed or renamed; app/main.py: convert gained required parameter 'rates'; existing callers break
L9   4. Test convert with a fake behind get_rates
      tests 2 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names lost or changed app.main.convert, app.main.rates | openapi same | change check FAIL public-signature; app/main.py: rates was removed or renamed; app/main.py: convert gained required parameter 'rates'; existing callers break
L9   end    identical to the shape's after (3 files)
```
