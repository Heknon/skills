# Lay out a new service

**Verdict you produce:** the smallest layout that fits the requirements,
the reason, and what would change it.

```
layout:        <flat | by feature>, files: <tree>
why:           <the requirements that need each file>
not added:     <layers and abstractions left out, and why>
would change:  <what future need would justify each one>
first test:    <the test and its run>
```

## The default (decision AR2)

By feature: one folder per feature with `router.py`, `schemas.py`,
`service.py`, `repository.py`, `models.py` (the table or document) and
`domain.py`, plus `errors.py` and `dependencies.py` when there is
something to put in them; shared `db.py` and `errors.py` at the package
root; `main.py` with an app factory. The two recipes are
this layout (`recipes/`).

Go smaller when the requirements allow:

| Requirement | Layout |
| --- | --- |
| a few routes, no rules beyond validation, one storage | flat: `main.py`, `db.py`, `schemas.py`; one module per feature later |
| any rule a second caller (worker, CLI, job) will need, or a transaction across writes | the default: the rule and the transaction go in `service.py` |
| queries worth testing alone, or two storage calls per use case | a repository |

A rule such as "no two bookings of a room may overlap" is enough for a
service; a reporting job that will read the same data is enough for a
repository that returns domain models.

## Left out unless the requirements name them

- **A generic `BaseRepository[T]`**: every repository ends up
  overriding it, and it hides which queries exist. Write the methods
  each feature needs.
- **Ports and adapters** (`ports/`, `adapters/`, ABCs for every
  repository): only when one port has two real adapters. A `Protocol`
  beside the service is enough for a fake in tests
  (`recipes/sqlalchemy_service/app/accounts/service.py`).
- **An abstract service base**, a mediator, a command bus, events.
- **A domain model separate from the schema** is not in this list: new
  code keeps them apart (decision AR3, `core/boundary-models.md`).

## Start the conventions

A new service has no precedent, so say which conventions you start:
errors in `app/errors.py` (base and categories) and `<feature>/errors.py`
(`placement/custom-errors.md`); providers in `<feature>/dependencies.py`;
settings in one pydantic-settings class (the pydantic skill). Write them
down once, in the answer; the next change follows them.

## Steps

1. List the endpoints and every rule in the requirements.
2. Choose the layout from the table; name each file with the
   requirement that needs it.
3. Copy the nearer recipe (`recipes/sqlalchemy_service` or
   `recipes/beanie_service`) and delete what is not needed; rename the
   feature.
4. Write the first service test with a fake repository (no database),
   run it, and quote the line.
