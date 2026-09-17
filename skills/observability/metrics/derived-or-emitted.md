# Derived or emitted

**Verdict you produce:** `derived`, with the name of the Kibana screen or the
field that already shows it, or `emit`. It goes into the last column of the
*Metrics* table in `vocabulary.md`.

Some component in the path may already compute metrics from the spans it
receives. Emitting one of them again from the SDK is two copies of one fact,
with two names and two rounding rules, and the screens read only the copy the
pipeline made. Invariant 8.

## First, which component derives on this backend

This is the paradigm difference between the stacks. Answer it before the
questions below, from `backends/README.md`.

| Backend | Who derives span metrics and dependencies | On by default | Where the names live |
| --- | --- | --- | --- |
| Elastic | APM Server, from every span it receives | yes | `backends/elastic/overview.md` and the questions below |
| Grafana stack | Tempo's metrics-generator, or the collector's `spanmetrics` and `servicegraph` connectors. One of them, never both. | no, must be enabled | `backends/grafana/screens.md` and `backends/grafana/collector.md` |
| Victoria stack | only the collector's `spanmetrics` and `servicegraph` connectors writing into VictoriaMetrics; VictoriaMetrics derives nothing from traces | no, must be enabled | `backends/victoria/collector.md` |

On the Grafana and Victoria stacks, if no deriving component is enabled the
verdict for a count, a rate or a latency of a spanned thing is not `emit`. It
is **stop and ask**: enabling the connector is one config change and gives
every span its metrics, while emitting by hand gives one metric and a second
copy later. A person decides which.

## Questions, on Elastic

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
3. **Is it time spent per span type inside transactions?** That is
   **span breakdown metrics**. Data stream `metrics-apm.internal-<namespace>`,
   fields `span.self_time.count`, `span.self_time.sum.us`.
   Screen: **Time spent by span type** on the service Overview.
4. **Is it a count or a duration of any span, grouped by a span attribute
   the transaction dimensions do not carry?** For example tests per entity
   definition. Still `derived`, by query: a Lens chart on `traces-apm-*`
   aggregating `transaction.duration.us` or `span.duration.us`, split by
   `labels.<key>`. Write the query, not a metric. Per span labels are not
   dimensions of the metrics above, so this is the only place it exists.
5. **Is an OpenTelemetry Collector with the `spanmetrics` connector in the
   path?** Then it already emits `traces.span.metrics.calls` and
   `traces.span.metrics.duration` with dimensions `service.name`,
   `span.name`, `span.kind`, `status.code`. These arrive at Elastic as
   application metrics in `metrics-apm.app.<service.name>-<namespace>`, next
   to the server's own transaction metrics. Two copies exist. Nothing in the
   APM screens reads the connector's copy. Pick one: remove the connector
   from the pipeline, or accept that Lens charts on the connector's copy will
   not match the APM screens.

If none is yes: **`emit`**. Go to `metrics/instrument-type.md`.

## The observable check

Before writing `emit`, open Kibana, APM, Services, the service. If a chart on
Overview, Transactions or Dependencies already shows the number, the verdict is
`derived` and the chart's title goes in the vocabulary. If not, open Discover
on `metrics-apm.*` and search for the field named above. If the field exists
for this service, the verdict is `derived`.

## Verdict

Write into the *Metrics* table, last column:

```
| sahara.tests.duration | none | s | none | yes: Latency chart, transaction.duration.histogram |
| sahara.controller.polls | counter | {poll} | entity.definition, outcome | no |
```

## Never

- Never emit a histogram of a span's duration.
- Never emit a counter of a span's occurrences or failures.
- Never emit a metric per dependency call. `peer.service` on the `CLIENT`
  span is what draws the dependency and its charts.
- Never run the `spanmetrics` connector and the APM screens for the same
  numbers without writing which one is the source of truth in the
  vocabulary.
- Never trust derived throughput under tail based sampling in the collector.
  Elastic states: "derived throughput and count metrics are likely to be
  inaccurate". That is a sampling question, not a reason to emit.

## Stop and ask

- The span is sampled away below 100% and the count must be exact. A person
  chooses between head sampling that keeps the count and an emitted counter
  marked `duplicate` in the vocabulary. See `core/sampling-and-volume.md`.
- The backend is not Elastic APM Server and `backends/` has no file for it.
- A chart is wanted per an attribute value that is unbounded. That is a
  query with a filter, never a metric.

## Examples

| Wanted | Verdict | Where it already is |
| --- | --- | --- |
| Test duration p95 per test name | derived | Latency chart; `transaction.duration.histogram` |
| Tests per minute across the cycle | derived | Throughput chart |
| Failure rate per entity definition | derived | Dependencies, failed transaction rate per `span.destination.service.resource` |
| Time in entity operations versus test body | derived | Time spent by span type |
| Tests per entity definition | derived by query | Lens on `traces-apm-*` split by `labels.entity_definition` |
| Controller polls per second | emit | no span around a poll |
| Live entities right now | emit | a level, no span |
