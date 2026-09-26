# Custom errors: when, the hierarchy, where, the fields

**Verdict you produce:** whether a built-in fits; if not, the classes,
where each lives, their fields, where each is raised and caught, and a
test per status.

```
built-in:   <ValueError | LookupError | ... fits, because no caller handles it differently> | no: <the caller that catches it by type>
classes:    <Name(Category)>, fields <names>, code "<code>"
lives in:   <path>, precedent <path:line> | default (defaults.md)
raised in:  <path>   caught or translated in: <path or the category handler>
tests:      <status or behaviour per class, run line>
```

Every behaviour quoted here was rerun in the lab on Python 3.12.14, and
the same probe printed the same lines on 3.11.15. The plan's first
draft was wrong in one place, corrected below.

## 1. When to define one

Only when something will catch it **by type** or translate it:

- a caller handles it differently from other failures (a 404 against a
  409, retry against give up, skip the row against stop the import);
- it crosses a layer boundary and is translated once there
  (`core/errors.md`, L8);
- its handler needs data from it (which id, which limit).

Otherwise raise a built-in:

| Situation | Built-in |
| --- | --- |
| a bad argument value | `ValueError` |
| a wrong type | `TypeError` |
| a missing key or item the caller asked for | `LookupError` (or `KeyError`, `IndexError`) |
| not written yet, or an abstract method | `NotImplementedError` |
| no permission at the OS or resource level | `PermissionError` |
| a deadline passed | `TimeoutError` |

Never bare `Exception` (ruff `TRY002`). One class per distinct
handling, not one per message: `OrderNotFoundError` and
`CustomerNotFoundError` both earn a class only if some code catches one
and not the other, or the handler needs `order_id`; otherwise
`NotFoundError` with a message is enough.

*eval* builtin-fits: `parse_quantity()` is a pure function whose only
caller (`app/cli.py`) already catches `ValueError`. A new
`NegativeQuantityError(Exception)` crashed that caller (*lab:*
`app.quantities.NegativeQuantityError: -3` escaped `main`); `raise
ValueError(f"quantity must not be negative: {text!r}")` kept it working.

## 2. The hierarchy

```
AppError                        one base per application or library
    NotFoundError               categories: the HTTP edge maps each
    ConflictError               to one status (404, 409, 403 ...)
        InsufficientFundsError  specific classes only where a caller needs them
    PermissionDeniedError
```

- One handler per category (api registers it; *lab,* Starlette 1.7.0:
  a handler for a base class catches its subclasses, and the nearest
  class in the MRO wins, `core/errors.md`). A new specific error needs
  no new handler.
