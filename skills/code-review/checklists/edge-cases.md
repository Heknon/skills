# Edge cases

Always run (`core/checklist.md`). For each input the change reads, try
the values below in your head, then run the one you doubt (a call in
the project's interpreter, or a throwaway script, `core/tools.md`).

### EDG1 Empty

- **Ask:** empty list, string, dict, file, query result: does `[0]`,
  `max()`, `min()`, division by `len()` or `next()` still work?
- **Scenario (lab, library service):** `t / len(ratings)` for a book
  with no ratings raised `ZeroDivisionError`; `GET /books/b-2` answered
  500.
- **Severity:** major when an empty input is plausible (a new customer,
  an empty cart).

### EDG2 None and missing

- **Ask:** where can a value be `None` or a key be missing: `.get(`,
  `find_one(`, `Model.get(`, an optional field? Is it checked before use?
- **Severity:** major for a 500 on a plausible request.

### EDG3 Zero, negative, huge

- **Ask:** what does a quantity, amount, percent, page or size of 0, -1
  or a very large number do? Is it bounded where it enters (a model
  field constraint, a `Query(ge=...)`)?
- **Scenario:** a transfer of -20 points moves 20 points the other
  way.
- **Severity:** blocker when a negative amount moves money or points
  the wrong way; major for a crash.

### EDG4 Duplicates and order

- **Ask:** two equal items, the same request twice, results with no
  sort: does the code assume unique or ordered data?
- **Facts:** a unique index against duplicates under concurrency is
  mongodb's (`core/writes.md`, upserts); a stable sort for pages is
  api's and mongodb's (`core/pagination.md` in each).

### EDG5 Text

- **Ask:** case, surrounding spaces, Unicode forms, very long text: is
  `Ann@Example.com` the same user as `ann@example.com` everywhere the
  change compares them?

### EDG6 Time

- **Ask:** naive against aware datetimes, the local zone of the server,
  day boundaries, month ends, a date compared with a datetime.
- **Sign:** `datetime.now()`, `utcnow()`, `date.today()`, `.days`.
- **Severity:** major when a deadline or a charge moves by a day.

### EDG7 Many

- **Ask:** what happens with 10 000 rows, a 50 MB body, a page size of
  100 000? Reads without a limit and inputs without a maximum are
  data (`data.md`) and api-contract (`api-contract.md`) items.

## Signs

```
EDG1  +  \[0\]|\[-1\]|\bmax\(|\bmin\(|/\s*len\(|\bnext\(
EDG2  +  \.get\(\s*[^"'/\s)]|\.get\(\s*["'][^/]|find_one\(|\bOptional\[|\|\s*None\b
EDG3  +  ^\s*(async\s+)?def\s.*\b(qty|quantity|amount|points|percent|page|size|limit|count|cents)\b\s*:\s*int
EDG5  +  \.lower\(\)|\.strip\(\)|==\s*\w*(email|name|code|sku)\b
EDG6  +  datetime\.now\(\)|utcnow\(|date\.today\(\)|\.days\b
```
