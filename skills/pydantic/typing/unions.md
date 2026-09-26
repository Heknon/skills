# Unions and discriminators

## Smart mode, the default

For `Union[A, B]` (or `A | B`) pydantic tries every member and keeps
the best match: an exact type beats a converted one, and among models
the one with more fields set wins. On a tie the **first** member wins.

*lab (2.13.5):*

| Field | Input | Result |
| --- | --- | --- |
| `Union[int, str]` | `"1"` | `'1'` (exact `str`) |
| `Union[str, int]` | `1` | `1` (exact `int`) |
| `Union[int, str] = Field(union_mode="left_to_right")` | `"1"` | `1` (first that converts) |
| `Union[Dog, Cat]`, both with `type: str` and defaults | `{"type": "cat", "name": "Tom"}` | **`Dog`** (tie, first wins) |
| same | `{"type": "cat", "name": "Tom", "indoor": False}` | `Cat` (more fields set) |
| same | `{"type": "cow", "name": "Daisy"}` | `Dog`: nothing rejects it |

Making fields `Optional` or reordering the union moves the problem: with
`Union[Cat, Dog]`, *lab:* dogs became cats.

## Discriminated unions: the fix when members share a shape

Give each member a `Literal` tag and name it:

```python
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field

class Dog(BaseModel):
    type: Literal["dog"]
    name: str
    breed: str = "unknown"

class Cat(BaseModel):
    type: Literal["cat"]
    name: str
    indoor: bool = True

Pet = Annotated[Union[Dog, Cat], Field(discriminator="type")]

class Owner(BaseModel):
    pets: list[Pet]
```

*lab:*

| Input | Result |
| --- | --- |
| `{"type": "cat", "name": "Tom"}` | `Cat` |
| `{"type": "cow", "name": "Tom"}` | `union_tag_invalid`: `Input tag 'cow' found using 'type' does not match any of the expected tags: 'dog', 'cat'` |
| `{"name": "Tom"}` | `union_tag_not_found` |
| `{"type": "cat"}` | `missing` at `('pet', 'cat', 'name')`: only the chosen member is reported |

Without the discriminator, a bad payload reports every member: *lab:*
two `literal_error`s at `('pet', 'Dog2', 'type')` and `('pet', 'Cat2',
'type')`.

The tag field must be a `Literal` in every member; `Field(discriminator=)`
on a field typed `Union[...]`, or `Annotated[Union[...],
Field(discriminator=...)]` as a reusable type (it works in
`TypeAdapter(list[Pet])` too, *lab*).

## When there is no tag field

A callable picks the member; each member is labelled with `Tag`:

```python
from pydantic import Discriminator, Tag

def pick(v):
    if isinstance(v, dict):
        return "cat" if "indoor" in v else "dog"
    return "cat" if hasattr(v, "indoor") else "dog"

class Owner(BaseModel):
    pet: Annotated[
        Union[Annotated[Dog, Tag("dog")], Annotated[Cat, Tag("cat")]],
        Discriminator(pick),
    ]
```

*lab:* `{"type": "x", "name": "a", "indoor": False}` became `Cat`. The
function must handle both dicts (input) and model instances (dumping).
