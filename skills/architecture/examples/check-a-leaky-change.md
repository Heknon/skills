# Worked example: checking the layering of a change

Kinds: Recognise, Check. The outputs are from a lab run on the
review-diff sandbox's change (Beanie 2.2.0, ruff 0.16.9); line numbers
are the working tree's.

## The ask

> Review the layering of the change in change.diff (already applied to
> the working tree). Do not change code.

## Steps

1. **Card first** (`core/recognise.md`). `README.md`: "routes call a
   service, services call a repository, even when the service only
   forwards. Only repositories import Beanie documents' query API."
   Layout by feature (`app/invoices/{router,service,repository,
   models,schemas,dependencies}.py`); trace
   `router.py:29 get_invoice -> service.py:12 get -> repository.py:10
   Invoice.find_one`. Errors: `HTTPException` in the router, no custom
   errors.
2. **Read the diff**: two new routes (`/overdue`, `/open-totals`), a
   repository method `totals_by_customer`, a `try` in `create`, a
   forwarding service method.
3. **Searches** (`checklist/finding.md`) on the touched files; hits:

   ```
   L1  app/invoices/router.py:18   rows = await Invoice.find(Invoice.paid == False, ...).to_list()
   L6  app/invoices/repository.py:18   async def totals_by_customer(self) -> list[dict]:
   L8  app/invoices/repository.py:1    from fastapi import HTTPException
   L8  app/invoices/repository.py:16   raise HTTPException(409, f"invoice {data.number} already exists")
   ```

   The project runs ruff, so `B904` too:
   `app/invoices/repository.py:16:13: B904 Within an except clause,
   raise exceptions with raise ... from err ...`.
4. **Open each hit.** All four are real. `router.py:25` indexes
   `r["_id"]`: the consumer of the L6 rows.
5. **Card exceptions.** `service.py:18` `totals_by_customer` only
   forwards to the repository. The README's rule asks for exactly that:
   allowed, not L2 and not a finding.
6. **Scenarios** for severity: L8, a worker creating invoices gets an
   `HTTPException`; L6, renaming `customer_id` in the `$group` breaks the
   route at run time with a `KeyError`; L1, the next job that needs
   overdue invoices copies the query.

## The answer

```
## Structure
by feature, app/invoices/; team rule (README.md): every route goes through
a service, forwarding allowed; only repositories use Beanie's query API.

## Result
Findings, suggested severities (code-review decides):
[L8] app/invoices/repository.py:16  DuplicateKeyError turned into
     HTTPException(409) inside the repository, without `from` (B904).
     A worker creating invoices gets an HTTP error. Suggested major.
     Target: DuplicateInvoiceError(ConflictError) raised from exc, one 409
     handler (shapes/L8-untranslated-db-error.md).
[L6] app/invoices/repository.py:18  totals_by_customer returns the
     aggregation's dicts; app/invoices/router.py:25 indexes r["_id"].
     Suggested minor, major if the pipeline changes. Target: a
     CustomerTotal model built in the repository (shapes/L6-...).
[L1] app/invoices/router.py:18  overdue_invoices queries Invoice directly,
     against the README's rule. Suggested minor. Target: a repository
     method called through the service (shapes/L1-query-in-route.md).
Allowed by the card: InvoiceService.totals_by_customer (service.py:18)
only forwards, as the team rule requires.
Verdict: changes needed for L8; L6 and L1 in the same change.

## Checked
- The searches of checklist/finding.md on the four touched files; ruff
  check --select B904: 1 error.

## Not checked
- The endpoints were not run against a server in this review.
- Seen, not part of this change: the repository takes InvoiceIn (a
  request schema) in create(), app/invoices/repository.py:12.
```
