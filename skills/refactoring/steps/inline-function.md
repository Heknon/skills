# Inline function

Replace calls of a function with its body, and remove the function. The
reverse of `extract-function.md`, used when a function adds nothing but
a name.

## Preconditions

- Every caller is found (`core/every-reference.md`). A public function
  with callers outside this repository is not inlined; at most its
  callers here are.
- The function is not reached by name: no registry, table, string,
  entry point, or patch target (`core/dead-code.md` lists how the lab
  found those).
- It is not recursive and not overridden in a subclass.

## Mechanics

1. For each call, copy the body in place of the call. Parameters become
   the argument expressions, evaluated once: if an argument is anything
   but a plain name or constant, assign it to a local first.
2. A `return expr` at the end becomes an assignment to the variable the
   call was assigned to. A `return` in the middle means the body does
   not inline cleanly: leave this call.
3. Checks after each caller, or after all in one step if there are few.
4. Remove the function in its own step (`core/dead-code.md`), after a
   search that finds no hit but the definition.

## Traps

| Trap | Lab |
| --- | --- |
| an argument with a side effect, copied into each use | `square(next(it))` gave 4; the inlined `next(it) * next(it)` gave 6 |
| a test patches the function | removing it fails the test: `AttributeError: <module ...> does not have the attribute '<name>'` (the same message as a missed rename) |
| the function's default argument was evaluated at `def` time | inlined, the expression runs at every call; see `replace-magic-value.md` |

## Probe inputs

Arguments with side effects or costs, if any caller passes them; the
edge inputs of the body.

**Done when:** no caller remains, the function is gone in its own
commit, and the checks and probe are unchanged.
