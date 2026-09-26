# Layering violations, L1 to L11

Checklist version 1 (architecture skill, first build). IDs are stable:
code-review cites them, refactoring names its recipes after them. A
later version may add IDs; it never renumbers or reuses one.

Run `core/recognise.md` first. What the structure card allows is not a
finding (the last column). Severity follows code-review's scale, which
code-review owns: the suggestion is the level with no failure scenario,
and the scenario that raises it.

| ID | Violation | Rule broken | Suggested severity | Raise to | Card exception | Shape |
| --- | --- | --- | --- | --- | --- | --- |
| **L1** | the route queries the database | a route calls one function below and maps the result | minor | major when a second caller needs the same query and copies it | a codebase with no data layer anywhere (flat): note once, not per route | `shapes/L1-query-in-route.md` |
| **L2** | business logic in a router | rules live in the service or domain model | minor | major when a worker or CLI runs the same use case without the rule | a crud-per-feature codebase that keeps simple checks in routes | `shapes/L2-logic-in-router.md` |
| **L3** | a database model in a response or request body | no row or `Document` crosses the HTTP boundary | minor (filtered by a response model) | **blocker** when a hidden field reaches the client or a client can set a protected field (`is_admin`, `_id`); major for `200 null` or a 500 on a missing row | none: this one is never allowed | `shapes/L3-db-model-at-boundary.md` |
| **L4** | the service knows HTTP | no `fastapi`/`starlette` import, no `HTTPException`, no `Request` in services | minor | major when a non-HTTP caller exists (worker, CLI, job) | none | `shapes/L4-service-knows-http.md` |
| **L5** | a transaction split across layers | one owner, the service through a unit of work; repositories flush | major | **blocker** when two writes that must happen together can half apply (money, stock) | a yield dependency with `scope="function"` that is the only committer (`core/transactions.md`) | `shapes/L5-split-transaction.md` |
| **L6** | the repository returns raw data | domain models out, never dicts, cursors, rows, `Select` | minor | major when callers index by stored key names (`r["_id"]`) | a codebase that uses the `Document` itself as its domain model (decision AR3) | `shapes/L6-raw-data-from-repository.md` |
| **L7** | imports point up, or round | edge inwards only; no cycles; no function-level import to hide one | minor | major when the app fails to start or only starts because of a local import | services that accept schemas, where the codebase does so throughout | `shapes/L7-imports-point-up.md` |
| **L8** | a database error untranslated, or translated twice | driver to domain once in the repository, `from exc`; domain to HTTP in one handler | major (a duplicate is a 500) | blocker when a broad `except` turns other failures into a success or a 404 | none | `shapes/L8-untranslated-db-error.md` |
| **L9** | a dependency that cannot be swapped | providers in `Depends`, overrides keyed by the provider | minor | major when tests patch globals or hit a real service because the override has no effect | module-level engine or client objects read through a provider (they are process-wide by design) | `shapes/L9-unswappable-dependency.md` |
| **L10** | a thing placed against precedent | a new thing goes where its kind lives | nit | minor when it creates a second home for a kind, or an import from a higher layer | a new convention the person asked for | `shapes/L10-placed-against-precedent.md` |
| **L11** | an exception that cannot be handled well | a class callers catch by type; fields to `super().__init__`; no `HTTPException` base in the domain | minor | major when it crosses a process boundary (unpicklable) or a caller parses `str(e)` to decide | `except Exception` at the outermost edge (the unhandled-error handler, a job runner) | `shapes/L11-unhandleable-exception.md` |

## A finding

```
[L5] app/repository.py:23  await self.session.commit() in AccountRepository.debit
  rule:      one transaction owner; repositories flush (core/transactions.md)
  scenario:  transfer to a frozen account: debit committed, credit fails, money gone
  severity:  blocker (suggested; code-review decides)
  shape:     shapes/L5-split-transaction.md
```

One finding per line the change adds or touches. A violation already
present before the change goes under "seen, not part of this change",
not into the findings (`checklist/finding.md`).
