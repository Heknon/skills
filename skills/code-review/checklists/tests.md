# Tests

Run for every change: changed behaviour needs a test that can fail. In
full for the Tests kind (`core/review-tests.md`). Whether a test can
fail is the pytest skill's rule (`core/write-test.md`, step 5 and "Signs
a test cannot fail"); this checklist asks it of each test in the diff.

### TST1 The test checks its own stand-in

- **Ask:** does the test replace the thing it tests (a `monkeypatch`, a
  `mock.patch`, a lambda) and then assert what the stand-in returns, or
  assert only that a mock was called?
- **Scenario (lab, library service):** a notice test built a `Mock()`
  mailer and asserted only `mailer.send.called`. With the day count
  broken to 0, and with the wrong recipient: `1 passed` each time. A
  test with `mailer.send.assert_called_once_with(...)` failed on the
  same break (`AssertionError: expected call not found.`).
- **Severity:** minor; major when it is the only test of behaviour that
  moves money or data, because that behaviour is then untested.

### TST2 Changed behaviour with no test that can fail

- **Ask:** for each changed contract (`review_diff.py defs`) and each
  new branch: which test calls it and would fail if it broke? Name the
  test, or say none.
- **Severity:** minor; major for a money, security or data path.

### TST3 A test was changed to match the new code

- **Ask:** was an expected value, an assert or a `pytest.raises` changed
  or removed in the same change as the code? Then the requirement
  decides which is right (pytest: `core/test-or-code.md`).
- **Sign:** a removed `assert` or `pytest.raises`; `review_diff.py defs`
  prints `test removed:`.
- **Scenario:** a test that expected an exception is replaced by one
  that expects `None`: maybe right for the function, and certainly a
  sign that its callers' contract changed (`core/callers.md`).

### TST4 Only the happy path or the default is tested

- **Ask:** do the tests try the boundary, the error, the non-default
  argument? A test of the default hides a wrong formula for every other
  value.
- **Scenario:** a function with a default argument tested only with the
  default: a formula wrong for every other value passes.

### TST5 The fake cannot show the bug

- **Ask:** what can the test double not do that the real thing does:
  query operators, concurrency, transactions, unique indexes, time?
- **Scenario:** a fake collection that compares values cannot match
  `{"$ne": null}`, so an operator injection passes its tests.
- **Facts:** mongodb (`pymongo/mongomock.md` lists what mongomock
  lacks); pytest (`core/mocking.md`).

### TST6 A test was skipped, marked xfail or loosened

- **Ask:** was `skip`, `xfail`, a wider `approx` or a broader `except`
  added to reach green? pytest invariant 1 forbids it unless asked.

## Signs

```
TST1  +  monkeypatch\.setattr\(|mock\.patch|patch\.object\(|MagicMock\(|return_value\s*=
TST3  -  ^\s*assert\b|pytest\.raises\(
TST5  +  ^\s*class\s+Fake\w*|^\s*class\s+\w*(Stub|Dummy|InMemory)\w*
TST6  +  pytest\.mark\.(skip|xfail)|pytest\.skip\(|approx\(.*\b(rel|abs)\s*=
```
