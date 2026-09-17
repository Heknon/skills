# Parent or link

**Verdict you produce:** for the span you are adding, the one span that is its
**parent**, and the list of spans it **links** to. The parent goes into the
`Spans` table of `vocabulary.md` as `Root: no`. Each link goes into the
`Required attributes` column as `link:<relation>`.

A span has exactly one parent and any number of links. The parent is where the
code ran. A link is anything else the span belongs to. Getting this wrong in
one direction puts thousands of transactions in one trace; in the other it
leaves a span with no parent and no way to find it from the screen it belongs
on.

## Questions

1. **Was a span already active in the code when this span opened?** Check it
   in code: `trace.get_current_span().get_span_context().is_valid` is `True`.
   Yes: that span is the parent. The SDK sets it. Do not pass `context=` to
   change it. No: this span is a root. Go to `core/unit-of-work.md` and confirm
   it is allowed to be one.
2. **Is there another thing this span belongs to, whose span is not the active
   one?** List each. Each one is a **link**, never a parent. The common cases:
   - the unit sits inside an outer thing, such as a test inside a session, an
     item inside a batch. The outer thing has its own root. Link to it.
   - the span operates on a long-lived thing that has a span of its own, such
     as an entity created earlier, a connection, an environment. Link to that
     span if its `SpanContext` is stored on the object. If no span exists for
     it, record its id as an attribute and stop; do not invent a span.
   - the span consumes a message, a job or a file that another span produced.
     Link to the producer's span context, carried in the message.
   - the span retries an earlier attempt. Link to the attempt it retries.
3. **Is the linked span's context available before this span starts?** Yes:
   pass it in `links=` at start. No: call `span.add_link(...)` after start,
   and note that the sampler did not see it.
4. **Does the link have a fact of its own?** Put it in the link's attributes,
   under the key `link.relation` with one of the values from the table below.

## Verdict

Write into `vocabulary.md`, in the `Spans` table row for this span:

```
| <span name> | <kind> | no | link:belongs_to, link:operates_on, ... | ... |
```

and in `Span attributes`:

```
| link.relation | string | label | belongs_to, operates_on, produced_by, retries | not indexed by Elastic |
```

## The API, opentelemetry-python 1.2x

- `from opentelemetry import trace`
- Build a link: `trace.Link(span_context, attributes)`. `span_context` is a
  `SpanContext`, from `span.get_span_context()`. `attributes` is optional.
- Pass at start: `tracer.start_as_current_span(name, links=[link])`. The
  sampler receives `links` in `should_sample`, so a link present at start can
  influence sampling.
- Add after start: `span.add_link(span_context, attributes)`. Added in
  opentelemetry-python 1.23.0. On an ended span it is dropped with the warning
  `Tried calling _add_link on an ended span`. Before 1.23.0 the method does
  not exist and links can only be passed at start.
- Limits: 128 links per span and 128 attributes per link by default,
  `OTEL_SPAN_LINK_COUNT_LIMIT` and `OTEL_LINK_ATTRIBUTE_COUNT_LIMIT`.
- Recipe: `traces/recipes/python_span_wrapper.py`, function `link_to`.

## How Elastic treats a link

- APM Server writes each OTLP link as one entry of `span.links`, with the
  linked trace id and span id, and drops the link's attributes.
  UNVERIFIED: the exact index field paths, expected `span.links.trace.id`
  and `span.links.span.id`.
- A link whose attributes contain `elastic.is_child` or `is_child` set to
  `true` is not stored as a link. APM Server treats the linked span as a child
  instead. Never set those keys.
- Kibana 8.x shows links in the span detail flyout of the trace waterfall.
  UNVERIFIED: the tab label and the first 8.x minor that shows incoming and
  outgoing links.
- The service map ignores `span.links` before 8.19. From 8.19 the service map
  reads them, Kibana pull request 215645.
- Latency, throughput, failure rate and the Dependencies screen never follow
  links. They follow the parent and `span.destination.service.resource`. A
  linked span contributes nothing to the linked trace's numbers.

## Never

- Never make the outer thing the parent to keep everything in one trace.
- Never pass `context=` to `start_span` to reparent a span onto a thing it did
  not run inside. That hides where the code ran.
- Never link to a span you have no `SpanContext` for. An id string is an
  attribute, not a link.
- Never set `elastic.is_child` or `is_child` on a link.
- Never expect a link to appear in a chart. It appears in the waterfall only.

## Stop and ask

- The active span at open time is not the one a person would call the caller,
  for example a span left active by a leaked context. That is a bug in the
  caller's instrumentation, not a reason to reparent.
- The thing to link to lives in another process and its context was never
  propagated. Propagation is `core/context-propagation.md`; do not guess ids.

## Examples

| Span | Parent | Links | `link.relation` |
| --- | --- | --- | --- |
| test root span | none, it is a root | the session root span | `belongs_to` |
| `entity.create` inside a test | the test span | none | |
| `entity.revert` on an entity created in an earlier test | the current test span | the earlier `entity.create` span, if its context is stored on the entity | `operates_on` |
| `job.run` in a consumer | the consumer's poll span | the producer's `job.enqueue` span | `produced_by` |
| `entity.create` second attempt | the current test span | the first `entity.create` span | `retries` |
| session root span | none | the cycle root span, if one exists | `belongs_to` |
