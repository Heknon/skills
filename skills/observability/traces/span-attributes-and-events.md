# Span attributes and events

**Verdict you produce:** for each fact you want on a span, whether it is an
**attribute** or an **event**, its exact key or event name, and its type. The
attribute goes into `Span attributes` in `vocabulary.md`; the event goes into
`Span events`.

An attribute is a fact about the whole span. An event is a fact about one
moment inside it, with its own timestamp and its own attributes. Both live in
the span document. Neither is a log line.

## Questions

1. **Is the fact true for the whole span, or did it happen at a moment?**
   Whole span, such as an id, a size, a mode, a result count: **attribute**.
   A moment, such as a retry, a cache miss, a threshold crossed, a payload
   received: **event**. `core/signal-choice.md` question 2 sent you here for
   the second case.
2. **Is it an exception?** Use `span.record_exception(exception)` and nothing
   else. It writes an event named `exception` with attributes
   `exception.type`, `exception.message`, `exception.stacktrace` and
   `exception.escaped`. Then `span.set_status(Status(StatusCode.ERROR,
   description))`. See `core/errors-and-status.md`.
3. **What is the value's type?** Allowed: `str`, `bool`, `int`, `float`, and
   a sequence whose members are all one of those types. A `dict`, a `None`
   alone, an object or a mixed sequence is dropped by the SDK with the warning
   `Invalid type ... for attribute` or `mixes types`, and the key never
   reaches the backend. Fix the type in the vocabulary before writing code.
4. **Is the value a structure, a customer-defined dictionary, or a payload?**
   One attribute holding `json.dumps(value, sort_keys=True)` as a `str`.
   Never spread its keys into attributes; see invariant 11. Name the key
   `<noun>.json`, for example `entity.definition.json`.
5. **Is the value an id?** Send it as `str`, even when it is numeric. Elastic
   fixes a label's type from the first document that arrives, and a second
   type for the same key is rejected.
6. **Does an event need attributes?** Yes when the moment has facts of its
   own, such as `retry.attempt`, `retry.delay_seconds`. They follow the same
   types and limits as span attributes. They are on the event, not the span.

## Verdict

Write into `vocabulary.md`:

```
| <key> | string, int, float, bool | attribute or label | <allowed values or unbounded> | labels.<key with dots as underscores> |
```

or

```
| <event name> | <span names it may appear on> | <event attribute keys> |
```

## Limits, opentelemetry-python 1.2x SDK

Defaults from `opentelemetry.sdk.trace.SpanLimits`, each with the environment
variable that changes it:

| Limit | Default | Environment variable |
| --- | --- | --- |
| attributes per span | 128 | `OTEL_SPAN_ATTRIBUTE_COUNT_LIMIT`, or `OTEL_ATTRIBUTE_COUNT_LIMIT` for all |
| events per span | 128 | `OTEL_SPAN_EVENT_COUNT_LIMIT` |
| links per span | 128 | `OTEL_SPAN_LINK_COUNT_LIMIT` |
| attributes per event | 128 | `OTEL_EVENT_ATTRIBUTE_COUNT_LIMIT` |
| attributes per link | 128 | `OTEL_LINK_ATTRIBUTE_COUNT_LIMIT` |
| attribute value length | unlimited | `OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT`, or `OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT` for all |

Past a count limit the SDK drops the newest silently. Past the length limit a
string is cut with `value[:max_len]`. A JSON payload attribute needs a length
limit chosen on purpose; `traces/recipes/python_otel_setup.py` sets one.

## What Elastic does with them

- An attribute key that is not an ECS field, and that is every key you invent,
  is stored under `labels.` for strings and booleans and `numeric_labels.` for
  numbers, with every `.` in the key replaced by `_`. `cycle.id` is
  `labels.cycle_id` in the index. APM Server does this in
  `input/otlp/traces.go`, function `replaceDots`. The `Backend spelling`
  column of the vocabulary records the result.
- `deployment.environment` on the resource becomes `service.environment`.
- Events other than `exception` stay in the span document.
  UNVERIFIED: under which field Kibana 8.x shows a non exception event in the
  span flyout.
- UNVERIFIED: how APM Server stores a sequence valued attribute under
  `labels.`. Do not use sequences on a span bound for Elastic until a person
  has checked one in the index.

## Never

- Never put a dictionary in an attribute. It is dropped, not flattened.
- Never write an exception as a log line, an attribute or an event of your
  own. `record_exception` is the only way, and it comes with status `ERROR`.
- Never let a customer-defined key become an attribute key. The dictionary
  goes in one JSON string.
- Never send the same key as `int` in one span and `str` in another.
- Never record an event in a loop without a bound. 128 is the ceiling and the
  rest vanish.
- Never use a span event where there is no span. That is a log; load `logs/`.

## Stop and ask

- The payload is larger than a few kilobytes per span. That is a volume
  decision, `core/sampling-and-volume.md`, and a person approves it.
- The fact needs to be grouped by on a chart and is currently an event
  attribute. Events are not aggregable in Kibana; the fact may need to be a
  span attribute in the label tier, or a metric.

## Examples

| Fact | Verdict | Exact string | Type |
| --- | --- | --- | --- |
| The entity instance id | attribute | `entity.id` | string |
| The entity definition | attribute, label tier | `entity.definition` | string |
| The entity definition's fields, customer defined | attribute | `entity.definition.json` | string, JSON |
| A create was retried | event | `retry` with `retry.attempt` int, `retry.reason` string | |
| The controller raised | `record_exception` | `exception` | |
| Rows returned by a query | attribute | `db.response.returned_rows` | int |
| Worker heap size sampled each second | neither, it is a metric | | |
