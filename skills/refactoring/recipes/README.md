# Recipes: from a layering violation to its shape

A recipe is the way from one of the architecture skill's violations
(`skills/architecture/checklist/violations.md`, IDs L1 to L11) to the
shape that fixes it, as catalogue steps, each green and committed. The
architecture skill owns the end state: `skills/architecture/shapes/`
holds, per ID, a before, an after and a test both pass. A recipe never
restates that end state; it holds the steps between and the traps seen
on the way. Each recipe was replayed from the shape's before to its
after, with every check run after every step (`run_recipes.py`).

**Verdict you produce:**

```
violation: <ID> at <path:line>
end state: skills/architecture/shapes/<file>, in this codebase's names (the structure card)
pins:      tests <summary>; probe .ledger/probe.py; OpenAPI .ledger/openapi-before.json
steps:     <n>. <recipe step>: <hash> <subject>; <checks summary>
contract:  <OpenAPI and probe identical | changed: <what>, in <hash>, and why>
findings:  <bugs the shape leaves as they are, and checker findings that name them>
verdict reshape: <at the shape | stopped after step <n>: <why>>
```

## Which recipe

| The ask, or the finding | ID | Recipe |
| --- | --- | --- |
| a query built in a route; "add a repository" | L1 | `L1-query-in-route.md` |
| rules in a route; "move the logic into a service" | L2 | `L2-logic-in-router.md` |
| a database row returned or accepted by a route; "separate the DB and API models" | L3 | `L3-db-model-at-boundary.md` |
| `HTTPException` or `fastapi` in a service | L4 | `L4-service-knows-http.md` |
| commits in a repository; "make the transfer atomic" | L5 | `L5-split-transaction.md` (its last step changes behaviour) |
| a repository that returns dicts, rows or cursors | L6 | `L6-raw-data-from-repository.md` |
| a circular import, or an import inside a function to hide one | L7 | `L7-imports-point-up.md` |
| a driver error caught in a route | L8 | `L8-untranslated-db-error.md` |
| a repository or client built at import; "make it swappable in tests" | L9 | `L9-unswappable-dependency.md` |
| an error, constant or helper kept apart from its kind | L10 | `L10-placed-against-precedent.md` |
| `raise Exception(...)`, or a caller that reads `str(e)` | L11 | `L11-unhandleable-exception.md` |

A code-review finding cites the ID; so does architecture's check. A
layout migration (layer folders to feature folders) has no ID and no
recipe: architecture's invariant is to follow the codebase's layout,
never to migrate it unasked. If asked, plan it as **Plan** and move one
module per step (`steps/move-module.md`).

## Before the first step

1. **Recognise the codebase** with architecture's `core/recognise.md`.
   The recipes use the shapes' names and single files; your files,
   names and layers come from the structure card. Add no layer the
   codebase lacks (architecture's invariant 3).
2. **`core/before-you-start.md`**, as for any refactoring. For code
   behind HTTP the probe calls the routes and prints status, headers and
   body; `raise_server_exceptions=False` prints a 500 instead of raising
   it in the probe:

   ```python
   import sys
   sys.path[:0] = ["", "src"]

   from fastapi.testclient import TestClient

   from app.main import app

   client = TestClient(app, raise_server_exceptions=False)
   for path in ["/users/1", "/users/2"]:
       r = client.get(path)
       print(path, r.status_code, dict(r.headers), r.text)
   ```

   Call every route the recipe touches, with the inputs that reach each
   branch: found, missing, refused. Keep it in `.ledger/`.
3. **Dump the OpenAPI document** with the api skill's tool, before the
   first step and after each step that touches a route
   (`skills/api/fastapi/openapi.md`, "Diff two versions").
4. **Search what the steps will change**, all files: the providers
   tests override (`dependency_overrides\[`), the globals tests patch
   (`monkeypatch.setattr`, `mock.patch`, `setitem`), and the callers
   that catch an exception type a step changes (`except HTTPException`,
   `except Exception`). Each hit is a reference (`core/every-reference.md`).

## Rules every recipe follows

| Rule | Lab evidence |
| --- | --- |
| Add the new place unused, then switch the callers, then remove the old | every recipe; every commit green |
| Register a handler before anything raises its error | L4: the service raised first; the test got `app.errors.OutOfStockError: only 1 of apple left`, a client 500 |
| A new provider takes, through `Depends`, the provider the tests override | L3: an override of `get_session` stopped reaching the route; chained, 2 passed |
| Never build a repository or service at import | L1: a test that set `app.state.rows` got the rows from import time |
| A global that tests patch is a reference: move the patch in the step that moves the global | L2, L9: `AttributeError: ... has no attribute 'TIERS'` |
| A step that changes behaviour is its own commit, with a test that failed first | L5 |
| A new type-checker finding about behaviour the code already had is a finding: keep the behaviour, make it explicit, report it, never silence it | L3: `union-attr` on the missing user, a 500 before and after; an explicit `raise` keeps the 500 and clears it |

## What the checks say on a reshape

- **Tests and probe**: identical after every step of every recipe,
  except L5's last step, which is a behaviour change on purpose.
- **OpenAPI**: identical in every recipe except L6 step 4, where the
  response gains a named schema.
- **Public names**: a route's line changes whenever its parameters do
  (`app.main.get_user`); names only imported (`HTTPException`,
  `ConfigDict`) go. Explain each; nobody calls a route by keyword.
- **Seniority's change check**, when a harness runs it
  (`reference/change-check.md`): it reports a route's changed or added
  parameter as a broken signature (L1, L3, L9), and a narrowed `except`
  as a new swallowed error (L11); neither is. It reports the removal of
  a method (L7), which is real and named in the answer. It does not see a public module constant or variable removed
  (L2 `TIERS`, L9 `rates`); `tools/public_names.py` does.

## How they were run

```powershell
cd <skill>\recipes
uv run python run_recipes.py                  # every recipe, from the shapes beside this skill
uv run python run_recipes.py L3 --shapes <architecture>\shapes --harness <repo>\harness\seniority-checks\check_change.py
```

`run_recipes.py` writes the shape's before into a new git repository,
applies each step's diff, runs pytest, ruff (`E4,E7,E9,F,B,PLC0415,
TRY002`), mypy, `tools/import_all.py`, `tools/public_names.py` and the
OpenAPI dump after each one, commits it, and checks that the last tree
is the shape's after, byte for byte. Its output for each recipe is at
the end of the recipe. *lab:* Python 3.12.14, FastAPI 0.141.1
(Starlette 1.7.0), pydantic 2.13.5, SQLAlchemy 2.1.1 on aiosqlite
0.22.1, pytest 9.1.1, ruff 0.16.9, mypy 2.3.1, git 2.43.0: every recipe
green and at its after. The PowerShell lines are *not run on Windows*.
