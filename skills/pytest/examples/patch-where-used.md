# Worked example: the mock that did nothing

Kinds: Mock, Fix. Outputs from a lab run on pytest 9.1.1.

## The ask

> My test patches the clock but still gets the real time. Is
> monkeypatch broken?

```python
# app/clock.py
import time
def now():
    return time.time()

# app/report.py
from app.clock import now
def stamp():
    return f"at {now():.0f}"

# tests/test_report.py
from app import report
def test_stamp(monkeypatch):
    monkeypatch.setattr("app.clock.now", lambda: 1000)
    assert report.stamp() == "at 1000"
```

## Steps

1. **Run it**: `uv run pytest tests/test_report.py::test_stamp`
   ```
   E       AssertionError: assert 'at 1790359156' == 'at 1000'
   E         - at 1000
   E         + at 1790359156
   ```
   The real time came through: the patch did not reach `stamp`.
2. **Find the name the code under test uses** (`core/mocking.md`):
   `app/report.py` does `from app.clock import now`. That import copied
   the function into `app.report` as `app.report.now` when the module
   was loaded. Replacing `app.clock.now` afterwards changes `app.clock`
   only; `stamp` still calls its own `now`.
3. **Patch where it is used**: `monkeypatch.setattr("app.report.now",
   lambda: 1000)`. Run: `1 passed`.
4. The same mistake with `mocker.patch("app.clock.now",
   return_value=1000)` failed in the same way; monkeypatch is not
   broken, and switching tools would not help.
5. **Can it fail?** Changed `stamp` to return `f"at {now() + 1:.0f}"`:
   `assert 'at 1001' == 'at 1000'`. Restored: `1 passed`.

## The answer

```
## Result
monkeypatch works; it patched a name stamp() does not use. app/report.py
imports `from app.clock import now`, so stamp() calls app.report.now.
Changed the test to patch "app.report.now". The alternative is to change
report.py to `from app import clock` and call clock.now(); then patching
app.clock.now works, and every module that uses the clock the same way can
be patched in one place.

## Checked
- Before: assert 'at 1790359156' == 'at 1000' (the real clock).
- After: tests/test_report.py::test_stamp passed.
- Broke stamp (now() + 1): the test failed with 'at 1001' != 'at 1000'.
  Restored: passed.

## Not checked
- Other tests that patch app.clock.now: searched, none in this repository.
```
