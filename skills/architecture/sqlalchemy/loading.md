# Loading, and MissingGreenlet

**Verdict you produce:** why an attribute access failed, and the fix in
the data layer.

## The error (*lab,* SQLAlchemy 2.1.1, aiosqlite)

Any access that needs IO outside SQLAlchemy's async context raises:

```
sqlalchemy.exc.StatementError: (sqlalchemy.exc.MissingGreenlet) greenlet_spawn has not
been called; can't call await_() here. Was IO attempted in an unexpected place?
```

The class raised is `StatementError` wrapping `MissingGreenlet`, so
`except MissingGreenlet` does not catch it (and catching is not the fix).

| Access | When it raised |
| --- | --- |
| a column attribute after `commit()` with the default `expire_on_commit=True` | the object was expired; reading it needs a SELECT |
| a relationship not loaded (`order.customer`, `customer.orders`) with the default lazy loading | the lazy load is IO |
| a relationship declared `lazy="raise"` | `InvalidRequestError: 'Order.notes' is not available due to lazy='raise'` (a clearer error, on purpose) |

In a route, *eval* lazy-after-commit: the repository committed and
returned the row; building `OrderOut` read it. With `model_validate`
in the route: `pydantic_core.ValidationError: 3 validation errors for
OrderOut ... Error extracting attribute: StatementError:
(sqlalchemy.exc.MissingGreenlet) ...` with type `get_attribute_error`.
Returning the row and letting the response model read it:
`fastapi.exceptions.ResponseValidationError: 3 validation errors`, the
same type. The client saw `500 Internal Server Error`.

## Fixes that passed in the lab

1. **The repository returns a model built while the session is open**:
   flush, map the row (and the relationships it just set) to a pydantic
   model, then let the unit of work commit. The route never touches a
   row (L3). This is the recipes' way.
2. `expire_on_commit=False` on the sessionmaker: the create case passed.
   It does not help a relationship that was never loaded.
3. For relationships: `select(Order).options(selectinload(Order.lines))`,
   `await session.refresh(order, ["lines"])`, or with the `AsyncAttrs`
   mixin `await order.awaitable_attrs.lines` (all three loaded the
   lines in the lab).

Not fixes: a sync route (it cannot use the async session), `except`
around the access, `lazy="joined"` on every relationship without a test
of the query count.
