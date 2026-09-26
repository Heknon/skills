# Sprout and wrap

**Verdict you produce:** where the new code lives, its tests, and proof
that the old code's behaviour did not change.

```
kind:      <sprout function | wrap function>
new code:  <path:function>, tests <node ids>, failing when broken
old code:  <path:function>, changed only by <the call to the sprout | nothing>
behaviour: <characterization tests or probe identical>
verdict new code: <in place | stop: needs the old code pinned first>
```

When a change must go into code that is too tangled to pin in the time
available, do not write the new logic inside it. Write it beside, as
new code with its own tests, and touch the old code as little as a
single call. This is how new behaviour enters legacy code; it is not a
refactoring, so its commit is a behaviour change named as one, apart
from any refactoring step.

## Sprout: new logic in a new function, called from the old

1. Write the new function with the logic, typed, with tests that fail
   when it is broken (pytest's `core/write-test.md`).
2. In the old code, replace the lines (or add the call) with one call
   to it. If it replaces existing lines, the sprout must first do
   exactly what those lines did: that commit is an extraction
   (`steps/extract-function.md`), and the change of logic is a second
   commit, in the sprout, with its tests.

In the lab, the currency conversion inside `build_report` became

```python
def to_eur(amount: float, currency: str, rate: str | None) -> float:
    """Amount in euros. A missing rate counts as 1, as build_report always did."""
    if currency == "EUR":
        return amount
    return amount * float(rate or 1)
```

called as `amt = to_eur(float(r["amount"]), r["currency"], r.get("rate"))`,
with three tests of its own, one pinning the 1:1 oddity; the three
characterization tests of `build_report` still passed (7 passed in all).
A later fix for the missing rate now changes `to_eur` and its tests,
not the long function.

## Wrap: new behaviour around the old function

1. Write a new function that calls the old one unchanged and adds the
   new behaviour before or after.
2. Callers that want the new behaviour call the wrapper; the old
   function and its other callers are untouched.

```python
def build_report_logged(path: str) -> str:
    """build_report, unchanged, plus one log line with the report's size."""
    text = build_report(path)
    log.info("overdue report: %d lines", text.count("\n") + 1)
    return text
```

In the lab its two tests passed: one with `build_report` replaced to
check the log line (`caplog.messages == ["overdue report: 2 lines"]`),
one calling the real function on a fixed date.

## Never

- Never put the new logic inside the untested function "because it is
  only a few lines".
- Never commit a sprout that changes what the old lines did in the same
  commit that moves them.
