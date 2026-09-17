# TraceQL and LogQL queries to paste

Stamp: Tempo 3.0 TraceQL reference and v2.8.x reference, Tempo API docs, Loki
3.7 log queries, metric queries and structured metadata pages, read
2026-09-17. PromQL, including the RED, dependency and cardinality queries, is
in `queries-promql.md`.

Rename before pasting: the attribute keys `sahara.cycle.id`,
`sahara.environment.id`, `sahara.entity.definition`,
`sahara.entity.instance.id`, `test.nodeid_hash`, the service name
`sahara-harness`, and the values in angle brackets. TraceQL uses the key as
sent, dots and all. LogQL uses the Loki spelling from `mapping.md`,
underscores, and the same key is a stream label only when it is in the index
list.

TraceQL goes in Explore with the Tempo data source, **TraceQL** tab, or in
`GET :3200/api/search?q=<url-encoded query>`. LogQL goes in Explore with the
Loki data source, or in `GET :3100/loki/api/v1/query_range?query=<url-encoded>`.

## TraceQL and LogQL rules that matter here

- TraceQL: `{ <conditions> }` selects spans. `resource.k`, `span.k`, `event.k`,
  `link.k`, `instrumentation.k` name the scope; `span:name`, `span:status`,
  `span:kind`, `span:duration`, `trace:rootName`, `trace:rootService`,
  `trace:id`, `span:id`, `event:name`, `link:traceID` are intrinsics with a
  colon. Strings in double quotes. `=~` and `!~` are anchored at both ends.
  `&&` and `||` inside braces; `>`, `>>`, `<`, `<<`, `~` between braces are
  parent, ancestor, child, descendant, sibling. Pipe to `count()`, `avg()`,
  `min()`, `max()`, `sum()`, `select()`, or the metrics functions `rate()`,
  `count_over_time()`, `quantile_over_time()`, `histogram_over_time()`,
  `compare()` with `by ()`.
- LogQL: `{label="value"}` is the stream selector, index labels only. Then
  `|=` `!=` `|~` `!~` on the line, `| json` or `| logfmt` to parse, and
  `| key="value"` label filters, which see structured metadata without a
  parser. Metric form wraps it: `sum by (k) (count_over_time({...}[5m]))`.

## All spans of one cycle

```
{ span.sahara.cycle.id = "<cycle id>" }
```

Only the test root spans of the cycle, the unit of work:

```
{ span.sahara.cycle.id = "<cycle id>" && span:parentID = "" }
```

UNVERIFIED: that `span:parentID = ""` matches a root; the intrinsic is
documented, the empty comparison is not. The documented alternative selects
whole traces by their root:

```
{ trace:rootService = "sahara-harness" && span.sahara.cycle.id = "<cycle id>" }
```

Tests of the cycle that failed, with how many per test name:

```
{ span.sahara.cycle.id = "<cycle id>" && span:status = error } | count() by (span:name)
```

Failed tests per minute over the cycle, a TraceQL metrics query:

```
{ span.sahara.cycle.id = "<cycle id>" && span:kind = internal && span:status = error } | rate() by (span:name)
```

The session root that a test links to, given the session's trace id:

```
{ link:traceID = "<32 hex characters>" }
```

## All operations on one entity instance

```
{ span.sahara.entity.instance.id = "<instance id>" && span:kind = client }
```

Add the cycle when instance ids repeat across cycles:

```
{ span.sahara.entity.instance.id = "<instance id>" && span.sahara.cycle.id = "<cycle id>" }
```

The tests whose entity operation on that instance failed, structural form:

```
{ trace:rootService = "sahara-harness" } >> { span.sahara.entity.instance.id = "<instance id>" && span:status = error }
```

Latency of one operation per definition, p95 over the time range:

```
{ span:name = "entity.create" } | quantile_over_time(span:duration, 0.95) by (span.sahara.entity.definition)
```

## Find one span by span id

```
{ span:id = "<16 hex characters>" }
```

The whole trace by id, no search:

```
GET :3200/api/v2/traces/<32 hex characters>
```

Add `?start=<unix seconds>&end=<unix seconds>` when the trace is old; without
them Tempo checks every block, which is slow but complete. A 404 means no
block holds it. `tempo-cli query api trace-id http://tempo:3200 <trace id>`
prints the same.

## Documents where a label has an unexpected type

Tempo keeps the type. The check is which comparison matches.

An id that someone sent as a number:

```
{ span.sahara.cycle.id > 0 }
```

A count that someone sent as a string:

```
{ span.sahara.retry.count =~ ".+" && span.sahara.retry.count != "" }
```

UNVERIFIED: that a regex comparison skips numeric values rather than
erroring; run it on one hour first. Loki stores every structured metadata
value as a string and Prometheus every label as a string, so there is no
type split in those two; a number that should have been a string simply
compares as a string.

Attributes that exceeded `distributor.max_attribute_bytes` are truncated,
not refused. Nothing marks them. Search for a value that ends early:

```
{ span.sahara.entity.instance.id =~ ".{2048,}" }
```

## Spans that can become a dependency

Link 1 and 2 of the chain in `screens.md`:

```
{ span:kind = client && span.peer.service != "" }
```

One definition only:

```
{ span:kind = client && span.peer.service = "<definition name>" }
```

Exit spans that will not draw an edge, `CLIENT` with no peer attribute:

```
{ span:kind = client && span.peer.service = nil && span.db.system = nil }
```

`= nil` matches a span that lacks the attribute and `!= nil` one that has
it. Links 3 to 5 are PromQL, in `queries-promql.md`.

## Error documents for a service

No error store. Exceptions are events on the span:

```
{ resource.service.name = "<service name>" && event:name = "exception" } | select(event.exception.type, event.exception.message)
```

Grouped, like Kibana's error groups:

```
{ resource.service.name = "<service name>" && event:name = "exception" } | count() by (event.exception.type)
```

Spans with an error status but no exception event, which the SDK's
`record_exception` would have added:

```
{ resource.service.name = "<service name>" && span:status = error } !>> { event:name = "exception" }
```

The negated structural operators are marked experimental in the reference
and can return false positives. Without them, run the two selections
separately and diff.

Errors of one cycle as log lines, when the harness also logs them:

```
{service_name="<service name>"} | sahara_cycle_id="<cycle id>" | detected_level="error"
```

## Log lines for a trace id

```
{service_name="<service name>"} | trace_id="<32 hex characters>"
```

Only the lines of one span:

```
{service_name="<service name>"} | span_id="<16 hex characters>"
```

Lines outside any span carry no `trace_id`. Find those by the correlation
keys the logging filter adds:

```
{service_name="<service name>"} | sahara_cycle_id="<cycle id>" | trace_id=""
```

UNVERIFIED: that `| trace_id=""` matches a line with no such metadata key
rather than only an empty value. Log volume per level for one cycle:

```
sum by (detected_level) (count_over_time({service_name="<service name>"} | sahara_cycle_id="<cycle id>" [5m]))
```

## Never

- Never write `{sahara_cycle_id="..."}` as a stream selector. It is
  structured metadata; the selector returns nothing. Put it after the pipe.
- Never write `span.service.name`. The service is a resource attribute.
- Never paste a query from memory. Copy it from here and rename.

## Stop and ask

- A query needs an attribute that no row of `mapping.md` produces.
- A TraceQL metrics query is wanted on Tempo 2.x and `local-blocks` is not
  in the processors list. That is a Tempo config change, not a query.
