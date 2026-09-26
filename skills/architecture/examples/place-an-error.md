# Worked example: one new error, placed by precedent

Kinds: Place a thing, Errors. Lab run on the errors-precedent sandbox
(FastAPI 0.141.1, Starlette 1.7.0).

## The ask

> GET /invoices/99 and POST /invoices/99/pay answer 500. They should
> answer 404.

## Steps

1. **Reproduce.** `TestClient(app, raise_server_exceptions=False)`:
   both `500 Internal Server Error`; with the default client, GET raised
   `ValidationError: 1 validation error for InvoiceOut ... input_value=None`
   and pay raised `AttributeError: 'NoneType' object has no attribute
   'paid'`. `BillingService.get_invoice` returns `None` for a missing
   invoice and nothing turns it into a 404.
2. **Kind**: an exception (a caller, the HTTP edge, handles it as 404).
   A built-in would not map to 404 through the existing handler, so a
   domain error is right (`placement/custom-errors.md` section 1).
3. **Precedent** (`placement/place-a-thing.md` step 2), the exception
   search:

   ```
   app/core/errors.py:7      class AppError(Exception):
   app/core/errors.py:11     class NotFoundError(AppError):
   app/core/errors.py:15     class ConflictError(AppError):
   app/billing/errors.py:4   class InvoiceAlreadyPaidError(ConflictError):
   app/customers/errors.py:4 class CustomerNotFoundError(NotFoundError):
   ```

   `app/core/errors.py:3` says: "Feature errors live in their feature's
   errors.py and subclass a category." The handler:
   `app/core/handlers.py:15` registers one handler for `AppError`,
   which maps categories through `STATUS = {NotFoundError: 404,
   ConflictError: 409}` (`:6`). The siblings have a class-level `code`,
   positional fields passed to `super().__init__`, and `__str__`.
4. **New file or existing** (`new-or-existing.md`): `app/billing/errors.py`
   exists and holds this feature's errors: join it. No
   `exceptions.py`, no class in `service.py`, no new handler (the
   category's 404 is already mapped).
5. **The class**, shaped like `InvoiceAlreadyPaidError`:

   ```python
   class InvoiceNotFoundError(NotFoundError):
       code = "invoice_not_found"

       def __init__(self, invoice_id: int) -> None:
           super().__init__(invoice_id)
           self.invoice_id = invoice_id

       def __str__(self) -> str:
           return f"invoice {self.invoice_id} not found"
   ```

6. **Raise it in the service**: `get_invoice` raises it instead of
   returning `None`, and `pay` calls `get_invoice`. The router is
   unchanged.
7. **Tests**: one parametrized test for both paths, expecting 404 and
   `{"code": "invoice_not_found", "detail": "invoice 99 not found"}`.
   `uv run pytest -q` -> `4 passed in 0.36s`.

## The answer

```
## Structure
errors: base and categories in app/core/errors.py:7-15; feature errors in
<feature>/errors.py (app/billing/errors.py:4, app/customers/errors.py:4);
one AppError handler maps categories (app/core/handlers.py:6,15).

## Result
- app/billing/errors.py: InvoiceNotFoundError(NotFoundError), code
  "invoice_not_found", field invoice_id. Precedent:
  app/billing/errors.py:4 (InvoiceAlreadyPaidError). Rule: precedent.
- app/billing/service.py: get_invoice raises it; pay uses get_invoice.
- No new handler: NotFoundError is already mapped to 404.
- tests/test_invoices.py: test_missing_invoice_is_404 for GET and pay.

## Checked
- Before: both paths 500 (ValidationError, AttributeError).
- uv run pytest -q: 4 passed in 0.36s.

## Not checked
- Other callers of get_invoice that relied on None: searched
  get_invoice\( and found only the router and pay.
```
