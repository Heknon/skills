# Derived or emitted

**Verdict you produce:** `derived`, with the screen or the field on the
backend that already shows it, from `backends/<backend>/screens.md`, or
`emit`. It goes into the last column of the *Metrics* table in
`vocabulary.md`.

Some component in the path may already compute metrics from the spans it
receives. Emitting one of them again from the SDK is two copies of one fact,
with two names and two rounding rules, and the screens read only the copy the
pipeline made. Invariant 8.

## First, which component derives on this backend

This is the paradigm difference between the stacks. Answer it before the
questions below, from the `span metrics derived by` line of
`backends/README.md`. The full comparison, with what is on by default and
where the numbers land, is the first table of `backends/paradigms.md`; this
is the summary.

| Backend | Span metrics derived by |
| --- | --- |
| Elastic | APM Server, from every span it receives, always on |
| Grafana stack | Tempo metrics-generator, or the collector's `span_metrics` and `service_graph` connectors; one of them is enabled, never both |
| Victoria stack | collector connectors only, `span_metrics` and `service_graph` writing into VictoriaMetrics; nothing derives by default |

When the line says `nothing`, the verdict for a count, a rate or a latency of
a spanned thing is not `emit`. It is **stop and ask**: enabling the connector
is one config change and gives every span its metrics, while emitting by hand
gives one metric and a second copy later. A person decides which.

## On Elastic

Answer in order. The first yes is `derived`.

1. **Is the thing a root span of this service, a transaction?** Its count,
   its latency distribution and its failure rate are **transaction metrics**.
   Data streams `metrics-apm.transaction.<metricset.interval>-<namespace>`
   and `metrics-apm.service_transaction.<metricset.interval>-<namespace>`,
   intervals `1m`, `10m`, `60m`. Fields `transaction.duration.histogram`,
   `transaction.duration.summary`, `event.success_count`. Dimensions include
   `service.name`, `service.environment`, `transaction.name`,
   `transaction.type`, `transaction.result`, `event.outcome`.
   Screens: APM, Services, the service, Overview: **Latency**, **Throughput**,
   **Failed transaction rate**, the **Transactions** table.
2. **Is the thing a `CLIENT` or `PRODUCER` span with a destination
   attribute?** Its latency, throughput and error rate per destination are
   **service destination metrics**. Data stream
   `metrics-apm.service_destination.<metricset.interval>-<namespace>`. Fields
   `span.destination.service.response_time.count`,
   `span.destination.service.response_time.sum.us`. Dimensions include
   `span.destination.service.resource`, `service.target.type`,
   `service.target.name`, `event.outcome`.
   Screens: APM, **Dependencies**, and the **Dependencies** table on the
   service Overview with latency, throughput, failed transaction rate and
   impact.
3. **Is it time spent per span type inside transactions?** That would be
   **span breakdown metrics**, data stream `metrics-apm.internal-<namespace>`,
   fields `span.self_time.count`, `span.self_time.sum.us`, screen **Time
   spent by span type**. They are **not derived for OTLP data in 8.x**: the
   chart is blank for OpenTelemetry data, a listed limitation
   (`backends/elastic/screens.md`, service overview row). The answer here is
   no; go to question 4 and write a query.
4. **Is it a count or a duration of any span, grouped by a span attribute
   the transaction dimensions do not carry?** For example tests per entity
   definition, or time in entity operations against the test body. Still
   `derived`, by query: a Lens chart on `traces-apm-*` aggregating
   `transaction.duration.us` or `span.duration.us`, split by `labels.<key>`.
   Write the query, not a metric. Per span labels are not dimensions of the
   metrics above, so this is the only place it exists.
5. **Is an OpenTelemetry Collector with the `span_metrics` connector in the
   path?** Then it already emits `traces.span.metrics.calls` and
   `traces.span.metrics.duration` with dimensions `service.name`,
   `span.name`, `span.kind`, `status.code`. These arrive at Elastic as
   application metrics in `metrics-apm.app.<service.name>-<namespace>`, next
   to the server's own transaction metrics. Two copies exist. Nothing in the
   APM screens reads the connector's copy. Pick one: remove the connector
   from the pipeline, or accept that Lens charts on the connector's copy will
   not match the APM screens.

If none is yes: **`emit`**. Go to `metrics/instrument-type.md`.

### The observable check

Before writing `emit`, open Kibana, APM, Services, the service. If a chart on
Overview, Transactions or Dependencies already shows the number, the verdict is
`derived` and the chart's title goes in the vocabulary. If not, open Discover
on `metrics-apm.*` and search for the field named above. If the field exists
for this service, the verdict is `derived`.

## Other backends

Other backends: the verdicts do not change; the stored shape is in
backends/<backend>/mapping.md and the differences in backends/paradigms.md.

## Verdict

Write into the *Metrics* table, last column:

```
| sahara.tests.duration | none | s | (none) | yes, derived: see backends/<backend>/screens.md |
| sahara.controller.polls | counter | {poll} | sahara.entity.definition, outcome | no |
```

## Never

- Never emit a histogram of a span's duration.
- Never emit a counter of a span's occurrences or failures.
- Never emit a metric per dependency call. `peer.service` on the `CLIENT`
  span is what draws the dependency and its charts.
- Never run the `span_metrics` connector and a backend that derives the same
  numbers itself without writing which one is the source of truth in the
  vocabulary.
- Never trust derived throughput under tail based sampling in the collector.
  Elastic states: "derived throughput and count metrics are likely to be
  inaccurate", and every deriving component sees only the spans that reach
  it. That is a sampling question, not a reason to emit.

## Stop and ask

- The span is sampled away below 100% and the count must be exact. A person
  chooses between head sampling that keeps the count and an emitted counter
  marked `duplicate` in the vocabulary. See `core/sampling-and-volume.md`.
- The backend is none of the three in `backends/`.
- The `span metrics derived by` line of `backends/README.md` says `nothing`
  and the thing has a span.
- A chart is wanted per an attribute value that is unbounded. That is a
  query with a filter, never a metric.

## Examples

Screen names are Elastic's; the same verdicts on the other stacks are in
`backends/<backend>/screens.md`.

| Wanted | Verdict | Where it already is |
| --- | --- | --- |
| Test duration p95 per test name, `sahara.tests.duration` | derived | Latency chart; `transaction.duration.histogram` |
| Tests per minute across the cycle | derived | Throughput chart |
| Failure rate per entity definition | derived | Dependencies, failed transaction rate per `span.destination.service.resource` |
| Time in entity operations versus test body | derived by query | Time spent by span type is blank for OTLP in 8.x; Lens on `traces-apm-*` by `span.type` and `labels.sahara_entity_operation` |
| Tests per entity definition | derived by query | Lens on `traces-apm-*` split by `labels.sahara_entity_definition` |
| Controller polls per second, `sahara.controller.polls` | emit | no span around a poll |
| Live entities right now, `sahara.entities.live` | emit | a level, no span |
