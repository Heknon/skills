# Python types: what type a value has

**What it decides:** the type of a name or expression, and where that
answer comes from.

## In order

1. **An annotation.** `def f(x: int) -> list[str]`, `timeout: float = 3`,
   a dataclass field, a `TypedDict` or `Protocol`. If the value is
   annotated where it is created, that is its declared type. Read it.
2. **A stub.** For an installed library without annotations, a `.pyi`
   file with the same module name, or a `types-<name>` package, holds them.
3. **A type checker's inference.** Unannotated code, or a question about
   what a value is at one point (after an `if isinstance`, from a
   dictionary, from a library call): ask a checker with `reveal_type`.
   How: `tools/type-checkers.md`.
4. **The runtime.** What the value is in one real run: print
   `type(value)` at that point, in a run you are allowed to make. It tells
   you one run, not every run.

## Reading the checkers' answers

The three checkers do not always agree, because they infer differently.
For `cfg = {"a": 1, "b": [1, 2]}` (checked with ty 0.0.84, mypy 2.3.1,
Pyright 1.1.414):

- ty: `dict[str, int | list[int]]`
- mypy: `dict[str, object]`
- Pyright: `dict[str, Unknown]`

For a function with no return annotation, only Pyright infers the return
type from the body. For `parse_rows` below, which builds
`[dict(zip(header, row)) for row in reader]` with no annotations:

- ty: `Unknown`
- mypy: `Any` (mypy treats an unannotated function's return as `Any`)
- Pyright: `list[dict[str, str]]`

So for "what does this unannotated function return", ask Pyright. An
`Unknown` or `Any` from ty or mypy there means "not annotated", not "the
type cannot be known".

`Unknown` (Pyright, ty) and `Any` mean the checker could not tell. It is
not a type to report as the answer: say the type is not known statically,
and why (no annotation, an untyped library).

## Report

Write the type, which checker gave it, and its output line, copied. If two
checkers disagree and the difference matters, give both.

## Never

- Never state a type from a variable's name (`user_id` is not proof of
  `int`), from how such code usually looks, or from your own reading of
  the body. Reading gives a hypothesis; the checker's line is the answer.
- Never leave a `reveal_type` call in project code. It is a probe; see
  `tools/type-checkers.md` for where to put it.
