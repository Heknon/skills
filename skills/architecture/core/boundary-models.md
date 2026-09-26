# Models at each boundary

**Verdict you produce:** which class is used at each boundary, where the
mapping between them lives, and a test that a hidden field stays hidden.

```
request:   <schema class> (fields a client may set)
response:  <schema class> (fields a client may see)
domain:    <class the service works with, or "the database model (card)">
database:  <Document or mapped class>
mapping:   row -> domain in <repository path>; domain -> response in <path>
test:      <test that asserts the response keys, and one that a forbidden input is refused>
```

What a pydantic model does (`from_attributes`, `model_dump`,
`extra="forbid"`) is the pydantic skill's; which model sits where is
this file's.

## Why the database model stays behind the repository

*lab,* FastAPI 0.141.1, Beanie 2.2.0, a `User` document with
`password_hash` and `is_admin`, sandbox users-beanie:

| Route | Result |
| --- | --- |
| returns the `User` document, no response model | 200 with `_id`, `password_hash`, `is_admin`, `failed_logins`; the OpenAPI schema property is `_id` |
| the same, for a missing id | **200 `null`** |
| `-> UserOut` or `response_model=UserOut` returning the document | filtered: `{"id", "email"}` |
| `body: User` on a POST | a client set `is_admin: true` **and `_id`** |
| PATCH with `body: dict` and `user.set(body)` | a client became admin; `is_admin` stored `true` |

A response model filters, but relies on every route remembering it, and
the database model still leaves its layer. On SQLAlchemy async the
filtered row is read after the session's work: *lab,* SQLAlchemy 2.1.1,
sandbox lazy-after-commit: `ResponseValidationError` with
`get_attribute_error` and `(sqlalchemy.exc.MissingGreenlet)
greenlet_spawn has not been called` (`sqlalchemy/loading.md`).

Beanie 2.2.0 also refuses to build a document before `init_beanie`:
*lab:* `User(...)` raised `beanie.exceptions.CollectionWasNotInitialized`.
So a fake repository that returns documents needs a server; one that
returns domain models does not. That is the practical reason for domain
models in tests.

## The default (decision AR3)

- **Schemas** in the feature's `schemas.py`: `XIn` lists only fields a
  client may set, with `extra="forbid"`; `XOut` only fields a client may
  see.
- **Domain models** in `domain.py`: pydantic models, `frozen=True`,
  holding what the service needs, including internal fields
  (`kyc_reference`) that `XOut` leaves out.
- **Database models** in `models.py`, used only by the repository.
- **Mapping**: `_to_domain(row)` in the repository, while the session is
  open; `XOut.from_domain(domain)` on the schema. The router calls
  `from_domain`; nothing below the router imports a schema.

The recipes do exactly this (`recipes/*/app/accounts/`), and their
`test_open_account_hides_internal_fields` asserts the whole response
body, so a new field fails the test until someone decides it is public.

## Where the codebase uses the database model as the domain model

Accept it (decision AR3): many Beanie codebases pass `Document`s to the
service. Keep the hard rule only: no database model in a route signature
or response. Map at the route: `UserOut.model_validate(user.model_dump())`
as the sandbox's `POST /users` does. Do not introduce a domain layer for
one route.

## Request models for updates

A PATCH body is its own schema listing only what the client may change,
with `extra="forbid"` (*lab,* users-beanie: `is_admin` in the body gave
422 `extra_forbidden` and the stored value stayed `false`). What omitted
and `null` mean, `exclude_unset=True`, and the dict body with
`apply_patch` for validation across fields are the api skill's
(`skills/api/core/put-and-patch.md`) and pydantic's.

## Tests to write

```python
def test_response_has_only_public_fields(client):
    r = client.get(f"/users/{user_id}")
    assert set(r.json()) == {"id", "email", "display_name", "bio"}

def test_client_cannot_set_is_admin(client):
    r = client.patch("/users/me", headers=auth, json={"is_admin": True})
    assert r.status_code == 422
```

Assert the set of keys, not the absence of one key: a new secret field
must fail the test too.
