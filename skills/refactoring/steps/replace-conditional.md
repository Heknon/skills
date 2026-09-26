# Replace a conditional

Replace an `if`/`elif` chain with a flatter form: early returns, a
lookup table, `match`, or a method on each type. Each form decides
equality, order and failure in its own way, so the replacement is a
behaviour change unless those agree for every input the code can get.

## Preconditions

- The chain is pinned with inputs for every branch, the fall-through,
  and the odd inputs below.

## Mechanics

1. Early returns first (the safest form): turn `else: if ...` into
   `if ...: return`, keeping the order of the conditions.
2. A lookup table only when every condition is `x == <constant>` on the
   same `x`, the constants are distinct, and `x` is always hashable.
3. Checks and the probe after each change; commit.

## Traps seen in the lab

A tidy of `pricing.py` replaced

```python
if code == "SPRING10":
    return total - total * 0.1
elif code == "VIP":
    return total - total * 0.2
elif code == None:
    return total
else:
    return total
```

with `rate = DISCOUNT_RATES.get(code)`. The probe (codes `"SPRING10"`,
`"VIP"`, `None`, `""`, `"spring10"`) was identical, yet the behaviour was
not:

| Input | The chain | The table |
| --- | --- | --- |
| `discount(100, [])` | `100` | `TypeError: unhashable type: 'list'` |

A `match` statement with the same string cases returned the default for
`[]`, as the chain did. Also:

| Change | Differs when |
| --- | --- |
| `==` to `is` (ruff `E711` for `== None`) | a type defines `__eq__`: lab, a class whose `__eq__` returns `True` gave `X() == None` `True` and `X() is None` `False`; for ordinary values the result is the same |
| conditions reordered | two conditions can both be true: the first one used to win |
| a table of functions built at import | the table holds the functions themselves: with `mock.patch("disc.spring", return_value=0)` the chain returned `0` and the table `90.0` (lab) |

The same tidy turned `for i in range(len(basket)): t = t + basket[i][1]`
into `for _name, price in basket:`; a basket item of three values then
raised `ValueError: too many values to unpack (expected 2)` where the
old loop returned the total.

## Probe inputs

Every branch, the fall-through, `None`, an empty value, a value of
another type (a list for a string key), and values that match two
conditions.

**Done when:** the new form gives the same result or the same exception
for every probe input, including the odd ones, or the difference is
listed as a finding and the old form kept.
