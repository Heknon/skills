# Context propagation

**Verdict you produce:** for each boundary the unit of work crosses, one of
`automatic`, `inject and extract`, `link by key`, and the carrier that
crosses it. Each boundary goes into `vocabulary.md` under *Boundaries*.

The trace context is a `trace_id`, a `span_id` and a `trace_flags` byte. It
lives in the current `Context`, which opentelemetry-python keeps in a
`contextvars` variable by default. Anything that starts a new execution unit
without copying that variable starts a new trace. Invariant 9 says the
library carries it. This procedure says which library call, per boundary.

All names are from opentelemetry-python 1.2x. Default propagator is
`OTEL_PROPAGATORS=tracecontext,baggage`, which writes the headers
`traceparent` and `tracestate`. A `traceparent` value looks like
`00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`. The last byte is
`01` when sampled.

## Questions, for each boundary

1. **What kind of boundary is it?** Thread, process, HTTP call, queue, or
   none of these. Find the row in the table below.
2. **Does the far side run the SDK with the same propagator?** Read its
   `OTEL_PROPAGATORS`. No SDK on the far side: verdict `link by key`.
3. **Can a string cross?** A header, an environment variable, a message
   attribute, an argument. No string can cross: verdict `link by key`.
4. **Does the far side start after the near span exists?** A subprocess
   started per unit can take the unit's context. A worker started once at
   session start cannot take a per unit context from its environment. Then
   the string must ride each message, or the verdict is `link by key`.
5. **Does the far work belong to this unit, or is it its own unit?** Belongs:
   the far span is a child, `context=` the extracted context. Its own unit: the
   far span is a root with `links=[Link(...)]`. See `traces/parent-or-link.md`.

## Mechanism per boundary

| Boundary | Verdict | What to call |
| --- | --- | --- |
| `asyncio` task | automatic | nothing; a task runs in a copy of the context |
| `threading.Thread`, `ThreadPoolExecutor` | automatic | `from opentelemetry.instrumentation.threading import ThreadingInstrumentor` then `ThreadingInstrumentor().instrument()` once at startup, package `opentelemetry-instrumentation-threading` |
| a thread you cannot instrument | inject and extract | `context = opentelemetry.context.get_current()` before submit; `token = opentelemetry.context.attach(context)` at the start of the work and `opentelemetry.context.detach(token)` at the end; or submit `contextvars.copy_context().run(function)` |
| `subprocess`, `multiprocessing` started per unit | inject and extract | `carrier = {}`; `opentelemetry.propagate.inject(carrier)`; pass `carrier["traceparent"]` as environment variable `TRACEPARENT`; far side `context = opentelemetry.propagate.extract({"traceparent": os.environ["TRACEPARENT"]})`; `tracer.start_as_current_span(name, context=context)` |
| xdist worker | link by key | workers start once per session, so a test on a worker is its own root; `cycle.id` and `session.id` are the keys; `PYTEST_XDIST_WORKER` holds the worker name |
| HTTP through an instrumented client | automatic | the instrumentation calls `inject` on the request headers |
| HTTP through a bare client | inject and extract | `opentelemetry.propagate.inject(headers)` before the call; server side `opentelemetry.propagate.extract(request.headers)` |
| queue, producer side | inject and extract | span kind `PRODUCER`; `inject(message_attributes)` |
| queue, consumer side | inject and extract, as a link | `context = extract(message_attributes)`; `span_context = opentelemetry.trace.get_current_span(context).get_span_context()`; `tracer.start_as_current_span(name, kind=SpanKind.CONSUMER, links=[Link(span_context)])` |
| no string can cross | link by key | both sides carry the same correlation key from `core/correlation-keys.md`; the viewer joins on it |

The propagator class behind `inject` and `extract` for W3C headers is
`opentelemetry.trace.propagation.tracecontext.TraceContextTextMapPropagator`.
Call the module functions, not the class, so `OTEL_PROPAGATORS` stays in
charge. Signatures:
`inject(carrier, context=None, setter=DefaultSetter())`,
`extract(carrier, context=None, getter=DefaultGetter())`.

The runtime context is chosen by `OTEL_PYTHON_CONTEXT`. Unset means
`opentelemetry.context.contextvars_context.ContextVarsRuntimeContext`.

## Rebuilding a context from stored ids

When the far side wrote `trace.id` and `span.id` somewhere as hex strings and
nothing else crossed, a link can still be built:

```python
from opentelemetry.trace import Link, SpanContext, TraceFlags

span_context = SpanContext(
    trace_id=int(trace_id_hex, 16),
    span_id=int(span_id_hex, 16),
    is_remote=True,
    trace_flags=TraceFlags(TraceFlags.SAMPLED),
)
link = Link(context=span_context)
```

Use it for a link only. Never make a rebuilt context a parent.

## Verdict

Write into `vocabulary.md` under *Boundaries*:

```
| <from> -> <to> | automatic, inject and extract, or link by key | <carrier: header, TRACEPARENT env, message attribute, key name> | <child or link on the far side> |
```

## Never

- Never pass a `Span` object to another process. It cannot be pickled and its
  `end()` must run where it started.
- Never build a `traceparent` string by hand. `inject` builds it.
- Never call `attach` without a matching `detach` in a `finally`.
- Never make a long running far side a child of a short near span. The child
  would end after its parent. Link it.
- Never read the context from a global variable you set yourself.
- Never rely on the environment for a per unit context in a process that was
  started once.

## Stop and ask

- The far side runs an SDK with a different propagator, such as `b3`. Both
  sides must set the same `OTEL_PROPAGATORS`. A person owns the far side.
- A proxy or a broker between the two sides strips unknown headers or
  message attributes. Verify with one request and read the far side's
  headers before choosing `link by key`.
- The far side has no SDK and writes no ids anywhere. Then there is no
  `link by key` either, and a person decides whether to add one.

## Examples

| Boundary | Verdict | Carrier |
| --- | --- | --- |
| Test calls the controller in a `ThreadPoolExecutor` | automatic | `ThreadingInstrumentor` |
| Test starts a helper binary per test | inject and extract | `TRACEPARENT` environment variable, far span is a child |
| Controller pushes a job onto a broker, a service processes it later | inject and extract, as a link | message attribute `traceparent`, far span is a `CONSUMER` root |
| Controller calls the entity's REST API with `requests` | automatic | `traceparent` header |
| Controller drives hardware over a serial line | link by key | `entity.id` on both sides' logs |
| Controller test runs on an xdist worker | link by key | `cycle.id`, `session.id` |
