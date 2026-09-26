# Forward references and `model_rebuild`

A model's annotations are resolved when the class is built. A name that
does not exist yet at that moment leaves the model incomplete, and the
first use fails:

```
pydantic.errors.PydanticUserError: `Order` is not fully defined; you
should define `Customer`, then call `Order.model_rebuild()`.
```

(*lab*, 2.13.5; its code is `class-not-fully-defined`.)

## When pydantic fixes it alone

*lab:*

- A model referring to itself, `children: list["Node"] = []`, works.
- In one module, `A` using `"B"` before `B` is defined fails if used
  before `B` exists, and works on first use once `B` is defined: the
  rebuild is automatic when the name can be found in the module.

## When you must rebuild: models in two modules

Two models that refer to each other across files import each other only
for type checkers, to avoid a circular import:

```python
# shop/orders.py
from __future__ import annotations
from typing import TYPE_CHECKING
from pydantic import BaseModel
if TYPE_CHECKING:
    from shop.customers import Customer

class Order(BaseModel):
    id: int
    customer: Customer | None = None
```

At run time `Customer` never exists in `shop.orders`, so no automatic
rebuild can find it. Rebuild both once both classes exist, where both
names are in scope, such as the package's `__init__.py`:

```python
# shop/__init__.py
from shop.customers import Customer
from shop.orders import Order

Order.model_rebuild()
Customer.model_rebuild()
```

*lab:* importing `shop.orders` runs `shop/__init__.py` first, and
`Order.__pydantic_complete__` was then `True`; the tests passed.
`model_rebuild()` looks the names up in the namespace of the code that
calls it (its `_parent_namespace_depth=2` parameter).

## Errors on the way

| *lab* message | Meaning |
| --- | --- |
| `PydanticUndefinedAnnotation: name 'Customer' is not defined` | `model_rebuild()` was called where `Customer` is not in scope |
| rebuild returns `True` | the model is complete now |

Where no module sees both names, pass them:
`Order.model_rebuild(_types_namespace={"Customer": Customer})` (*lab:*
worked). The leading underscore marks it private to pydantic; prefer
calling from a module that imports both.

## Never

- Never replace the annotation with `Any` or remove it: the model stops
  validating that field.
- Never import at module level into a circle to make the name exist; the
  import error only moves.
