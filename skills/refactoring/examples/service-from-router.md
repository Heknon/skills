# Worked example: logic out of a route into a service

Kind: Reshape (recipes L2 and L4), three steps. Outputs from a lab run
on Python 3.12.14, FastAPI 0.141.1 (Starlette 1.7.0), pytest 9.1.1,
ruff 0.16.9, mypy 2.3.1, git 2.43.0, commands run in PowerShell 7.5 on
Linux.

## The ask

> Move the business logic out of the POST /orders route in
> app/routes.py into a service. The nightly import will need the same
> rules.

`place_order` looks the customer up, prices the lines, gives gold
customers 10% off from 100.00, checks the credit limit, and saves the
order; it raises `HTTPException` 404 and 409 itself.

## Steps

1. **Before you start.** Baseline: `4 passed`, ruff `All checks
   passed!`, mypy `Success: no issues found in 7 source files`,
   `import_all: 5 ok, 0 failed, 0 skipped`. The structure card: a
   repository behind a provider (`get_repo` in `app/dependencies.py`),
   no service yet, no errors module. The search for what the steps
   change:

   ```powershell
   git grep -n -I -e "dependency_overrides" -e "HTTPException" -e "except "
   ```

   ```
   app/routes.py:33:        raise HTTPException(404, "unknown customer")
   app/routes.py:39:        raise HTTPException(409, f"credit limit exceeded: {owed} > {customer['credit_limit_cents']}")
   tests/conftest.py:32:    app.dependency_overrides[get_repo] = lambda: fake
   ```

   The tests swap the repository by `get_repo`: the new service must
   get its repository through that provider (`recipes/L2-logic-in-router.md`,
   "When the codebase has services"). The nightly job is a non-HTTP
   caller, so the service raises domain errors, not `HTTPException`
   (`recipes/L4-service-knows-http.md`).
2. **Pins.** A probe in `.ledger/probe.py` (`recipes/README.md`) that
   overrides `get_repo` with the tests' fake and prints status, headers
   and body for a gold order, one under the threshold, a refused one,
   an unknown customer, an empty order and a body without lines; and
   the OpenAPI document from the api skill's `openapi_dump.py`:

   ```
   c2 3 500 409 {'content-length': '47', 'content-type': 'application/json'} {"detail":"credit limit exceeded: 1500 > 1000"}
   c9 1 100 404 {'content-length': '29', 'content-type': 'application/json'} {"detail":"unknown customer"}
   wrote .ledger/openapi-before.json: OpenAPI 3.1.0, 1 paths, 1 operations
   ```

3. **Step 1: the errors and their handlers, unused.** `app/errors.py`
   with `AppError`, `NotFoundError`, `ConflictError`,
   `UnknownCustomerError` and `CreditLimitExceededError` (fields to
   `super().__init__`, the message in `__str__`), and one handler per
   category in `app/main.py`, registered before anything raises them.
4. **Step 2: the service and its provider, unused.** `OrderService.place`
   holds the same statements, raising the domain errors. The provider
   takes the repository through the provider the tests override:

   ```python
   def get_order_service(repo: Annotated[OrderRepository, Depends(get_repo)]) -> OrderService:
       return OrderService(repo)
   ```

5. **Step 3: the route calls the service**, and raises nothing itself.
6. **Checks after each step**, the same every time:

   ```
   4 passed in 0.10s
   All checks passed!
   Success: no issues found in 9 source files
   import_all: 7 ok, 0 failed, 0 skipped
   probe diff exit: 0
   openapi diff exit: 0
   ```

   Commits: `6c3a0ad Add domain errors and their handlers, not raised
   yet`, `6c659d0 Add OrderService and its provider, not used yet`,
   `2cf1832 Place orders through OrderService`, each with the body
   "Structure only; responses unchanged (probe and OpenAPI compared)."
   At the end `git diff HEAD~3 -- tests` printed nothing, and
   `app/service.py` has no `fastapi` or `HTTPException`.

In an earlier run the provider was written as
`OrderService(OrderRepository())`: the override no longer reached the
repository and 3 of 4 tests failed against the real data. Overriding
the new provider in `conftest.py` would have turned them green and left
the real wiring untested; the step was undone instead
(`core/step-loop.md`).

## The answer

```
## Steps
1. add the errors and handlers, unused: 6c3a0ad. pytest 4 passed; ruff All
   checks passed!; mypy Success (8 files); import_all 6 ok, 0 failed; probe
   and OpenAPI identical.
2. add OrderService and get_order_service, unused: 6c659d0. The same checks,
   9 files, 7 ok.
3. route through the service: 2cf1832. The same checks.

## References
tests/conftest.py:32 overrides get_repo: kept working, since
get_order_service takes Depends(get_repo). The two HTTPException raises in
app/routes.py became UnknownCustomerError and CreditLimitExceededError.

## Behaviour
Tests 4 passed at every step, unchanged. Probe (status, headers, body for
six requests) and OpenAPI identical after each step. For a non-HTTP caller,
OrderService.place raises UnknownCustomerError or CreditLimitExceededError
(AppError) where the route raised HTTPException.

## Findings
If seniority's change check runs, it reports place_order's parameter 'repo'
as renamed to 'service'; FastAPI fills it and no caller passes it
(reference/change-check.md).
```
