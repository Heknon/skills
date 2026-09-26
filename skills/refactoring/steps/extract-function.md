# Extract function

Move a block of statements into a new function, and call it from where
the block was.

## Preconditions

- The block is pinned: a test or probe input goes through it, including
  its boundaries.
- You can name what the block reads (its inputs) and what it changes
  that the rest of the function uses afterwards (its outputs).

## Mechanics

1. List the block's inputs: every local variable it reads that was set
   before it. They become parameters.
2. List its outputs: every local it assigns that is read after the
   block. One output is returned; several are returned as a tuple, or
   the block is too big: extract less.
3. Write the new function above the old one, private (`_name`) unless
   asked otherwise, with the statements copied exactly, operators and
   constants included. Copy, do not retype.
4. Replace the block with the call, assigning the outputs.
5. Checks, probe, commit: "Extract apply_discounts from order_total".

In the lab, the discount lines of `order_total` became

```python
def apply_discounts(subtotal: Decimal, items: int, customer: dict[str, object]) -> Decimal:
    """Bulk discount first, then the loyalty credit; never below zero."""
    if items > BULK_THRESHOLD:
        subtotal -= subtotal * BULK_RATE
    if customer.get("loyal"):
        subtotal -= LOYALTY_CREDIT
    if subtotal < 0:
        subtotal = Decimal("0")
    return subtotal
```

and the call `subtotal = apply_discounts(subtotal, items, customer)`:
5 passed, the probe identical, the off-by-one in `items > BULK_THRESHOLD`
kept and reported (`core/refactor-or-fix.md`).

## Traps

| In the block | What goes wrong | Do |
| --- | --- | --- |
| a local reassigned and used later | the caller keeps the old value | return it and assign it |
| `return` | returns from the new function, not the old one | extract less, or return a flag the caller checks |
| `yield` | lab: the loop called `_emit(r)` and dropped the generator: `['end']` instead of `[2, 6, 'end']`; with no other `yield` left the old function returned `None` (`TypeError: 'NoneType' object is not iterable`) | call it as `yield from _emit(r)` |
| `break` or `continue` | `SyntaxError: 'break' outside loop`, `SyntaxError: 'continue' not properly in loop` (ruff `F702`) | leave the loop control in the caller |
| a mutable argument changed in place | same object, same effect; fine, but name it | keep it, or return a copy only if asked |
| an exception caught around the block | the handler no longer covers code that moved | move the `try` with it, or leave it in the caller around the call |

## Probe inputs

The block's boundaries (for a threshold, the values just below, at and
above), and an input that skips the block entirely.

**Done when:** the new function holds the exact statements, the old one
calls it, and the checks and probe are unchanged.
