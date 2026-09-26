# Finding each violation

**Verdict you produce:** findings by ID with `path:line`, what the card
allows, and a verdict for the change or codebase.

```
card:      <the lines of the structure card that decide exceptions>
findings:  [ID] path:line  what; scenario; suggested severity
allowed:   <hits the card allows, and which card line allows them>
seen:      <violations present before the change, not part of it>
missed:    <what the searches cannot see, from the tables below>
verdict:   <no layering findings | findings: IDs>
```

## Steps

1. Structure card first (`core/recognise.md`). Collect the file sets the
   searches run on:

   ```
   route files       files with ^\s*@\w+\.(get|post|put|patch|delete|api_route)\(
   service files     service*.py, services/**
   repository files  repositor*.py, repositories/**, crud*.py, dal*.py, store*.py
   lower files       the repository files plus models*.py, domain*.py, db.py
   database models   names from ^class\s+(\w+)\((Document|Base|DeclarativeBase|SQLModel)\b
   ```

2. For a change, read the diff first and run the searches on the files
   it touches; report only hits on lines it adds or changes.
3. Run each ID's search below on its file set, excluding `.venv`,
   `site-packages` and tests unless the row says tests. Every hit is a
   lead: open the line and decide.
4. For each confirmed hit, check the card exceptions
   (`violations.md`); what is allowed goes under `allowed`.
5. Write each finding with a failure scenario; a finding without one is
   at most the suggested severity.

## The searches

The editor's `grep` takes Rust regular expressions, one line at a time
(`skills/navigation/core/search-patterns.md`); the lab ran the same patterns
with ripgrep 14, which uses the same regex engine.

```
L1  route files       await [A-Z]\w*\.(find|find_one|find_all|find_many|get|aggregate|insert|insert_one|insert_many|delete_all|count)\(
                      \bsession\.(execute|scalars?|get|add|query)\(|\bselect\(
                      \.find\(\s*\{|\.find_one\(\s*\{|\.aggregate\(\s*\[
L2  route files       ^\s+if\b.*\.(status|state|tier|balance|role|limit|total|kind|type)\b
                      and: two or more Depends(...) of repositories in one route (read)
L3  route files       ->\s*(list\[)?(User|Order)\b          with the database model names
                      response_model\s*=\s*(list\[)?(User|Order)\b
                      :\s*(User|Order)\s*[,)=]
                      a route with no return annotation: search the decorators,
                      read the def line under each; no "->" and no response_model is a lead
L4  service files     ^\s*(from|import)\s+(fastapi|starlette)\b|HTTPException|\bRequest\b|\bstatus_code\b
L5  routes, services, repositories
                      \.commit\(\)|\.rollback\(\)
    repositories, services
                      sessionmaker\(|AsyncSession\(|Session\(\)|start_session\(
L6  repository files  ->\s*(list\[)?(dict|Any|Row|Result|Select|Cursor)\b
                      get_pymongo_collection\(|get_motor_collection\(|\.mappings\(\)
L7  all non-test      ^\s+(from\s+\S+\s+import|import\s+\S+)        (function-level imports)
    lower files       ^\s*from\s+\S*\b(routers?|routes|api|services?|dependencies)\b\S*\s+import
    models, domain    ^\s*from\s+\S*\bschemas\b\S*\s+import
L8  routes, services  DuplicateKeyError|IntegrityError|pymongo\.errors|sqlalchemy\.exc|OperationFailure|BulkWriteError
    repositories      HTTPException
    all               ruff B904, if the project runs ruff (linting skill)
L9  all non-test      ^\w+\s*=\s*\w*(Repository|Service|Client|Store|Dao|DAO)\w*\(
    route files       ^\s+\w+\s*=\s*\w*(Repository|Service|Store)\(
    tests             dependency_overrides\[\s*[A-Z]
L10 placement/place-a-thing.md step 2, per kind: a definition in a file
    where no sibling of its kind lives while siblings exist elsewhere;
    file names errors.py and exceptions.py both present; a new utils*.py
L11 all non-test      raise\s+Exception\(|except\s+Exception\b|in\s+str\(\w+\)|str\(\w+\)\s*==|\.args\[0\]
    all               class\s+\w+\((\w+\.)?HTTPException\)
    all non-test      def __init__\(self,\s*\*\s*,
                      then read each exception class: __init__ without super().__init__,
                      or super().__init__ given only a message while __init__ takes fields
```

