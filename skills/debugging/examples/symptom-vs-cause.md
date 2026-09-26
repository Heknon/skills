# Worked example: the line that raised was not the cause

Kinds: Fix, Read, Inspect. Copy the order of the steps and the answer's
shape. Outputs are from a lab run on Python 3.12.14 and pytest 9.1.1,
in a copy of the `missing-key` sandbox.

## The ask

> `uv run python -m sales data/may.csv` crashes with KeyError: 'region'
> in report.py. April's file works. Fix it.

## Steps

1. **Reproduce both** (`core/reproduce.md`):

   ```
   $ uv run python -m sales data/april.csv
   North          140.00
   South           80.00
   $ uv run python -m sales data/may.csv
   Traceback (most recent call last):
     File "<frozen runpy>", line 198, in _run_module_as_main
     File "<frozen runpy>", line 88, in _run_code
     File "/home/user/dbg/ex1/sales/__main__.py", line 14, in <module>
       main(sys.argv)
     File "/home/user/dbg/ex1/sales/__main__.py", line 9, in main
       for region, total in sorted(totals_by_region(rows).items()):
                                   ^^^^^^^^^^^^^^^^^^^^^^
     File "/home/user/dbg/ex1/sales/report.py", line 5, in totals_by_region
       region = row["region"]
                ~~~^^^^^^^^^^
   KeyError: 'region'
   ```

   Exit 1. The reproduction fails every time.
2. **Read it** (`core/read-traceback.md`): one block; the raising frame
   and the deepest project frame are both `report.py` line 5. Was `row`
   already wrong when it arrived? The rows come from
   `sales/parser.py`, which is not in the traceback.
3. **Hypotheses** (seniority's `core/hypothesis-loop.md`):

   ```
   - H1 [open] the parser builds rows without a 'region' key for may.csv | test: print the keys it returns for each file | disproved if: may.csv's keys include 'region'
   - H2 [open] some rows of may.csv have an empty or missing region column | test: same print, and the rows | disproved if: every row has a region value
   ```

4. **One probe that splits both** (`core/inspect.md`), with no edit:

   ```
   $ uv run python -c "from sales.parser import read_rows; print(repr(sorted(read_rows('data/may.csv')[0])))"
   ['amount', 'customer', '﻿region']
   $ uv run python -c "from sales.parser import read_rows; print(repr(sorted(read_rows('data/april.csv')[0])))"
   ['amount', 'customer', 'region']
   ```

   H1 confirmed at step 4: the key is `'﻿region'`. H2 ruled out:
   the column is there, under another name. The first bytes show why
   (`core/shrink.md`):

   ```
   $ uv run python -c "print(open('data/may.csv', 'rb').read(26)); print(open('data/april.csv', 'rb').read(23))"
   b'\xef\xbb\xbfregion,customer,amount\n'
   b'region,customer,amount\n'
   ```

   may.csv starts with a UTF-8 byte order mark; `encoding="utf-8"` keeps
   it as part of the first column's name.
5. **Fix the cause, in the parser**, not in the report:

   ```
   -    with open(path, newline="", encoding="utf-8") as f:
   +    with open(path, newline="", encoding="utf-8-sig") as f:
   ```

   `utf-8-sig` drops the mark if it is there and reads plain UTF-8
   otherwise. Both files now work:

   ```
   $ uv run python -m sales data/may.csv
   East           310.00
   North           99.00
   South           45.25
   ```

   The tempting fix at the raising line, `row.get("region", "unknown")`,
   was tried in the lab on a copy: it printed `unknown 454.25` and exit
   0, every sale under one wrong region.
6. **Keep the reproduction as a test** (pytest's `core/write-test.md`),
   in `tests/test_report.py`:

   ```python
   def test_export_with_byte_order_mark(tmp_path):
       export = tmp_path / "bom.csv"
       export.write_bytes(b"\xef\xbb\xbfregion,customer,amount\nEast,Dune,310.00\n")
       assert totals_by_region(read_rows(export)) == {"East": 310.0}
   ```

7. **Prove it** (`core/prove-the-fix.md`):

   ```
   $ uv run pytest -q
   3 passed in 0.01s
   $ git stash push -- sales/parser.py
   $ uv run pytest -q
   FAILED tests/test_report.py::test_export_with_byte_order_mark - KeyError: 're...
   1 failed, 2 passed in 0.02s
   $ uv run python -m sales data/may.csv
   KeyError: 'region'
   $ git stash pop
   $ uv run pytest -q
   3 passed in 0.01s
   ```

## The answer

```
## Cause
sales/parser.py opened the export with encoding="utf-8". data/may.csv
starts with a UTF-8 byte order mark (b'\xef\xbb\xbf'), which that
encoding keeps, so the first column was named '﻿region' and
report.py:5 found no 'region' key. April's file has no mark.

## Reproduction
uv run python -m sales data/may.csv -> exit 1, KeyError: 'region' at
sales/report.py line 5.

## Fix
sales/parser.py: encoding="utf-8-sig", which drops the mark when present.
Added tests/test_report.py::test_export_with_byte_order_mark.

## Proof
With the fix: may.csv prints East 310.00, North 99.00, South 45.25;
uv run pytest -q: 3 passed. With the parser change stashed: the new test
fails with KeyError: 'region' (1 failed, 2 passed) and the command fails
as before. Restored: 3 passed.

## Result
Added test_export_with_byte_order_mark in tests/test_report.py.

## Checked
uv run pytest -q: 3 passed; 1 failed with the fix reverted.

## Not checked
Other exports with a mark in another column name; only the first column
can carry it.

## Done when
may.csv prints its regions: observed at step 5.

## Not done
none

## Unverified
none

## Decided for you
Kept the reproduction as a pytest test, since the project has a suite.
Did not use row.get('region', ...) in report.py: it hid the bug.
```
