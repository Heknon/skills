# Improve the error

**Verdict you produce:** whether the error the person saw pointed at the
cause, and if not, a better one: where it is raised, what it names, and
proof that it shows, kept in its own commit after the fix.

```
seen:       <the error the person saw, copied>
pointed:    yes | no: <what it lacked: the value, where it came from, what was expected>
where:      <file:line where the bad value entered the code>
change:     <one row of the table in step 3>
type:       <kept: <Type>; `except` search: <file:line of each catch> | new class, placed by architecture's placement/custom-errors.md>
no secrets: <the values the message and notes carry; none is a secret or personal data>
rerun:      <the reproduction, and the new last line or log line>
test:       <asserts the type and the value it names, not the whole message>
commit:     <hash> <subject>, after the fix <hash> <subject>
verdict:    improved | not needed: <why>
```

Enter here from `core/loop.md` step 7, once `core/prove-the-fix.md` has
said proven. The fix removed this cause; this step makes the next cause
of the same kind quick to find. It changes what the code reports, never
what it does.

## Steps

1. **Judge the error the person saw.** Put its last line next to the
   cause you found. Did it name the bad value, where it came from, and
   what was expected?

   | The error | Verdict |
   | --- | --- |
   | names the value and where it came from, such as `ValueError: unknown country code 'XX'; known: ['DE', 'FR', 'GB', 'IE']` | not needed: stop here |
   | a library's or the standard library's, raised inside it | do not edit the library; improve it at the project's boundary with it (step 3) |
   | names only what was asked for (`KeyError: 'price'`), or nothing (`[<class 'decimal.ConversionSyntax'>]`, `report service failed`) | improve |
   | the right text, but logged with `str(e)`, so the type and traceback were lost | improve the log call |

2. **Find where the bad value entered**: the file read, the response
   parsed, the setting loaded, the argument accepted. That is the
   boundary, often a few calls above the line that raised
   (`core/read-traceback.md`, step 5).
3. **Choose one change:**

   | Situation | Change | *lab* |
   | --- | --- | --- |
   | the message lacks the value | a message naming the value with `repr`, where it came from, and what was expected | `amount '1,50' is not a number; write it with a dot, such as 1.50` |
   | a lower-level error crosses a boundary, such as a library's into the project's | `raise New(...) from exc`; `from exc`, never `from None`, so the cause is still printed | `The above exception was the direct cause of the following exception:` above the new one |
   | the type is right; only the context is missing (which row, which file) | `exc.add_note(...)`, then a bare `raise` | a line `../feed-v2-bad.json: item 2 of a version 2 feed has keys ['price', 'quantity', 'sku']` under `KeyError: 'pricing'` |
   | a bad value passes the boundary and fails calls later | check it at the boundary and raise there, naming it | `ValueError: ../feed-v3.json: feed version 3 is not supported (known: 1, 2)` in place of `KeyError: 'qty'` two modules away |
   | an `except` that logs and goes on | `logger.exception("...")`, or `exc_info=True`, in the `except` | the traceback and its notes; `str(e)` of a `KeyError` printed only `'price'` |

   Where to log and at which level is observability's
   (`logs/levels.md`); this step only keeps the traceback.
4. **Keep the type callers catch.** Before any change of type or base,
   search for every place that catches it or a base of it:

   ```powershell
   git grep -n -E "except.*(InvalidOperation|DecimalException|ArithmeticError)|raises\((InvalidOperation|ArithmeticError)"
   ```

   The bases are in the type's `__mro__` (`python/exceptions.md` lists
   the surprising ones). If anything catches it, keep the type: raise
   the same type with a better message, or add a note. *lab
   (keep-the-caught-type):* a new `AmountError(ValueError)` escaped
   `except InvalidOperation` in `load()`, and the import that set line
   4 aside crashed on it; `raise InvalidOperation(f"amount {text!r} ...")
   from exc` kept it working. A new class, when one is earned, follows
   architecture's `placement/custom-errors.md` (when, where, fields,
   pickling).
5. **Put no secret or personal data in a message or a note.** Messages
   reach logs, tickets and screens. List every value the new text
   carries. Never a token, a password, a connection string, a URL with
   its query string, an email address or a whole record. *lab
   (no-secret-in-message):* `f"GET {url} failed"` printed
   `?token=rpt-7f3a9c2e41d84b6f` into the job's output; naming
   `{base_url}/v1/reports/{report_id}` did not. Libraries do this too:
   httpx puts the full URL in `HTTPStatusError`, SQLAlchemy the row's
   values, PyMongo the duplicated key, pydantic the rejected input
   (`python/exceptions.md`, *Library errors*). Wrapping one does not
   remove it: *lab,* `raise ReportError(...) from exc` still printed
   httpx's `for url '...?token=tok_live_9f2c'` in the chain above. Stop
   the secret where it enters the text (the token in a header, not the
   URL; `hide_parameters=True`; `hide_input_in_errors=True`). If that is
   not this change's to make, `from None` with the cause's type and
   status copied into the new message is the one exception to step 3,
   written under seniority's *Decided for you*.
6. **Rerun the reproduction.** The new text must appear in its output.
   If the fix left nothing failing, make a small input that fails the
   same way (a version 3 feed, an unknown code) and show the old line
   and the new one.
7. **Test the type and the value it names**, not the whole message:
   `pytest.raises(InvalidOperation, match="'1,50'")`, or an attribute.
   The test fails with the improvement reverted (*lab:* `Regex pattern
   did not match` against `[<class 'decimal.ConversionSyntax'>]`). With
   a test suite, write it through pytest's `core/write-test.md`.
8. **Commit it on its own, after the fix**, with git's
   `core/commit.md`: stage by file (`git add -- <path>`), the fix and
   its test first, then the improvement and its test. *lab (improve-in-
   own-commit):* reverting a mixed commit to back out a noisy message
   brought `KeyError: 'price'` back; with two commits, reverting the
   improvement kept `stock value 50.00`. If the fix and the improvement
   touch the same file, commit the fix before writing the improvement.

## Never

- Never change an exception's type or base without searching for every
  `except` and `pytest.raises` that catches it or a base of it.
- Never put a secret or personal data in a message, a note or a field
  that reaches `__str__`.
- Never `raise ... from None` to make a message tidier: the cause is
  the next person's evidence.
- Never log only `str(e)`: the type, the traceback and the notes are
  lost.
- Never mix the improvement into the fix commit, and never improve an
  error before the fix is proven.
- Never test the whole message text: it changes, and the test breaks
  for the wrong reason.
- Never edit a library's installed source to improve its message.
