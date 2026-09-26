# Extract variable

Give a sub-expression a name by assigning it to a local variable.

## Preconditions

- The expression has no side effect, or it runs exactly as often and at
  the same moment after the change.
- The new name is not already used in the function.

## Mechanics

1. Assign the expression to a local on the line just before the
   statement that uses it, so it is evaluated at the same point.
2. Replace the expression with the name. Only that occurrence, unless
   the others are the same expression evaluated at the same moment.
3. Checks, commit: "Name the bulk discount rate in order_total".

## Traps

Moving an expression out of a condition changes when it runs:

```python
if ok and expensive(x) > 1:      # before: expensive() runs only when ok
    ...

ratio = expensive(x)             # after: it runs every time
if ok and ratio > 1:
    ...
```

In the lab, `before(False, 0)` returned `"no"` without calling
`expensive`; `after(False, 0)` raised `ZeroDivisionError: division by
zero`. The same holds for the right side of `or`, a conditional
expression's branches, a comprehension's condition, and code after a
`None` check that the expression relies on.

| Also watch | Why |
| --- | --- |
| the expression reads something the statement before changes | hoisting it above that statement reads the old value |
| two occurrences replaced by one variable | an expression with a side effect or a changing value (time, random, an iterator) now runs once |

## Probe inputs

The inputs that make the guarding condition false, and those that would
make the expression raise.

**Done when:** the expression runs under the same conditions as before,
and the checks and probe are unchanged.
