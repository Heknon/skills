# Understand an error

**Verdict you produce:** what the error means here, the value behind it,
and where that value came from, each shown by something you ran.

```
error:     <the last line, copied: type with its module, then the message>
whose:     <built-in | standard library | library <name> | project>
means:     <what this type says happened, from python/exceptions.md>
value:     <the value behind it, printed with repr where it was used: "keys ['pricing', 'quantity', 'sku']">
came from: <where that value was made: the file, the response, the setting, the call that returned None>
shown by:  <the probe or command, and what it printed>
owner:     <this skill | pydantic | api | mongodb | architecture | packaging | offline-docs>
```

`core/read-traceback.md` finds which exception to read and the frame
that matters. This file reads that exception: what its type means in
real code, which value to print, and where to look. The lookup tables
are in `python/exceptions.md`.

## Steps

1. **Copy the last line of the first exception**, character for
   character. Split it: the type with its module, then the message.
   The module says whose error it is (`python/exceptions.md`, *Read the
   last line in two parts*).
2. **Look the type up, never the words.** Find its row in
   `python/exceptions.md`. The message's words change between Python
   versions and libraries (*lab:* a JSON trailing comma reads
   `Expecting property name enclosed in double quotes` on 3.12 and
   `Illegal trailing comma before end of object` on 3.13), so reasoning,
   code and tests that match the words break. The type does not.
3. **Check the message is not one that hides its cause**
   (`python/exceptions.md`, *Messages that hide the cause*). An empty
   body and a 502 HTML page print the same `JSONDecodeError`; a byte
   order mark prints as a plain `KeyError: 'region'`.
4. **Print the value behind it**, where it was used, with `repr`: the
   keys a `KeyError` did not find, the length an `IndexError` ran past,
   the call on the line that returned `None`, the text a parse
   rejected. The message names what was asked for, not what was there.
   Print the whole value, not the one field the message names: *lab
   (read-past-the-message):* the message said `'price'`, and the record
   `{'sku': 'A1', 'quantity': 4, 'pricing': {...}}` showed a second
   renamed field that a `price`-only fix hit next. Use a probe
   (`core/inspect.md`) and remove it after.
5. **Ask where the value came from**, and check it:

   | It came from | Check |
   | --- | --- |
   | data: a file, a response, a row | read its first bytes or lines; for a response, the status and content type before the body |
   | the code: a function returned `None` or the wrong type | that function's return paths |
   | the environment: the current folder, `sys.path`, a local file named like a module, the installed version | `os.getcwd()`, `sys.path[0]`, `<module>.__file__`; navigation's `core/environment.md` |
   | a setting or a secret | which source set it (pydantic's `settings/trace.md` for settings); never print a secret's value |

6. **A library's error is settled by its installed source.** Read the
   line that raised it and the attributes it keeps (`e.response`,
   `e.orig`, `e.details`, `e.errors()`) with offline-docs
   `core/behaviour.md`. What the error means in its domain belongs to
   its owner:

   | Error | Owner |
   | --- | --- |
   | pydantic `ValidationError` | pydantic `core/read-error.md` |
   | an HTTP status, an API's error body | api `core/methods-and-status.md`, `core/errors.md` |
   | PyMongo `DuplicateKeyError`, a slow or failed query | mongodb |
   | SQLAlchemy `IntegrityError` turned into a domain error | architecture `sqlalchemy/errors.md` |
   | a package missing or at the wrong version | packaging |

7. **No traceback?** Get one, or the evidence that stands for it
   (`python/exceptions.md`, *Errors without a traceback*): a log line
   that logged `str(e)`, an exit code, an HTTP status, a wrong value.
   A log line is not enough to fix from: *lab (keep-the-traceback):*
   `record 3 failed: 'NoneType' object has no attribute 'strip'` could
   be any of the five `.strip()` calls in `clean()`; the traceback named
   one.
8. **Write the verdict**, then continue in `core/loop.md` at step 3:
   the reproduction shows this error, and the fix goes where the value
   came from.

## Never

- Never match an error by its exact words, in reasoning, in code or in
  a test: match the type and the value it names.
- Never read only the message line of a `KeyError`: print the keys that
  exist, and the whole record.
- Never make the message go with a default (`.get(key, 0)`, `or ""`):
  *lab:* `(country_name(code) or "").strip()` imported a customer with
  no country and no error.
- Never decide what a library's error means from its message alone;
  read the installed source.
- Never print a secret to understand an error; print its length or
  whether it is set.
