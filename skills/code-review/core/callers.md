# Callers: who relies on what changed

**Verdict you produce:** for each changed contract, every caller with
what it relies on, and whether that still holds.

```
contract:  src/library/books.py:23 get_book: no longer raises BookNotFound; returns None
callers:   src/library/loans.py:8  calls it, catches BookNotFound (:9), reads book.title (:11)  BREAKS
           src/library/api.py:18   in the diff, now checks for None                   holds
searched:  \bget_book\b and \bBookNotFound\b in src and tests, on the branch and on origin/main
not covered: <what-search-misses items that apply and were not ruled out>
verdict callers: <all hold | breaks: path:line, ... | unknown: <what could not be searched>>
```

A change is judged by what relies on it. The diff shows the new
function; the bug is often in a file the diff does not touch.

## Steps

1. **List the changed contracts**:

   ```
   uv run --no-sync python <skill>\recipes\review_diff.py defs $env:TEMP\review.diff
   ```

   It compares each function and method before and after, across files,
   and prints parameters, defaults, return annotations, exceptions
   raised, a new `return None`, moves, and module names removed
   (*lab*, the library service): `get_book` "return annotation: Book ->
   Book | None" and "no longer raises: BookNotFound"; a renamed helper
   "renamed to format_date? (a new def at the same place)" with
   "parameters: (value, tz) -> (value, tz = 0)"; a model "fields:
   +rating: float". It cannot see a change of meaning with the same
   signature: a value in other units, a list now sorted differently,
   `None` returned through a variable, a new branch in the body. Read
   each changed function's body for those.
2. **Find the callers** of each one: navigation's Trace in
   (`core/trace-in.md`), with its search patterns
   (`core/search-patterns.md`) and its list of what a search misses
   (`core/what-search-misses.md`). Search the exception class too, not
   only the function: `except BookNotFound` is a caller of the raise.
   Search main's tip as well (`sources/git-diff.md`, "Callers added on
   main").
3. **Open every caller outside the diff** and write what it relies on:
   the exception it catches, the value it indexes, the default it
   leaves out, the order it expects, the type it passes on.
4. **Decide, per caller, with an input.** "Breaks" needs the input and
   the wrong result: `loan_slip("b-9", "Ann")` raised `AttributeError:
   'NoneType' object has no attribute 'title'` where it returned `Ann:
   unknown book b-9` (*lab*). Run it when a call is cheap
   (`core/tools.md`, "Run a case"); otherwise label it inferred.
5. **Write the finding at the caller's line**, not at the changed
   function, and rank it (`core/rank.md`). The fix to suggest is
   usually in the change (keep raising, or update the caller in the
   same change), not a rewrite.

## A checker as a probe

The project's mypy passed on that change: by default mypy does not
check the body of a function without annotations (linting:
`mypy/errors.md`). Run once with the flag, as a probe, not as CI's
verdict:

```
uv run --no-sync mypy --check-untyped-defs
```

*lab, mypy 2.3.1:* `src/library/loans.py:11: error: Item "None" of
"Book | None" has no attribute "title"  [union-attr]` on the branch,
where the project's own run said `Success: no issues found in 7 source
files`. A hit is a lead
for step 3; the finding is still written with its scenario. Say under
*Checked* that the flag is not in the project's config.

## Never

- Never say "no callers" from one search (navigation invariant 4).
- Never trust the tests to have found the callers: a caller with no
  test of the changed case passes (*lab*: `3 passed` with the caller
  broken).
- Never end without `verdict callers`; `unknown` with the reason is a
  valid verdict and goes under `## Not reviewed`.
