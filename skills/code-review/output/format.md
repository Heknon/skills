# The answer

Four headings, in this order, each with `none` when empty. Seniority's
closing headings come after them.

```
## Verdict
changes needed: 1 blocker (GET /books/{id} answers 500 for a book with no reviews), and CI fails (ruff B006, E501)

## Findings
[1 blocker] src/library/reviews.py:14  EDG1  average of no ratings divides by zero
  when: GET /books/b-2, a book with no ratings -> 500 (ZeroDivisionError at reviews.py:14)
  evidence: ran TestClient(app).get("/books/b-2") -> 500 Internal Server Error
  suggest: return None (and make BookOut.rating float | None) when there are no ratings
[2 minor] tests/test_api.py:8  TST4  only a book with ratings is tested
  when: the no-ratings case breaks again -> no test fails
  evidence: read tests/test_api.py:8-13
  suggest: a test for GET /books/b-2
[3 nit] naming and style, grouped:
  src/library/reviews.py:11  t and r: total and rating say more
  src/library/api.py:24  the comment repeats the next line
  src/library/api.py:25  Rating: a local variable in lower case
seen before this change (not in the verdict):
  none

## Checked
- reviewed: rating at 3c6aecf against main at 6b4f0bc (merge base), 3 files +14 -2
- uv run --no-sync ruff check .: Found 2 errors. New: src/library/reviews.py:10:41: B006, tests/test_api.py:9:89: E501
- uv run --no-sync mypy: Success: no issues found in 7 source files
- uv run --no-sync pytest -q: 3 passed
- callers: average_rating and BookOut used only in src/library/api.py (git grep)
- passes: correctness, errors, edge-cases, tests, api-contract, security

## Not reviewed
none
```

## A finding

```
[<n> <severity>] <path>:<line>  <checklist ID>  <a few words>
  when: <input or state> -> <wrong result>
  evidence: ran <command> -> <what it printed> | read <path:line> | inferred from <what>
  suggest: <the smallest fix, as text> | refactoring for later: <name>
```

| Part | Rule |
| --- | --- |
| number | findings are numbered once, in order of severity, so a re-review can refer to them |
| severity | `core/rank.md`; blockers first, nits last |
| `path:line` | the line where the failure starts; for a broken caller, the caller's line. No line: not reported |
| ID | the checklist item (COR1, SEC1, TST4), or architecture's L1 to L11 |
| `when:` | the failure scenario. Without it the finding is at most a nit |
| `evidence:` | `ran` (observed), `read` (read), `inferred` (with what would confirm it); never memory |
| `suggest:` | the smallest change that removes the scenario, as text; a restructuring is named for the refactoring skill, never done here |

Nits: at most five, in one entry, one line each. Tool lines never appear
under *Findings* unless a finding cites them with a scenario of its own.

## Checked

One line each: what was reviewed (head, base, size), every tool with
its command and summary line and the new lines, the tests with their
summary line, each caller search, each run of a case, each pass. A
reproduction outside the repository says that it was deleted.

## Not reviewed

Every file in the change not read line by line, what could not run
(a database, GitLab, Windows), and callers that could not be searched
(other repositories). `none` only when all of it was read and run.

## Posting it

The answer is shown to the person. It goes to GitLab only when asked,
as one note (`sources/gitlab-mr.md`).
