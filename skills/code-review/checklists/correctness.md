# Correctness

Always run (`core/checklist.md`). One pass: read every hunk with only
these questions. A sign is where to look, not a finding; most logic
bugs have no sign, so every hunk is read whatever the signs say.

### COR1 A bound is off by one

- **Ask:** does each slice end, range end and comparison take exactly
  what the requirement says: "10 or more", "up to 1 kg", "page 2"?
- **Sign:** `+ 1` or `- 1` beside an index or slice; `<` or `>` against
  a limit, a count or an amount.
- **Scenario:** the rule says "18 and over", the code says `age > 18`:
  a reader who is exactly 18 is refused.
- **Severity:** blocker when every call returns wrong data; major when
  one boundary input is wrong (exactly the limit).

### COR2 A condition is inverted or incomplete

- **Ask:** read each `if` aloud with a concrete input. Is `not`, `and`,
  `or`, `==`, `is None` the right way round? Is a case missing?
- **Sign:** a changed `if`, `elif`, `while` or `return <comparison>`.
- **Scenario:** `if loan.returned: charge the late fee` charges readers
  who returned on time and never those who did not.
- **Severity:** as COR1.

### COR3 A formula uses the wrong operand or unit

- **Ask:** work one example by hand from the requirement, then through
  the code. Percent, cents against euros, grams against kilograms,
  seconds against milliseconds.
- **Sign:** `* 100`, `/ 100`, `// 100`, `* 1000`, a rate or percent.
- **Scenario:** a timeout read in seconds and passed where milliseconds
  are expected: 30 becomes 0.03 s and every slow call fails.
- **Severity:** blocker when money or stored data is wrong for normal
  input.

### COR4 A contract changed: parameters, defaults, return, raise

- **Ask:** what did callers rely on before? A default they omit, an
  exception they catch, a value they never checked for `None`.
- **Sign:** a changed `def` line or default; a removed `raise`; a new
  `return None`; `review_diff.py defs` lists each one.
- **Scenario (lab, library service):** `get_book` returned `None`
  instead of raising; `loan_slip`, outside the diff, still caught the
  exception and then read `book.title`: `AttributeError` for an unknown
  id.
- **Severity:** set at the caller that breaks (`core/callers.md`).

### COR5 The docstring, comment or name says something else

- **Ask:** does the code do what its docstring, comment, name or the
  commit message says? The words are the requirement you can check
  against; when they disagree, one of them is wrong.
- **Sign:** "or more", "at least", "at most", "up to", "rounded",
  "default", "never", "always" in added text.
- **Scenario:** docstring "rounded half up", code `//`: every half cent
  is rounded down.
- **Severity:** the code's failure decides; a wrong docstring over
  right code is minor.

### COR6 Shared state is changed where the caller does not expect it

- **Ask:** does the change mutate an argument, a module-level object or
  a class attribute that other calls or requests also see?
- **Sign:** `global`; `.append(`, `.update(`, `+=` on a module name or a
  parameter.
- **Severity:** major when a second call sees the first call's data.
  Under threads this is concurrency (`concurrency.md`).

### COR7 Money or counts in floats

- **Ask:** are amounts kept in integer cents or `Decimal`, and rounded
  once, where the requirement says?
- **Sign:** `float` beside price, amount, total or cents; `round(`.
- **Severity:** major when a total can be off by a cent that is
  charged; minor for a display.

### COR8 A copy-and-paste slip

- **Ask:** in repeated lines, does each use its own variable (`a.x`,
  `b.x`), its own key, its own message?
- **Sign:** none a search can see: read the repeated lines side by side.

## Signs

```
COR1  +  \[[^\]]*[-+]\s*1\s*\]|[-+]\s*1\s*$|range\(\s*1\s*,
COR1  +  \w*(balance|limit|max|min|count|total|stock|qty|size|len)\w*\s*[<>]=?|[<>]=?\s*\w*(balance|limit|max|min|count|total|stock|qty|LIMIT|MAX|MIN|COUNT|ORDERS)
COR2  +  ^\s*(if|elif|while)\b.*(\bnot\b|!=|\bis not\b)
COR3  +  (\*|//?)\s*(100|1000|60|3600)\b|\bpercent\b.*(\*|/)
COR4  -  ^\s*raise\b
COR4  +  ^\s*return None\b|^\s*return\s*$
COR4  +  ^\s*(async\s+)?def\s.*=\s*(True|False|None|\d+)
COR5  +  \b(or more|at least|at most|up to|or less|rounded|by default|never|always)\b
COR6  +  ^\s*global\s
COR7  +  \bfloat\b.*\b(price|amount|total|cents)|\bround\(
```
