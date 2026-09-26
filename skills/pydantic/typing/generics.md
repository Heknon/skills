# Generic models

A model can take a type parameter, for envelopes such as a page of
results:

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
```

Python 3.12 also accepts the new syntax, *lab:* `class Page2[U](BaseModel)`
worked the same way.

*lab (2.13.5):*

| Use | Result |
| --- | --- |
| `Page[int](items=["1"], total=1)` | `Page[int](items=[1], total=1)`: items validated as `int` |
| `Page[int](items=["x"], total=1)` | `int_parsing` at `('items', 0)` |
| `Page(items=["x", 1], total=2)` | accepted as is: an unparametrised generic validates `T` as `Any` |
| `Page[int].__name__` | `'Page[int]'`, which is also the JSON schema title |

Rules:

- Always parametrise where data is validated: `Page[Order]`, not
  `Page`. Unparametrised, nothing inside is checked.
- A generic model can be a field: `results: Page[Order]`.
- For a clean name in a JSON schema, subclass it:
  `class OrderPage(Page[Order]): pass` (*lab:* schema title
  `OrderPage`).

Checkers treat `Page[int]` as a generic class: *lab:* pyright showed
`p.items` as `list[int]` and flagged `Page[int](items=["1"], total=1)`
(lax conversion is invisible to it, `typing/checkers.md`).