## What the lab found (*lab*, both recipes and fifteen sandboxes)

| Where | Hits |
| --- | --- |
| `recipes/sqlalchemy_service` | none |
| `recipes/beanie_service` | L5 `app/accounts/repository.py:81` `start_session(`: the unit of work's `transaction()`, which is its job. Allowed; a hit in any other repository method is session-per-call |
| review-diff (the eval's change) | L1 `router.py:18` `Invoice.find(...)` in `overdue_invoices`; L6 `repository.py:18` `-> list[dict]`; L8 `repository.py:1` and `:16` `HTTPException` in the repository. The forwarding `totals_by_customer` in the service: no hit, and the README's team rule allows it |
| transfer | L5 `repository.py:23` and `:33`, `commit()` in `debit` and `credit` |
| lazy-after-commit | L5 `repository.py:14`, `commit()` in `add` |
| circular | L7 `models.py:5` `from app.schemas import MemberOut` |
| wrong-override | L9 `tests/test_notes.py:13`, `:21`, keyed by the class; L6 `repository.py:12`, `get` returns a dict (real, small) |
| worker-pickle, utils-dump | L11 `except Exception`: the job runner's edge and a retry helper with `# noqa: BLE001`; both allowed, read the context |
| users-beanie with the leaky-user and mass-assign baits applied | L3 `body: User` in the PATCH, and the GET with no return annotation (found by the multiline form, ripgrep `-U`) |
| credit-limit with the bait applied | L4 `services/orders.py:1` `from fastapi import HTTPException` and the raise |
| errors-precedent with an error defined in the service, keyword-only | L11 `def __init__(self, *, invoice_id)`; L10 by `place-a-thing.md` (an exception class in `service.py` while `billing/errors.py` exists) |

## What the searches miss

| ID | Missed |
| --- | --- |
| L1 | a query in a helper function the route calls in the same file; an in-memory store accessed like a dict; a query through a lower-case module (`db.users.find(...)` is found only by the `{` form) |
| L2 | almost everything: logic is read, not searched. Read each route the change touches: more than parse, one call, map is a lead |
| L3 | a database model returned through a variable of another name with no annotation (the no-annotation lead catches the route, not the type); `dict(row)` or `row.__dict__` returned |
| L4 | HTTP knowledge through a helper module the service imports (`from app.web_utils import fail`); status codes as plain ints in a tuple |
| L5 | a commit hidden in a context manager or a helper (`async with session.begin()` inside a repository method is not matched: search `\.begin\(\)` in repositories too) |
| L6 | a repository that returns the `Document` (allowed only by the card, decision AR3); a `list` without a type annotation |
| L7 | cycles through three or more modules with top-level imports only: the app fails to start, so run it (`uv run python -c "import app.main"`), or import-linter if the project has it |
| L8 | a driver error caught as a base (`PyMongoError`, `SQLAlchemyError`, `Exception`) in a route: search those names too; translation done twice across two repositories |
| L9 | objects built in a provider but cached in a module global; `functools.lru_cache` on a provider (fine to override, `skills/api/fastapi/dependencies.md`) |
| L10 | everything the placement searches miss (`place-a-thing.md`) |
| L11 | an exception class whose base is not named `*Error`/`*Exception`; a caller that tests `e.args` through a helper |

## Tools that enforce some of this

If the project already runs them (the linting skill runs them; never add
them unasked): ruff `B904`, `BLE001`, `TRY002`, `N818`, `PLC0415`; an
import-linter contract (`recipes/*/pyproject.toml`,
`[tool.importlinter]`). *lab,* import-linter 2.15, a service importing
`fastapi`: `lint-imports` exited 1 and printed

```
app.accounts.service is not allowed to import fastapi:

-   app.accounts.service -> fastapi (l.2)
```