- A class-level `code = "insufficient_funds"` gives a stable,
  machine-readable name the handler can put in the body (the recipes
  send `{"code": ..., "detail": ...}`; the problem-details shape is
  api's).
- Domain errors never subclass `HTTPException`. *lab:* a subclass of
  `HTTPException` raised in a service does give a 404 with its detail,
  which is why it looks fine; it still ties the service to FastAPI (L4,
  L11).
- A domain error may also subclass a built-in when callers outside the
  application catch the built-in: `class NotFoundError(AppError,
  LookupError)` (*lab:* an `OrderNotFoundError` below it was caught by
  `except LookupError` and still pickled with its field).
- Names end in `Error` (PEP 8; ruff `N818`: *lab,* 0.16.9, `Exception
  name QuotaExceeded should be named with an Error suffix`), unless the
  codebase's names do not.

## 3. Where

- Base and categories: one shared module (`app/errors.py`, or
  `core/errors.py`).
- Specific errors: the feature's `errors.py`, or the domain layer's in a
  by-layer codebase; one central file if that is the precedent.
- A library re-exports its public errors from its package
  `__init__.py`.
- Driver errors (`DuplicateKeyError`, `IntegrityError`) never leave the
  repository.
- Never next to the code that first raises it (L10).

`place-a-thing.md` finds the precedent; `defaults.md` applies when there
is none.

## 4. The fields

A custom error carries structured attributes for what a handler needs
(`order_id`, `limit`) and a readable `str(e)` for logs. How the class
stores them decides whether it survives `pickle` (multiprocessing,
`ProcessPoolExecutor`, task queues) and `copy.deepcopy`. The probes,
*lab,* Python 3.12.14 and 3.11.15:

| Class | `str(e)` | `e.args` | pickle and deepcopy |
| --- | --- | --- | --- |
| `__init__(self, order_id)` with no `super().__init__` | `'7'` | `(7,)` | ok |
| `__init__(self, order_id, limit)`, no `super().__init__`, message kept in `self.message` | `'(7, 100)'` | `(7, 100)` | ok |
| `__init__(self, *, order_id)`, no `super().__init__` | `''` | `()` | `TypeError: NoSuperKw.__init__() missing 1 required keyword-only argument: 'order_id'` |
| `__init__(self, *, order_id, limit)` calling `super().__init__()` | `''` | `()` | `TypeError: ... missing 2 required keyword-only arguments: 'order_id' and 'limit'` |
| `__init__(self, *, order_id, limit)` calling `super().__init__(f"order {order_id} ...")` | the message | `('order 7 over limit 100',)` | `TypeError: KwOnly.__init__() takes 1 positional argument but 2 were given` |
| `__init__(self, order_id, limit)` calling `super().__init__(f"...")` (positional fields, message to super) | the message | the message only | `TypeError: MsgOnly.__init__() missing 1 required positional argument: 'limit'` |
| **`__init__(self, order_id, limit)` calling `super().__init__(order_id, limit)`, message in `__str__`** | the message | `(7, 100)` | **ok, fields and message kept** |
| keyword-only fields with a `__reduce__` returning `(rebuild, (cls, order_id, limit))` | the message | the message | ok |
| `@dataclass` exception | `'(7, 100)'` | `(7, 100)` | ok, but `hash(e)`: `TypeError: unhashable type: 'DC'`; `@dataclass(eq=False)` is hashable |

Correction to the plan's draft: an `__init__` without `super().__init__`
does **not** leave `str(e)` empty when it takes positional arguments:
`BaseException.__new__` stores them in `args`, so `str(e)` is their
tuple (`'(7, 100)'`), not the message. It is empty only when the fields
are keyword-only.

Why pickling matters, *lab:*

- `ProcessPoolExecutor`, a job raising the keyword-only error: the
  caller got `concurrent.futures.process.BrokenProcessPool: A process in
  the process pool was terminated abruptly`, with the cause
  `TypeError: QuotaExceededError.__init__() missing 1 required
  keyword-only argument: 'limit'` raised while the parent unpickled the
  result (*eval* worker-pickle). The real error was lost.
- `multiprocessing.Pool.apply`: the result thread died with the same
  `TypeError` and the call **never returned** (the probe was stopped by
  a 30-second timeout).
- The positional form reached the caller intact:
  `__main__.Positional: order 7 over limit 100`.

So, decision AR9 (default): **positional fields passed to
`super().__init__(*fields)` in the order `__init__` takes them, the
message built in `__str__`, an optional class-level `code`.** Raise
sites may still pass fields by keyword (`QuotaExceededError(tenant,
limit=limit)` worked after the fix). Taught for reading: keyword-only
fields with `__reduce__`, and `@dataclass` exceptions.

```python
class InsufficientFundsError(ConflictError):
    code = "insufficient_funds"

    def __init__(self, account_id: int, balance_cents: int, amount_cents: int) -> None:
        super().__init__(account_id, balance_cents, amount_cents)
        self.account_id = account_id
        self.balance_cents = balance_cents
        self.amount_cents = amount_cents

    def __str__(self) -> str:
        return (f"account {self.account_id} holds {self.balance_cents} cents, "
                f"cannot send {self.amount_cents}")
```

- The message is built inside the class, not at every raise site.
- No secrets or personal data in fields that reach `__str__`, or in
  `args`: both reach logs. The recipes' `DuplicateAccountError` keeps
  `owner_email` as a field but leaves it out of the message.
- A test that the error survives a process boundary:
  `pickle.loads(pickle.dumps(e))` keeps type, fields and `str(e)`
  (`shapes/L11-unhandleable-exception.md`).

## 5. Raising

- At a translation point: `raise DomainError(...) from exc` (ruff
  `B904` flags the missing `from`: *lab* message `Within an except
  clause, raise exceptions with raise ... from err or raise ... from
  None`).
- `from None` only when the cause would leak internals.
- Catch the narrowest class; `except Exception` only at the outermost
  edge (ruff `BLE001`: `Do not catch blind exception: Exception`).
- Add context without a new class: `e.add_note("while importing row
  12")` (3.11 and later; *lab:* missing on 3.10.20).
- Never make a caller parse `str(e)` or `e.args[0]` to tell two cases
  apart: that is a missing class (L11).

## The ruff rules that flag some of this

Running and configuring them is the linting skill's; architecture never
turns a rule on unasked. *lab,* ruff 0.16.9, all present:

| Rule | Flags | Note |
| --- | --- | --- |
| `N818` | an exception name without `Error` | matches this file's naming |
| `TRY002` | `raise Exception(...)` | matches: never bare `Exception` |
| `TRY003` | a long or formatted message at the raise site, **built-ins too** | *lab:* it flagged `raise ValueError(f"quantity must not be negative: {text!r}")`; for a built-in that is style, not a reason for a custom class |
| `EM101`, `EM102` | a string or f-string literal passed to an exception | also style: `msg = f"..."; raise ValueError(msg)` satisfies them |
| `B904` | `raise` in `except` without `from` | matches: translate `from exc` |
| `BLE001` | `except Exception` | matches: only at the edge |

When a project enables `TRY003` or `EM10x`, follow its style at the
raise site; do not create a class to silence them.
