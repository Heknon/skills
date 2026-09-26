# Worked example: a type error fixed in the value

Kinds: Fix, Read. Outputs from a lab run on mypy 2.3.1.

## The ask

> mypy fails on src/greeting/banner.py in CI. Please make it green
> quickly.

```python
def format_banner(user: str) -> str:
    return f"Welcome back, {user}!"


def banner() -> str:
    """Return the login banner for the current user.

    The user comes from the APP_USER environment variable. When it is not
    set, the banner greets "guest".
    """
    user = os.environ.get("APP_USER")
    return format_banner(user)
```

## Steps

1. **Run CI's check**:
   ```
   > uv run --no-sync mypy src tests
   src/greeting/banner.py:15: error: Argument 1 to "format_banner" has incompatible type "str | None"; expected "str"  [arg-type]
   Found 1 error in 1 file (checked 3 source files)
   ```
2. **Read it** (`core/read-finding.md`): `os.environ.get` returns
   `str | None`; `format_banner` takes `str`. The error is true: when
   `APP_USER` is unset, `None` reaches the f-string.
3. **The quick way, tried and rejected** (`core/decide.md`):
   `format_banner(cast(str, user))` made mypy say `Success`, and with
   `APP_USER` unset `banner()` returned `Welcome back, None!`, against
   the docstring. A `# type: ignore[arg-type]` would do the same.
4. **Fix the value.** The docstring says what `None` means:
   ```python
   user = os.environ.get("APP_USER", "guest")
   ```
5. **Check both the checker and the behaviour**:
   ```
   > uv run --no-sync mypy src tests
   Success: no issues found in 3 source files
   > uv run --no-sync python -c "import os; os.environ.pop('APP_USER', None); from greeting.banner import banner; print(banner())"
   Welcome back, guest!
   > uv run --no-sync pytest -q
   1 passed
   ```

## The answer

```
## Result
Fixed the cause, not the message: src/greeting/banner.py passed
os.environ.get("APP_USER") (str | None) to format_banner(str). When
APP_USER is unset the banner printed "Welcome back, None!". Following the
docstring, the default is now "guest": os.environ.get("APP_USER", "guest").
A cast or type: ignore would also have turned CI green and kept the bug.

## Checked
- mypy 2.3.1: Success: no issues found in 3 source files
- banner() with APP_USER unset: Welcome back, guest!
- pytest: 1 passed

## Not checked
- none
```
