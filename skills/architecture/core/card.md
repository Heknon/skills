# The structure card

**Verdict you produce:** the card below, filled in, at the top of your
answer's `## Structure` section and before any change.

## The shape

```
layout:       <by layer | by feature | crud per feature | hexagonal | flat>, from <which folders>
entry points: <app object path:line; workers and CLIs that call the same code>
trace:        <route path:line> -> <next hop path:line> -> ... -> <ORM/ODM call path:line>
layers:       <which exist: router, service, repository/crud/DAL; which do not>
models:       database <where> | domain <where or "database model used as domain"> | schemas <where>
mapping:      <where rows become domain models, and domain models become responses>
wiring:       <providers and the file that holds them; how tests swap them>
transactions: <who commits: service/unit of work, repository per method, a yield dependency, none>
errors:       <base and categories path; feature errors path; handlers path; how driver errors are translated>
precedent:    <for each kind the task adds: its home path:line, or "none">
uneven:       <features built differently, and which one this change follows>
```

Each line is a fact you read, with a path. Write `inferred:` in front of
a line you did not confirm by reading.

## A filled card

The `credit-limit` sandbox (by layer, a worker beside the API), read
file by file:

```
layout:       by layer: app/routers/, app/services/, app/repositories/
entry points: app/main.py:19 app = FastAPI(lifespan=...); app/worker.py:18
              import_orders(service, rows): the nightly import, no FastAPI
trace:        app/routers/orders.py:24 place_order -> app/dependencies.py:13
              get_order_service -> app/services/orders.py:11 OrderService.place
              -> app/repositories/orders.py:28 add_order (in memory)
layers:       router, service, repository; all three exist
models:       database none yet (dataclasses Customer, Order in
              app/repositories/orders.py:5,12 act as rows and domain) |
              schemas OrderIn, OrderOut in app/routers/orders.py:12,17
mapping:      in the route: OrderOut(id=order.id, ...) (app/routers/orders.py:26)
wiring:       app/dependencies.py:9,13; the repository comes from app.state
transactions: none (in-memory store)
errors:       app/errors.py:4 AppError, :8 NotFoundError, :12
              CustomerNotFoundError; one handler per category in
              app/main.py:23; the worker catches AppError (app/worker.py)
precedent:    exception -> app/errors.py (one central file, categories and
              specific classes together)
uneven:       none
```

What the card decides for the task "reject orders over the credit limit
with 409": the rule goes in `OrderService.place` (the worker needs it
too), the error in `app/errors.py` under a new `ConflictError` category,
one 409 handler beside the 404 one in `app/main.py`, and no
`HTTPException` in the service, because the worker catches `AppError`.
The eval `credit-limit` checks exactly this.

## What the card allows

The card is also what code-review checks against: a forwarding service
in a codebase whose rule is "every route calls a service", routes that
query in a codebase with no data layer at all, a `Document` used as the
domain model. Each is a card exception, not a finding
(`checklist/violations.md`). Say so once in the card, not per line.
