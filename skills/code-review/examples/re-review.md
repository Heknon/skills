# Worked example: re-review after a rebase

Kind: Re-review. The outputs are from a lab run on the library service
(git 2.43.0, ruff 0.16.9, mypy 2.3.1, pytest 9.1.1, Python 3.12.14).

## The ask

> I pushed fixes for your review of the `coupons` branch and rebased
> it on main. Can you look again?

The first review, of commit `b8d59a9` "Waive late fees with a coupon
until it expires", had two findings and the verdict `changes needed`:

```
[1 blocker] src/library/fees.py:15  EDG6  naive now compared with an aware expiry
  when: fee_after_coupon(150, "SPRING") -> TypeError: can't compare offset-naive and offset-aware datetimes
  evidence: ran uv run --no-sync python -c "from library.fees import fee_after_coupon; print(fee_after_coupon(150, 'SPRING'))"
  suggest: datetime.now(UTC)
[2 minor] tests/test_fees.py  TST2  no test for a coupon before or after its expiry
  when: the comparison breaks again -> no test fails
  evidence: read tests/test_fees.py; ran pytest: 5 passed with finding 1 present
  suggest: tests on both sides of the expiry, with the time passed in
```

## Steps

1. **The earlier head**: `b8d59a9`, from the first review's *Checked*
   line.
2. **The fix on its own** (`core/re-review.md`, step 2). The branch was
   rebased, so `git diff b8d59a9..HEAD` would also show main's new
   README. The range-diff first:

   ```
   git range-diff b8d59a9~1..b8d59a9 main..HEAD
   1:  b8d59a9 = 1:  44dca5f Waive late fees with a coupon until it expires
   -:  ------- > 2:  d33909f Compare coupon expiry in UTC; test expiry
   ```

   The reviewed commit is unchanged (`=`); one new commit. Read it:
   `git show --stat d33909f` gave `2 files changed, 16 insertions(+), 3
   deletions(-)`, then `git show d33909f`.
3. **Tools on the new head** (`core/tools.md`):

   ```
   uv run --no-sync ruff check --output-format concise .   -> All checks passed!
   uv run --no-sync mypy                                    -> Success: no issues found in 9 source files
   uv run --no-sync pytest -q -p no:cacheprovider           -> 7 passed in 0.30s
   ```

4. **Each earlier finding, by its scenario**:
   - 1: the same call that raised before now answers:
     `fee_after_coupon(150, 'SPRING')` printed `150` (the coupon
     expired on 1 June 2026, and the lab ran on 26 September 2026). The
     comparison at `src/library/fees.py:18` uses `now`, set at line 17
     to `datetime.now(UTC)` when not given. **Fixed.**
   - 2: `tests/test_fees.py:14` (31 May, fee 0) and `:18` (2 June, fee
     150) pass `now` in, on both sides of the expiry. **Fixed.**
5. **The fix as new code** (`core/checklist.md`, `core/callers.md`).
   `git diff --output=$env:TEMP\fix.diff 44dca5f..HEAD`, then:

   ```
   review_diff.py defs  -> src/library/fees.py:13  fee_after_coupon
                               parameters: (fee_cents: int, code: str | None) -> (fee_cents: int, code: str | None, now: datetime | None = None)
   review_diff.py signs -> src/library/fees.py:14  EDG2  ...
                           src/library/fees.py:14  MOD1  ...
   ```

   The new parameter has a default, so existing calls keep working;
   `git grep -n -w fee_after_coupon -- src tests` found only the tests.
   EDG2 and MOD1 point at `now: datetime | None = None`: a caller could
   pass a naive `now` and get the first finding's `TypeError` back.
   The only callers are tests, which pass aware values; that is a
   future risk with no caller today, so no finding (`core/rank.md`
   step 2 would make it minor at most, and there is no scenario yet).
6. **Verdict**: both findings fixed, nothing new, tools clean.

## The answer

```
## Verdict
approve: both earlier findings are fixed; the fix adds nothing new; ruff, mypy and 7 tests pass

## Findings
earlier:
[1 blocker] fixed: src/library/fees.py:17 takes now in UTC; fee_after_coupon(150, "SPRING") -> 150, no TypeError
[2 minor] fixed: tests/test_fees.py:14 and :18 test both sides of the expiry
new:
none

## Checked
- reviewed: coupons at d33909f against main at 9fb711f; earlier review at b8d59a9
- git range-diff b8d59a9~1..b8d59a9 main..HEAD: b8d59a9 = 44dca5f (unchanged), d33909f new
- git show d33909f: 2 files changed, 16 insertions(+), 3 deletions(-)
- uv run --no-sync ruff check .: All checks passed!
- uv run --no-sync mypy: Success: no issues found in 9 source files
- uv run --no-sync pytest -q: 7 passed
- ran: fee_after_coupon(150, 'SPRING') -> 150
- callers of fee_after_coupon: tests only (git grep)

## Not reviewed
- 44dca5f again: unchanged since the first review (range-diff =)
```
