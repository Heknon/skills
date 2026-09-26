# Introduce parameter object

Replace a group of parameters that travel together with one object,
usually a dataclass.

This changes the signature (`change-signature.md`), so it is done as a
parallel change: the old function keeps its parameters and builds the
object; new callers pass the object.

## Preconditions

- The same parameters (for example `start, end, timezone`) are passed
  together through several functions.
- Every caller is found (`core/every-reference.md`).

## Mechanics

1. Add the class, unused. Checks, commit.

   ```python
   @dataclass(frozen=True)
   class Period:
       start: date
       end: date
       timezone: str = "UTC"
   ```

2. Add the new function that takes the object, with the body moved into
   it, and make the old function build the object and call it:

   ```python
   def report_for(period: Period) -> str:
       ...                                   # the body, reading period.start, period.end

   def report(start: date, end: date, timezone: str = "UTC") -> str:
       return report_for(Period(start, end, timezone))
   ```

   Checks, commit.
3. Move callers to the new function, a group per step. Keep the old
   function (`core/public-surface.md`).

## Traps

| Trap | Lab |
| --- | --- |
| a default that is a list or dict | `ValueError: mutable default <class 'list'> for field lines is not allowed: use default_factory`; use `field(default_factory=list)` |
| the body changed one of the parameters locally | with `frozen=True`: `dataclasses.FrozenInstanceError: cannot assign to field 'start'`; keep a local copy of that value in the body instead |
| callers passed the parameters by keyword | the old function keeps its parameter names, so they still work; the new one is only for new callers |

## Probe inputs

The old function's edge inputs, called through the old signature.

**Done when:** the old signature works as before, the new function takes
the object, and the checks and probe are unchanged.
