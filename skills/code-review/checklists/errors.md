# Errors

Always run (`core/checklist.md`). The question behind every item: when
this line fails, who finds out, and what do they believe happened?

### ERR1 An exception is swallowed

- **Ask:** what does the caller, the client or the log see when the
  code inside the `try` raises?
- **Sign:** `except Exception:` or bare `except:` followed by `pass`,
  `continue`, `return <default>`; `contextlib.suppress(Exception)`.
- **Scenario:** the write raises (the database is unreachable), the
  handler answers 201 with `saved: true`, and nothing was stored.
- **Severity:** blocker when the swallowed call is the request's own
  write (the client is told it is saved); major when a side effect
  (audit, e-mail, event) is lost with no log; minor when it is logged
  and the fallback is right. architecture's L8 raise rule agrees.

### ERR2 The `try` covers more than the call that may fail

- **Ask:** which one line is the `try` for? Is everything else in it
  meant to be caught too?
- **Sign:** a `try` body of several statements before a broad `except`.
- **Scenario:** a `try` added for one optional call also wraps the
  required call before it.
- **Fix to suggest:** only that call in the `try`, the exception logged.

### ERR3 Failure reported as success, or the wrong status

- **Ask:** can this route say `saved`, `ok` or 2xx after a failure? Is
  bad input a 4xx and a server fault a 5xx? The status codes and the
  error body are the api skill's (`core/errors.md`,
  `core/methods-and-status.md`).
- **Sign:** `saved=True`, `ok: True`, `success` after a `try`;
  `status_code=` changed; `HTTPException(` added.
- **Severity:** as ERR1 for a false success; major for 500 on bad input.

### ERR4 The cause is lost or the type changes

- **Ask:** does a re-raise keep the original (`from exc`)? Does a new
  exception type break a caller that catches the old one?
- **Sign:** `raise` inside `except` without `from`; `raise Exception(`.
  ruff `B904` reports the first where the project selects it (then it
  is a tool line under Checked, `core/tools.md`).
- **Facts:** where each translation happens is architecture's
  (`core/errors.md`, L8, L11).

### ERR5 A caller handles what is no longer raised

- **Ask:** for every `raise` the change removes or adds: which callers
  catch it, and what do they do now? `core/callers.md`.
- **Sign:** a removed `raise`, a new exception class, a changed
  `except` clause.

### ERR6 Resources are not released on error

- **Ask:** is every file, client, lock and session closed when the code
  between opening and closing raises?
- **Sign:** `= open(` without `with`; a client or session created
  inside a function with no `with` or `finally`.
- **Severity:** major when it leaks per request.

## Signs

```
ERR1  +  ^\s*except\s*(\(?\s*(Exception|BaseException)\b[^:]*)?:|^\s*pass\s*$|suppress\(\s*(Exception|BaseException)
ERR3  +  \b(ok|success|saved)\s*[=:]\s*True\b|status_code\s*=|HTTPException\(
ERR4  +  raise\s+Exception\(
ERR5  -  ^\s*raise\b|^\s*except\b
ERR6  +  ^\s*\w+\s*=\s*open\(
```
