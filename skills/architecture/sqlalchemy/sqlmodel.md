# Reading SQLModel code

A reading note, not a recipe (decision AR5).

- **SQLModel 0.0.47 does not install with SQLAlchemy 2.1.** *lab:* uv
  refused: `sqlmodel==0.0.47 depends on sqlalchemy>=2.0.14,<2.1.0`. It
  ran on SQLAlchemy 2.0.54.
- **One class as table and schema is the L3 leak by design.** *lab,*
  FastAPI 0.141.1: `class User(SQLModel, table=True)` with
  `password_hash` and `is_admin`, used as the body and the
  `response_model` of `POST /users`: a client sent `is_admin: true` and
  got back `{"password_hash": "h", "id": 1, "email": "a@x",
  "is_admin": true}`.
- **Table models skip validation.** *lab:* `User(email="a@x")` with the
  required `password_hash` missing was accepted.

In a SQLModel codebase: keep `table=True` classes behind the
repository, and give routes separate non-table classes (plain
`SQLModel` without `table=True`, or pydantic models) for input and
output (*lab:* a non-table `UserCreate(SQLModel)` missing a field raised
`ValidationError`). The layering rules are unchanged.
