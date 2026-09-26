# Worked example: review a branch

Kind: Diff. Copy the order of the steps and the answer's shape. The
outputs are from a lab run on a small library service (FastAPI 0.141.1,
pydantic 2.13.5, ruff 0.16.9, mypy 2.3.1, pytest 9.1.1, git 2.43.0);
the paths are Linux ones, and the PowerShell forms are *not run on
Windows*.

## The ask

> Can you review the `rating` branch before I merge it? It just adds
> the average rating to the book page.

## Steps

1. **Scope** (`core/scope.md`). `git status --short`: nothing.

   ```
   git merge-base main HEAD                     -> 6b4f0bc...
   git diff --shortstat main...HEAD             -> 3 files changed, 14 insertions(+), 2 deletions(-)
   git diff --output=$env:TEMP\review.diff main...HEAD
   review_diff.py scope                         -> 3 files, +14 -2
                                                     src/library/reviews.py  +8 -0  modified
                                                     src/library/api.py  +5 -1  modified
                                                     tests/test_api.py  +1 -1  modified
                                                   no two files received the same edit
   git log --reverse --format="%h %an %s" main..HEAD -> 3c6aecf Lab Author Show the average rating on the book page
   ```

   All three files are read line by line; nothing is left out.
2. **Tools** (`core/tools.md`). No CI file in this repository, so the
   tools `pyproject.toml` configures, on the branch:

   ```
   uv run --no-sync ruff check --output-format concise .   -> Found 2 errors.
   uv run --no-sync mypy                                    -> Success: no issues found in 7 source files
   uv run --no-sync pytest -q -p no:cacheprovider           -> 3 passed in 0.34s
   ```

   ruff found something, so the base too: `git switch --detach
   6b4f0bc`, ruff printed `All checks passed!`, `git switch -` printed
   the branch `rating` again. `review_diff.py newerrors base head`:

   ```
   src/library/reviews.py:10:41: B006 Do not use mutable data structures for argument defaults
   tests/test_api.py:9:89: E501 Line too long (91 > 88)
   2 new tool line(s) in ... that ... does not have
   ```

   Two new tool lines: CI would fail. They go under *Checked*, as they
   are.
3. **Callers** (`core/callers.md`). `review_diff.py defs`:

   ```
   src/library/api.py:12  BookOut.<fields>
       fields: +rating: float
   1 changed contract(s)
   ```

   `average_rating` is new, so its callers are in the diff.
   `git grep -n -w -E "average_rating|BookOut" -- src tests`: only
   `src/library/api.py` (lines 7, 12, 19, 25, 26) and the definition;
   the same search on `main` found only `api.py`. `BookOut` is a
   response model, and a new field in a response does not break a
   client (api: `core/compatibility.md`). `verdict callers: all hold`.
4. **Checklists** (`core/checklist.md`). A route and a response model
   changed: correctness, errors, edge cases, tests, api-contract,
   security. `review_diff.py signs`:

   ```
   src/library/reviews.py:14  EDG1  avg = t / len(ratings)
   src/library/reviews.py:15  COR7  return round(avg, 1)
   tests/test_api.py:9  TST3 (removed line, old numbering)  assert client.get("/books/b-1").json() == {"id": "b-1", "title": "Dune"}
   3 lead(s) from 53 signs; open each line and decide
   ```

   - EDG1 (empty): `len(ratings)` is 0 for a book nobody has rated.
     Every new book. Run it (`core/tools.md`, "Run a case"):

     ```
     uv run --no-sync python -c "from library.reviews import average_rating; average_rating([])"
       -> ZeroDivisionError: division by zero
     TestClient(app, raise_server_exceptions=False).get("/books/b-2")
       -> 500 Internal Server Error
     ```

     A finding.
   - COR7 (`round`): a display value rounded once, to one decimal. Set
     aside.
   - TST3 (a changed assert): the expected body gained `"rating": 4.3`,
     which is the change's purpose. Set aside; but the tests try only
     `b-1`, which has ratings: a TST4 finding.
   - Read by hand: `t`, `r`, `Rating`, and the comment `# work out the
     rating` above the line that does it: nits. B006 on line 10 is
     already a tool line; with the default never used, no scenario of
     its own, so no finding.
5. **Rank** (`core/rank.md`). A 500 on every unrated book is a crash on
   a normal input: blocker. The test gap: minor. Names and the comment:
   nits, grouped.
6. **Verdict** (`core/verdict.md`): a blocker and two new tool lines,
   so `changes needed`.

## The answer

```
## Verdict
changes needed: 1 blocker (GET /books/{id} answers 500 for a book with no ratings), and CI fails (ruff B006, E501)

## Findings
[1 blocker] src/library/reviews.py:14  EDG1  average of no ratings divides by zero
  when: GET /books/b-2, a book nobody has rated -> 500 (ZeroDivisionError at reviews.py:14)
  evidence: ran TestClient(app).get("/books/b-2") -> 500; average_rating([]) -> ZeroDivisionError
  suggest: return None when there are no ratings, and make BookOut.rating float | None
[2 minor] tests/test_api.py:8  TST4  only a rated book is tested
  when: the unrated case breaks again -> no test fails
  evidence: read tests/test_api.py:8-13
  suggest: a test that GET /books/b-2 answers 200 with rating null
[3 nit] naming and style, grouped:
  src/library/reviews.py:11  t and r: total and rating say more; sum(ratings) does the loop
  src/library/api.py:24  the comment repeats the next line
  src/library/api.py:25  Rating: a local variable in lower case
seen before this change (not in the verdict):
  none

## Checked
- reviewed: rating at 3c6aecf against main at 6b4f0bc (merge base), 3 files +14 -2
- uv run --no-sync ruff check .: Found 2 errors. New on this branch: src/library/reviews.py:10:41: B006, tests/test_api.py:9:89: E501 (base: All checks passed!)
- uv run --no-sync mypy: Success: no issues found in 7 source files
- uv run --no-sync pytest -q: 3 passed
- callers: git grep average_rating and BookOut on the branch and on main: only src/library/api.py
- ran: average_rating([]) and GET /books/b-2, in the project's interpreter
- passes: correctness, errors, edge-cases, tests, api-contract, security
- merge: git merge-tree --write-tree main HEAD exited 0

## Not reviewed
none
```

Seniority's closing headings follow these.
