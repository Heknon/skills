# Worked example: pin first, then restructure

Kinds: Pin, then Step (extract function) three times. Outputs from a
lab run on Python 3.12.14, pytest 9.1.1, ruff 0.16.9, git 2.43.0,
commands run in PowerShell 7.5 on Linux.

## The ask

> build_report in billing/report.py is one long function. Restructure it
> into smaller functions.

`build_report(path)` reads a CSV of invoices and today's date, and
returns the overdue report for the morning mail.

## Steps

1. **Is it pinned?** No tests at all:

   ```
   uv run --no-sync pytest -q   -> 1 warning in 0.00s; exit 5 (no tests collected)
   ```

   "Tests pass" would prove nothing. The task becomes **Pin** first
   (`legacy/characterization.md`).
2. **What does it read besides its argument?** The file (an argument
   already) and `datetime.date.today()`. Patching the clock in place
   does not work:

   ```
   TypeError: cannot set 'today' attribute of immutable type 'datetime.date'
   ```

3. **The smallest seam** (`legacy/seams.md`): a module function the
   code calls, which a test can replace.

   ```python
   def _today():
       return datetime.date.today()


   def build_report(path):
       # overdue invoices per customer, as text for the morning mail
       today = _today()
   ```

   The program's own output, before and after, the same day:

   ```powershell
   uv run --no-sync python -m billing.mail data/invoices.csv | Out-File -Encoding utf8 .ledger/mail-after.txt
   git diff --no-index --exit-code .ledger/mail-before.txt .ledger/mail-after.txt   # diff exit: 0
   ```

   Commit: `2617d11 Add a clock seam to build_report`.
4. **Characterization tests.** The expected lines come from the code,
   for three fixed dates chosen to reach every branch: some overdue, one
   customer past the 60-day flag, nothing overdue.

   ```powershell
   uv run --no-sync python -c "import datetime, billing.report as r; r._today = lambda: datetime.date(2026, 4, 15); print(repr(r.build_report('data/invoices.csv').splitlines()))"
   ['Overdue on 15 Apr 2026', 'Acme          1     1200.00 EUR   95 days !', 'Globex        2      710.00 EUR   54 days', 'Umbrella      1       99.99 EUR   47 days']
   ```

   The test, parametrized over the three dates, patches the seam and
   copies the sample file to `tmp_path`. `Umbrella` is a GBP invoice with
   no rate, added as EUR at 1:1; that line carries the comment
   `# Finding: GBP with no rate is added as EUR at 1:1. Pinned as it is
   today.` Result: `3 passed`.
5. **Can the tests fail?** Three breaks, each restored after:

   | Break | Result |
   | --- | --- |
   | paid invoices no longer skipped | `2 failed, 1 passed` |
   | the currency rate ignored | `2 failed, 1 passed` |
   | the worst-days comparison flipped | `2 failed, 1 passed` |

   `$env:PYTHONDONTWRITEBYTECODE = "1"` was set first, so a quick
   restore could not leave stale bytecode behind. Commit:
   `8c97a5f Pin build_report with characterization tests`.
6. **Now the refactoring**, one extraction per step
   (`steps/extract-function.md`), each followed by the tests, ruff and
   the mail output compared:

   ```
   466531b Extract _read_rows from build_report
   82f5a71 Extract _overdue_by_customer from build_report
   c327976 Extract _report_lines from build_report
   ```

   Each: `3 passed`, `All checks passed!`, mail output identical. The
   statements moved as they were, the GBP conversion included:

   ```python
   def build_report(path):
       # overdue invoices per customer, as text for the morning mail
       today = _today()
       rows = _read_rows(path)
       out = _overdue_by_customer(rows, today)
       lines = _report_lines(out, today)
       return "\n".join(lines)
   ```

## The answer

```
## Steps
1. seam: 2617d11 Add a clock seam to build_report; billing.mail output identical.
2. pin: 8c97a5f Pin build_report with characterization tests; 3 passed; each
   of three deliberate breaks failed 2 of them.
3. extract function: 466531b _read_rows; 82f5a71 _overdue_by_customer;
   c327976 _report_lines. After each: 3 passed, ruff All checks passed!,
   billing.mail output identical.

## References
none: only private functions were added; build_report's name and signature
are unchanged.

## Behaviour
Characterization tests (three dates) and the mail output unchanged at every
commit.

## Findings
- A GBP invoice with no rate is added to the EUR total at 1:1 (Umbrella,
  99.99). Pinned in the test with a comment; not fixed.
- _read_rows opens the file without a with-block; unchanged, as it was.
```
