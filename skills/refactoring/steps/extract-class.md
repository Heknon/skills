# Extract class

Gather module functions, or part of a class, and the data they share
into a new class, keeping the old functions working.

## Preconditions

- Every reader and writer of the shared data is found: search the data's
  names (`_levels`, `_reserved`), not only the functions. Tests, fixtures
  and other modules that touch module globals directly are users too.
- The functions are pinned.

## Mechanics

1. **Add the class, unused.** Copy the functions in as methods, the
   globals as attributes. Nothing calls it yet. Checks, commit: "Add
   Inventory class beside the module functions".
2. **Make the functions delegate to one default instance that shares
   the old data**, so everything that reads or writes the globals still
   sees the same objects:

   ```python
   class Inventory:
       def __init__(
           self,
           levels: dict[tuple[str, str], int] | None = None,
           reserved: dict[tuple[str, str], int] | None = None,
       ) -> None:
           self._levels = levels if levels is not None else {}
           self._reserved = reserved if reserved is not None else {}


   _levels: dict[tuple[str, str], int] = {}
   _reserved: dict[tuple[str, str], int] = {}
   _default = Inventory(_levels, _reserved)  # the same tables, so code that uses them directly still works


   def receive(warehouse: str, sku: str, quantity: int) -> int:
       return _default.receive(warehouse, sku, quantity)
   ```

   Checks, commit: "Delegate inventory functions to a default Inventory".
3. Moving callers to instances, and retiring the globals, are later
   steps, done when asked.

## Traps seen in the lab

| Trap | What happened |
| --- | --- |
| the default instance made its own dicts (`Inventory()`) | 4 of 5 tests failed: the conftest cleared the module's `_levels`, and a test wrote levels into it the way the nightly import does, while the functions read the instance's. The step was undone (`core/step-loop.md`) and redone as above: 5 passed |
| `levels or {}` instead of `levels if levels is not None else {}` | the module's dict is empty at import time, so `or` made a new one and the sharing was silently lost (lab: `shared? False`) |
| tests or fixtures patched to point at `_default` | that is patching forward: the tests describe how other code uses the module; they stay as they are |

## Probe inputs

A sequence of calls that writes then reads (receive, reserve, available),
and a direct write to the module's data followed by a read.

**Done when:** the module functions, the module's data and the tests
behave as before, and the class exists for new callers.
