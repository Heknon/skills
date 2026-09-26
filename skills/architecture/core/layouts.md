# Layouts

**Verdict you produce:** the name of the layout a codebase uses, with
the signs you saw, and how it grows.

| Layout | Signs in the tree | Where a new feature goes | Fits |
| --- | --- | --- | --- |
| **flat** | `main.py` with routes, maybe `models.py`, `db.py`; no layer modules | into `main.py` until it has about ten routes; then split by feature | scripts, small internal APIs |
| **crud per feature** | `<feature>/router.py`, `<feature>/crud.py`, `<feature>/schemas.py`; routes call crud functions directly | a new `<feature>/` with the same three files | small to medium services with little logic |
| **by feature** (default for new code) | `<feature>/router.py`, `service.py`, `repository.py`, `schemas.py`, often `errors.py`, `dependencies.py`; shared `db.py`, `errors.py` | a new feature folder with the same files | most services |
| **by layer** | `routers/`, `services/`, `repositories/` (or `crud/`), `schemas/`, `models/`, each with one module per feature | one new module in each layer folder | services with many small features sharing a lot |
| **hexagonal / clean** | `domain/`, `application/` or `use_cases/`, `ports/`, `adapters/` or `infrastructure/`; Protocols or ABCs for repositories | a port if a new outside system appears; otherwise a use case and an adapter | a port with two or more real adapters (two databases, a queue and HTTP) |

How to tell by-layer from by-feature when both folder kinds exist: the
trace of `core/recognise.md`. If one request passes through
`routers/orders.py`, `services/orders.py`, `repositories/orders.py`, it
is by layer, whatever else the tree holds.

A `services/` folder whose functions only call one repository function
each is still a service layer if the codebase's rule is that routes go
through it (a README or a consistent pattern says so). Follow it: a
forwarding service is a card exception, not L2 or a finding.

## Growing each one

- **crud per feature**: a rule used by two routes, or by a worker, earns
  a function in a module of the feature (`<feature>/rules.py` or
  `service.py`) only when the codebase has one somewhere; otherwise a
  function in `crud.py` that is not a query is a smell to mention, not
  to fix.
- **by feature**: shared code goes to the package's shared modules
  (`app/errors.py`, `app/db.py`), never into another feature.
  A feature importing another feature's repository is a sign they should
  talk through a service.
- **by layer**: keep one module per feature in each layer; do not start
  feature folders for the new code.
- **hexagonal**: a new adapter only for a new outside system. Do not add
  a port for code that has one implementation and no test that needs a
  second.

`core/design.md` decides the layout of a new service; this file is for
reading an existing one.
