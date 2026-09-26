# L7: an import that points up, removed

**End state:** the architecture skill's `shapes/L7-imports-point-up.md`:
the mapping lives on the higher side (`MemberOut.from_member`), and the
lower module imports nothing from the higher one. **Steps:** the new
mapper added unused, the callers moved, the old method and its hidden
import removed.

## Pins

The shape's test. Search every caller of the method that holds the
hidden import (`\.to_out\(`), in all files: it is public, so it is
removed only when every caller is in this repository and moved
(`core/public-surface.md`). ruff's `PLC0415` finds the hidden import:
`import` should be at the top-level of a file.

## Steps

### 1. Add the mapper on the higher side, not used yet

```diff
diff --git a/app/schemas.py b/app/schemas.py
--- a/app/schemas.py
+++ b/app/schemas.py
@@ -14,2 +14,6 @@ class MemberOut(BaseModel):
     id: int
     name: str
+
+    @classmethod
+    def from_member(cls, member: Member) -> "MemberOut":
+        return cls(id=member.id, name=member.name)
```

Commit: `Add MemberOut.from_member`

### 2. Move the caller to the new mapper

```diff
diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -1,5 +1,5 @@
-from app.schemas import MemberIn
+from app.schemas import MemberIn, MemberOut
 
 
 def create(name: str):
-    return MemberIn(name=name).to_member(1).to_out()
+    return MemberOut.from_member(MemberIn(name=name).to_member(1))
```

Commit: `Map members with MemberOut.from_member in create`

### 3. Remove `Member.to_out`, which nothing calls now, with the import that hid the cycle

With the direction test from the shape: it fails while the
function-level import exists, so it can only come in this step.
`PLC0415` goes away.

```diff
diff --git a/app/models.py b/app/models.py
--- a/app/models.py
+++ b/app/models.py
@@ -7,7 +7,2 @@ class Member:
     name: str
     password_hash: str
-
-    def to_out(self):
-        from app.schemas import MemberOut   # hides models -> schemas -> models
-
-        return MemberOut(id=self.id, name=self.name)
diff --git a/test_direction.py b/test_direction.py
new file mode 100644
--- /dev/null
+++ b/test_direction.py
@@ -0,0 +1,8 @@
+import ast
+import pathlib
+
+
+def test_models_import_no_schemas():
+    tree = ast.parse(pathlib.Path("app/models.py").read_text())
+    names = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
+    assert "app.schemas" not in names
```

Commit: `Remove Member.to_out and its function-level import`

## Traps seen in the lab

| Trap | What happened |
| --- | --- |
| the hidden import moved to the top of `models.py` instead | `ImportError: cannot import name 'MemberOut' from partially initialized module 'app.schemas' (most likely due to a circular import)` while collecting the tests. The cycle is fixed by moving the mapping, never the import |
| `to_out` removed before its caller moved | red: `AttributeError: 'Member' object has no attribute 'to_out'` |
| seniority's change check | step 3: `Member.to_out was removed or renamed`. True, and asked for: name it in the answer, with the search that found no other caller |

## What the checks said (lab)

```
L7   start  tests 1 passed | ruff {'PLC0415': 1} | mypy clean | import-all 4 ok, 0 failed, 0 skipped
L7   1. Add MemberOut.from_member
      tests 1 passed | ruff same | mypy same | import-all 4 ok, 0 failed, 0 skipped
      names none lost | change check OK
L7   2. Map members with MemberOut.from_member in create
      tests 1 passed | ruff same | mypy same | import-all 4 ok, 0 failed, 0 skipped
      names none lost | change check OK
L7   3. Remove Member.to_out and its function-level import
      tests 2 passed | ruff -PLC0415 | mypy same | import-all 4 ok, 0 failed, 0 skipped
      names lost or changed app.models.Member.to_out, app.schemas.Member.to_out | change check FAIL public-signature; app/models.py: Member.to_out was removed or renamed
L7   end    identical to the shape's after (5 files)
```
