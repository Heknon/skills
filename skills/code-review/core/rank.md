# Rank: the severity comes from the failure scenario

**Verdict you produce:** one severity per finding, and the scenario
line that decided it.

```
[1 blocker] src/library/reviews.py:14  EDG1  ... when: GET /books/b-2 (no reviews yet) -> 500
decided by: a crash on a normal input: every new book has no reviews
```

## The scale (CR1)

| Severity | The scenario shows | Examples from the lab |
| --- | --- | --- |
| **blocker** | wrong or lost data, money or stock; a security hole; a crash or a red CI on a normal input | a book page answers 500 for every book without reviews; every use of a coupon raises `TypeError`; `{"$ne": null}` as a token matches; a failed write reported as saved; a password hash in a response |
| **major** | wrong behaviour on a plausible input; a broken contract a caller relies on; lost updates under normal concurrency | the boundary value (exactly 18, exactly the limit) gets the wrong answer; an unknown id crashes a caller outside the diff; two requests add one |
| **minor** | a failure that needs an unlikely input or a future change; a layering breach with no failure yet; a gap in the tests | a query in a route with no second caller (L1); an error path with no test |
| **nit** | taste: names, comments, docstrings, style no tool enforces | `t`, `r`, `Rating`; a comment that repeats the code; a missing docstring |

## Deciding

1. **Write the scenario first**: an input or state, and the wrong
   result. No scenario: at most a nit, whatever the topic.
2. **Ask how normal the input is.** Every call, or a common input:
   blocker if the result is wrong data, money, security or a crash;
   major otherwise. A boundary or a less common input: major. Needs
   something unlikely: minor.
3. **Ask what it costs.** Money, stored data, access, other users'
   data: one level up from what step 2 gives, capped at blocker.
4. **Take the owner's suggestion as a starting point.** architecture's
   L1 to L11 carry a suggested severity and a "raise to" condition
   (`checklist/violations.md`); api's review says blocking, should or
   note (`core/review.md`). Keep the suggestion unless your scenario
   meets the raise condition, then check it against the table above.
5. **When one line has two findings**, rank the line by the worse
   scenario and cite both IDs (the leak outranks the layering breach:
   `checklists/architecture.md`).
6. **Say how sure you are** with the evidence label: `ran`, `read` or
   `inferred` (seniority's levels observed, read, inferred). A blocker
   that is only inferred says what run would confirm it.

## Inflation and deflation

- A request to "be strict" changes how hard you look, not the scale.
  A missing docstring is a nit in every review.
- Nits: at most five, grouped in one entry at the end
  (`output/format.md`). Twenty naming remarks bury the off-by-one.
- Never "must", "critical" or "urgent" outside a blocker.
- A small diff does not make a blocker smaller. One character (`<` to
  `<=`) can refuse every request at the limit.
- A pre-existing problem the change does not touch is not ranked: it
  goes under *seen before this change*, outside the verdict.
