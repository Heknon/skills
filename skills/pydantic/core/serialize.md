# Change what a dump looks like

**Verdict you produce:** the dumped output before and after.

```
before: <model_dump or model_dump_json output>
after:  <output>
how:    <the argument, config key or serializer that changed it>
```

## Dump modes

| Call | Gives | *lab* for `placed_at=datetime(2026,1,2,tzinfo=utc)` |
| --- | --- | --- |
| `model_dump()` | Python objects | `datetime.datetime(2026, 1, 2, 0, 0, tzinfo=...)` |
| `model_dump(mode="json")` | JSON-safe values | `'2026-01-02T00:00:00Z'` |
| `model_dump_json()` | a JSON string | `"placedAt":"2026-01-02T00:00:00Z"` (with `by_alias=True`) |

`Decimal` dumps as a string in JSON mode; `SecretStr` as
`'**********'` in both (*lab*).

## Aliases in the output

Aliases are used to **read** input by default, and to **write** output
only when asked:

| Want camelCase output | Works on |
| --- | --- |
| `model_dump(by_alias=True)`, `model_dump_json(by_alias=True)` at each call | all 2.x |
| `model_config = ConfigDict(serialize_by_alias=True)` once | 2.11 and later; *lab:* on 2.10.6 the key is **ignored silently** and the dump stays snake_case |

*lab (2.13.5)*, with `alias_generator=to_camel`:

```
model_dump()             {'order_id': 1, 'total_cents': 5, ...}
model_dump(by_alias=True) {'orderId': 1, 'totalCents': 5, ...}
```

Do not rename fields to camelCase to fix output: that breaks Python
callers and the aliases' purpose.

Constructing by field name when aliases exist needs
`validate_by_name=True` (2.11+) or `populate_by_name=True` (older, still
works in 2.13.5, to be deprecated in v3 per its docstring). *lab:*
without either, `Order(order_id=1)` failed with `missing` at
`('orderId',)`: error locations use the alias.

| Different names in and out | Write |
| --- | --- |
| one name both ways | `Field(alias="userName")` |
| several input names | `Field(validation_alias=AliasChoices("userName", "login"))` |
| input nested in another object | `Field(validation_alias=AliasPath("address", "city"))` |
| output name only | `Field(serialization_alias="userName")` |

## Leaving things out

| Argument | Leaves out | *lab* for `Opt.model_validate({"c": 0})`, defaults `a=None, b="d", c=0` |
| --- | --- | --- |
| `exclude_unset=True` | fields not in the input | `{'c': 0}` |
| `exclude_defaults=True` | fields equal to their default | `{}` |
| `exclude_none=True` | fields whose value is `None` | drops `a` |
| `include={...}`, `exclude={...}` | named fields; `exclude` wins | |
| `Field(exclude=True)` | the field, always | |
| `Field(exclude_if=callable)` | the field when the callable says so (2.12+) | |
| `exclude_computed_fields=True` | computed fields (2.12+) | |

`exclude_unset` works on nested models too: *lab:* `{'inner': {'a':
5}}` kept only the nested field that was sent. That is the basis of
PATCH (`partial/unset-and-none.md`).

## Changing a value on the way out

```python
from pydantic import computed_field, field_serializer

class Money(BaseModel):
    amount: Decimal
    currency: str = "EUR"

    @field_serializer("amount")
    def two_places(self, v: Decimal) -> str:
        return f"{v:.2f}"

    @computed_field
    @property
    def label(self) -> str:
        return f"{self.amount} {self.currency}"
```

*lab:* `{'amount': '3.50', 'currency': 'EUR', 'label': '3.5 EUR'}`. A
computed field is in the dump and in the schema, never read from input.
Beware: dumping a model with a computed field and validating the dump
again under `extra="forbid"` fails with `extra_forbidden` on the computed
field (*lab*); use `exclude_computed_fields=True` for such round trips.

`@model_serializer` replaces the whole output (*lab:* `{'value': 3}`).

## Secrets

`SecretStr` hides the value in `repr`, `str` and every dump; only
`.get_secret_value()` returns it (*lab*). Never print or paste what
`get_secret_value()` returns; check its length instead.
