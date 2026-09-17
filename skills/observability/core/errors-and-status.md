# Errors and status

**Verdict you produce:** for each span name, the rule that decides when it
ends with status `ERROR`, and for each failure, one of `error on this span`,
`error on this span and on its parent`, `expected, no error`, or `error log
line`. The rule goes into `vocabulary.md` in the *Spans* table, as a column
named *Fails when*.

Invariant 5 fixes the mechanics: a failure is a status plus a recorded
exception. This procedure decides which span carries it and when a failure is
not an error at all. The backend counts failures from `event.outcome` on the
root span, so a wrong verdict here makes the failure rate wrong everywhere.

## How to record one

All names are from opentelemetry-python 1.2x, `opentelemetry.trace`.

```python
from opentelemetry.trace import Status, StatusCode

span.record_exception(exception, attributes=None, timestamp=None, escaped=False)
span.set_status(Status(StatusCode.ERROR, description=str(exception)))
```

- `record_exception` adds one span event named `exception` with the
  attributes `exception.type`, `exception.message`, `exception.stacktrace`
  and `exception.escaped`. The last one is a string, `"True"` or `"False"`.
  The semantic conventions mark `exception.escaped` deprecated. Leave it at
  the default.
- `set_status` takes a `Status` or a `StatusCode`, plus `description`. A
  description is stored only with `StatusCode.ERROR`. With `OK` it is
  dropped and a warning is logged.
- Once a span's status is `OK`, later calls to `set_status` are ignored. Set
  `OK` last, or not at all. `UNSET` cannot be set by a call.
- `tracer.start_as_current_span(...)` defaults to `record_exception=True` and
  `set_status_on_exception=True`. An exception that leaves the `with` block
  already does both. Call them by hand only for an exception you caught.

## Questions, for each failure

1. **Did an exception leave the span's code block?** Yes: the SDK already
   recorded it and set `ERROR`. Verdict `error on this span`. Go to 3.
2. **Did the code catch the exception and continue?** A retry, a fallback, a
   default value. Yes: call `record_exception` on the span where it was
   caught. Set `ERROR` only if the span's work did not complete. A retried
   call that succeeded ends `OK` with the exception event still on it.
3. **Does the unit of work's contract still hold after this failure?** The
   test still passes, the request still returns 200, the message is still
   acknowledged. Yes: the parent stays `OK`. Verdict `error on this span`.
   No: the parent ends `ERROR` too, with its own description. Verdict `error
   on this span and on its parent`. A child's `ERROR` never reaches the
   parent by itself. The parent fails only when its own block raises or its
   own code calls `set_status`.
4. **Was this failure the expected answer?** A test marked expected to fail
   that failed, a lookup whose 404 means "absent" and the caller handles
   absent. Yes: verdict `expected, no error`. No `record_exception`, no
   `ERROR`. Record the verdict in a label attribute from the vocabulary, such
   as `test.outcome=xfailed` or `http.response.status_code=404`. An exception
   event would become an error document and pollute the Errors tab.
5. **Is there no span around it at all?** Startup, configuration, a thread
   with no context. Yes: verdict `error log line`, level `error`, with the
   correlation keys from `core/correlation-keys.md` set by hand.

## What Elastic does with it

From `elastic/apm-data`, `input/otlp/traces.go`:

- Status `OK` becomes `event.outcome: success`. `ERROR` becomes `failure`.
  `UNSET` becomes `unknown`. For HTTP spans the outcome is also derived from
  `http.response.status_code`: `>= 500` fails a server span, `>= 400` fails a
  client span. UNVERIFIED: whether an explicit `OK` wins over a `4xx` code on
  a client span. Set the status and check `event.outcome` on the exported
  document before trusting either.
- A span event named `exception` becomes an error document in
  `logs-apm.error-<namespace>`, with `error.exception.type`,
  `error.exception.message`, `error.exception.stacktrace`,
  `error.grouping_key`, `error.culprit`, and `trace.id` and
  `transaction.id` pointing back. It needs `exception.type` or
  `exception.message`. The service's Errors tab lists these documents,
  grouped by `error.grouping_key`.
- A span event with any other name becomes a log document with
  `event.kind: event`. It does not appear under Errors.
- Error documents are kept even when the trace is not sampled. The span
  status is not: an unsampled span is never exported.

## On metrics and logs

- Failure rate, error count per transaction name, errors per minute: all
  **derived** from `event.outcome` and error documents. Emit no error
  counter beside spans. Confirm in `metrics/derived-or-emitted.md`.
- A log line at level `error` is written only under verdict `error log
  line`. Inside a span it duplicates the exception event in another index.

## Verdict

Write into the *Spans* table of `vocabulary.md`, one cell per span name:

```
| <span name> | ... | fails when: <exact condition, e.g. "the controller raises" or "http.response.status_code >= 500"> ; expected: <conditions that stay OK, or none> |
```

## Never

- Never put `failed`, `error` or `timeout` in a span name. Status carries it.
- Never set `ERROR` on a parent because a child failed. Set it because the
  parent's own work failed.
- Never record an expected failure as an exception event.
- Never write a description with `OK`. It is dropped.
- Never log an exception inside a span at level `error` and also
  `record_exception` it.
- Never swallow an exception and end the span `OK` with nothing recorded.

## Stop and ask

- The unit's contract is not written down, so question 3 has no answer. A
  person defines what "the request succeeded" means.
- A failure is expected sometimes and not other times, and the code cannot
  tell which. A person names the attribute that distinguishes them.

## Examples

| Failure | Where it is caught | Verdict |
| --- | --- | --- |
| Test assertion fails | leaves the test function | error on this span, the test root |
| `entity.create` times out once, retry succeeds | inside the create call | error event on `entity.create`, status `OK`, parent `OK` |
| `entity.create` times out three times, test fails | leaves the fixture | error on `entity.create` and on the test root |
| Test marked xfail fails | pytest reports `xfailed` | expected, no error, `test.outcome=xfailed` |
| `entity.get` returns 404 and the caller treats it as absent | inside the caller | expected, no error, `http.response.status_code=404` |
| Plugin cannot parse its config file | before `pytest_sessionstart` | error log line |

## Other backends

The recording rules above are the same everywhere; only the stored shape
differs. Tempo keeps the `exception` event on the span and TraceQL filters
on `status = error` and `event:name = "exception"`. Loki and VictoriaLogs see
an exception only if a log line is written, which the rules above forbid
inside a span. Read the status, events and exceptions rows in
`backends/<backend>/mapping.md`.
