# Build a partial model

Facts here are from pydantic-partial 0.11.1 on pydantic 2.13.5 (*lab*),
and hold on 0.9.0 and 0.10.2 where the recipe also ran. Check the
installed release first (`partial/check-installed.md`).

## What `model_as_partial()` makes

```python
from pydantic import BaseModel
from pydantic_partial import PartialModelMixin

class User(PartialModelMixin, BaseModel):
    id: int
    name: str
    email: str | None = None
    status: Literal["active", "suspended"] = "active"

UserPatch = User.model_as_partial()
```

- A **subclass** of `User` named `UserPartial` (`issubclass(UserPatch,
  User)` is `True`), created with `pydantic.create_model`.
- Cached: calling `model_as_partial()` again with the same arguments
  returns the same class.
- Each **required** field becomes `Optional[...]` with default `None`.
- Each field **with a default keeps it** (`status` stays `"active"`), so
  a dump without `exclude_unset=True` sends the defaults back
  (`partial/unset-and-none.md`).
- The model's config, validators and serializers are inherited
  (`partial/validators.md`); so is `extra`: with `extra="forbid"` on
  `User`, a misspelt key in a PATCH body is `extra_forbidden`; with the
  default `ignore`, it is dropped and the PATCH does nothing, silently.

## Choosing fields

| Call | Makes optional |
| --- | --- |
| `User.model_as_partial()` | every required field |
| `User.model_as_partial("email", "name")` | only those; others keep their rules (*lab:* `name` still `missing` when not listed) |
| `User.model_as_partial("addr.city")` | the nested field `addr.city` only |
| `User.model_as_partial("home", "work.*")` | `home`, and every field of the nested `work` |

## Nested models

`recursive=True` makes nested models partial too, but only:

1. nested models that inherit `PartialModelMixin`: *lab:* a plain
   `Address(BaseModel)` stayed full, and `{"address": {"city": "Lyon"}}`
   failed with `missing` at `('address', 'street')`;
2. on fields **without a default**: *lab:* `work: Addr | None = None`
   and `billing: Addr = Addr(...)` stayed full even with the mixin
   (`missing` at `('work', 'street')`), because the code only rebuilds
   required fields. List them as `"work.*"`, `"billing.*"`:

```python
UserPatch = User.model_as_partial(
    *(name for name in User.model_fields if name != "billing"),
    "billing.*",
    recursive=True,
)
```

*lab:* `{"billing": {"postcode": "69001"}}` was then accepted.

Inside lists and unions of a required field it works: *lab:*
`members: list[Addr]` accepted `[{"city": "x"}]`, and `lead: Addr |
None` and `alt: Addr | int` (no defaults) accepted `{"city": ...}`.

## Naming the class

The name shows in JSON schemas (OpenAPI) and in error titles (*lab:*
`e.title` was `UPartial` for a partial of `U`).

| Release | Write |
| --- | --- |
| 0.7.0 and later | `User.model_as_partial(partial_cls_name="UserPatch")` |
| any | `UserPatch = create_model("UserPatch", __base__=User.model_as_partial())` |

*lab* on 0.5.5: the `create_model` form gave the schema title
`UserPatch`, and its fields stayed optional (`required` absent). A
subclass (`class UserPatch(User.model_as_partial()): pass`) works at
run time, but mypy reports `Unsupported dynamic base class`.

## Using it

Parse bodies with `UserPatch.model_validate(body)` (or `_json`).
Checkers type the partial class as `User`, so `UserPatch(name="x")` is
flagged `Argument missing for parameter "id"` (*lab*, pyright);
`model_validate` takes `Any` and is not.

Then merge and validate the result with the full model:
`partial/handoff.md` and `recipes/patch/`.
