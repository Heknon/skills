# Shapes: the end state for each checklist ID

One file per ID of `checklist/violations.md`: the rule, why, a
**before**, an **after**, and a **test that passes on both**. Some
shapes add an after-only test that shows what the after makes possible
(a test without HTTP, an override, a rollback).

| ID | File |
| --- | --- |
| L1 | `L1-query-in-route.md` |
| L2 | `L2-logic-in-router.md` |
| L3 | `L3-db-model-at-boundary.md` |
| L4 | `L4-service-knows-http.md` |
| L5 | `L5-split-transaction.md` |
| L6 | `L6-raw-data-from-repository.md` |
| L7 | `L7-imports-point-up.md` |
| L8 | `L8-untranslated-db-error.md` |
| L9 | `L9-unswappable-dependency.md` |
| L10 | `L10-placed-against-precedent.md` |
| L11 | `L11-unhandleable-exception.md` |

This skill states the end state, never the steps. The steps from a
before to an after, each checked, are the refactoring skill's recipes,
named by the same IDs; each shape's last line gives its recipe's path.

## Before is correct, only badly placed

Each before behaves correctly on the shared test; its fault is
structural. When the code in front of you is also wrong (it leaks a
field, a transfer half applies), that is a bug: fix it on purpose as a
behaviour change, with a test that fails first, then reshape. The
after-only tests of L5 and L7 fail on their befores (*lab:* L5
`assert ([70, 0] == [100, 0])`, L7 found the function-level import).

## Running them

```
cd <skill>\shapes
uv run python check_shapes.py            # every shape, both sides
uv run python check_shapes.py L5 L8      # some
```

`check_shapes.py` writes each side's files from the fenced blocks
(`python file=before/...`, `python file=after/...`, a shared
`python file=test_shape.py`) into a temporary folder and runs pytest
there, and ends with `check_shapes: <n> of <n> sides passed`. *lab,*
Python 3.12.14 with the pins in `pyproject.toml`: `check_shapes: 22 of
22 sides passed`. The PowerShell form above is *not run on Windows*.

## An after is clean under the linting checks

An after adds no ruff or mypy finding: ruff 0.16.9 (`E4,E7,E9,F,B,
PLC0415,TRY002`) and mypy 2.3.1 on `app`, as refactoring's
`run_recipes.py` runs them. Where typing shows a bug the before already
had, the after keeps the behaviour, makes it explicit and says so beside
the code (L3: the missing user, a 500 on both sides); it never silences
the checker. Where a finding is only an untyped value, the after types
it (L6: `TypedDict`s for the raw rows).
