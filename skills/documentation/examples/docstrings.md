# Worked example: cleaning up a module's docstrings

Follow this when asked to add, improve or clean up docstrings. Copy the
order and the shape; change the facts.

## The ask

> Clean up the docstrings in `src/billing/charges.py`.

"Clean up" allows adding, rewriting and deleting (`python/docstrings.md`,
Scope).

## Step 1: the style

`mkdocs.yml` has no mkdocstrings, and `pyproject.toml` no pydocstyle
setting. The package's other module, `gateway.py`, uses one-line
summaries ending with a full stop, triple double quotes, and the google
sections appear in `charge()`. So: google style, summary on the first
line, full stop, no types in `Args:` since every parameter is annotated.

## Step 2 and 3: each function

The module, before:

```python
def charge(customer_id: str, amount: int, retries: int = 5, delay: float = 0.5) -> dict:
    """Charge.

    Args:
        customer_id: The customer id.
        amount: The amount.
        retries: The retries.
        delay: The delay.
    """
    if amount <= 0:
        raise ValueError("amount must be positive")
    for attempt in range(retries):
        try:
            result = send(customer_id, amount)
            break
        except GatewayTimeout:
            time.sleep(delay * (attempt + 1))
    else:
        raise GatewayTimeout(customer_id)
    _last_payment[customer_id] = result["id"]
    return {"id": result["id"], "status": result["status"], "attempts": attempt + 1}


def format_amount(amount: int) -> str:
    """Format amount."""
    return f"{amount / 100:.2f}"


def last_payment(customer_id: str) -> str | None:
    return _last_payment.get(customer_id)


def _cents(value: str) -> int:
    """Convert a value to cents."""
    return round(float(value) * 100)
```

| Function | Public | Hidden facts, from the code | Verdict |
| --- | --- | --- | --- |
| `charge` | yes, tested from outside | raises `ValueError` (line 19) and `GatewayTimeout` (line 27); `retries` counts all attempts (`range(retries)`, line 20); `delay` is seconds and grows (`time.sleep(delay * (attempt + 1))`, line 25); writes module state `_last_payment` (line 28); returns a `dict` with keys `id`, `status`, `attempts` (line 29); `amount` is cents (see `format_amount`) | a docstring naming exactly those facts; drop `customer_id`, whose description only repeated its name |
| `format_amount` | yes | `amount` is cents: divided by 100 (line 34), and the test passes 1234 for "12.34" (`tests/test_charges.py:17`) | rewrite: the existing one repeats the name |
| `last_payment` | yes | only payments made by this process: it reads the module variable `_last_payment`; `None` when there is none | one line |
| `_cents` | no | none; the name says it | delete the docstring, which repeats the name |

## The change

```
$ git diff -U0 -- src/billing/charges.py
@@ -10 +10,3 @@ def charge(customer_id: str, amount: int, retries: int = 5, delay: float = 0.5)
-    """Charge.
+    """Charge a customer through the payment gateway, retrying on timeouts.
+
+    Records the payment id for `last_payment`.
@@ -13,4 +15,11 @@ def charge(customer_id: str, amount: int, retries: int = 5, delay: float = 0.5)
-        customer_id: The customer id.
-        amount: The amount.
-        retries: The retries.
-        delay: The delay.
+        amount: In cents. Must be positive.
+        retries: Attempts in total, not extra attempts after the first.
+        delay: Seconds. The wait after the nth timeout is `delay * n`.
+
+    Returns:
+        Keys `id` (the payment id), `status` (the gateway's status) and
+        `attempts` (how many calls were made).
+
+    Raises:
+        ValueError: If `amount` is not positive.
+        GatewayTimeout: If every attempt timed out.
@@ -33 +42 @@ def format_amount(amount: int) -> str:
-    """Format amount."""
+    """Format an amount in cents as a decimal string: 1234 gives "12.34"."""
@@ -37,0 +47 @@ def last_payment(customer_id: str) -> str | None:
+    """The id of the customer's last payment made by this process, or None."""
@@ -42 +51,0 @@ def _cents(value: str) -> int:
-    """Convert a value to cents."""
```

Every changed line is inside a docstring.

## The checks

```
$ uv run --no-sync python -c "import billing.charges"
(no output, exit 0)

$ uv run --no-sync pytest -q tests
...                                                                      [100%]
3 passed in 0.01s
```

The module is not in an API reference page, so no site build.

## The answer

```
## Changed
- src/billing/charges.py: rewrote the docstrings of charge() and
  format_amount(), added one to last_payment(), removed the one on
  _cents(). Only docstring lines changed.

## Sources
- amount is in cents: format_amount divides by 100 (charges.py:34);
  tests/test_charges.py:17 expects 1234 to give "12.34".
- retries counts all attempts: range(retries) (charges.py:20).
- delay is seconds and grows: time.sleep(delay * (attempt + 1)) (charges.py:25).
- charge raises ValueError (charges.py:19) and GatewayTimeout (charges.py:27).
- returned keys id, status, attempts: charges.py:29.
- last_payment only sees this process: it reads _last_payment (charges.py:6, 28, 38).

## Not verified
- That the gateway itself takes cents. The gateway's send() does not say;
  a reply from its owner or its docs would confirm it.

## Not done
- charge() sleeps once more after the last timeout before raising
  (charges.py:25-27). Probably unintended; not changed.
```
