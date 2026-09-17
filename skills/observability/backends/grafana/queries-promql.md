# PromQL to paste

Stamp: Prometheus 3.14 querying API and functions reference, Tempo 3.0
metrics-generator pages, Grafana Tempo data source source
`src/graphTransform.ts` at main, read 2026-09-17.

Rename before pasting: `sahara-harness`, `sahara_entity_definition`, and the
values in angle brackets. Series names below are the Tempo metrics-generator's.
When the collector's connectors produce them, swap `traces_spanmetrics_calls_total`
for `traces_span_metrics_calls_total`, `traces_spanmetrics_latency_bucket` for
`traces_span_metrics_duration_milliseconds_bucket`, and the label `service`
for `service_name`. Paste into Explore with the Prometheus data source, or
`GET :9090/api/v1/query?query=<url-encoded>`; on Mimir
`GET :8080/prometheus/api/v1/query` with `X-Scope-OrgID`.

## RED per service

Throughput, spans per second, for the unit of work's kind:

```
sum by (service) (rate(traces_spanmetrics_calls_total{span_kind="SPAN_KIND_INTERNAL"}[5m]))
```

Failure rate, 0 to 1:

```
sum by (service) (rate(traces_spanmetrics_calls_total{status_code="STATUS_CODE_ERROR"}[5m]))
/
sum by (service) (rate(traces_spanmetrics_calls_total[5m]))
```

Spans with status `UNSET` count in the denominator only, which is why status
must never be left `UNSET`. Latency p95 in seconds:

```
histogram_quantile(0.95, sum by (service, le) (rate(traces_spanmetrics_latency_bucket[5m])))
```

Per test name, the Transactions table:

```
topk(20, sum by (span_name) (rate(traces_spanmetrics_calls_total{service="sahara-harness", span_kind="SPAN_KIND_INTERNAL"}[5m])))
```

## Latency percentiles of one span name grouped by a label

Only after `sahara.entity.definition` is in the generator's `dimensions`:

```
histogram_quantile(0.95, sum by (sahara_entity_definition, le) (rate(traces_spanmetrics_latency_bucket{span_name="entity.create"}[5m])))
```

Not there yet: the TraceQL metrics form in `queries.md` answers the same
question at read time with no series.

## Dependencies, RED per peer

Link 5 of the chain in `screens.md`. Calls per second from the harness to each
peer:

```
sum by (server, connection_type) (rate(traces_service_graph_request_total{client="sahara-harness"}[5m]))
```

Failed share per peer:

```
sum by (server) (rate(traces_service_graph_request_failed_total{client="sahara-harness"}[5m]))
/
sum by (server) (rate(traces_service_graph_request_total{client="sahara-harness"}[5m]))
```

Client-side p95 per peer:

```
histogram_quantile(0.95, sum by (server, le) (rate(traces_service_graph_request_client_seconds_bucket{client="sahara-harness"}[5m])))
```

Spans the generator could not pair, which never became an edge:

```
sum by (client, server) (rate(traces_service_graph_unpaired_spans_total[5m]))
```

Is the producer alive at all:

```
count({__name__=~"traces_service_graph_request_total|traces_span_metrics_calls_total|traces_spanmetrics_calls_total"}) by (__name__)
```

Two names present means two producers are on. Turn one off.

## Metrics you emitted

A counter with unit `{poll}` and a histogram with unit `s`:

```
sum by (sahara_entity_definition) (rate(sahara_controller_polls_total[5m]))
histogram_quantile(0.95, sum by (sahara_entity_definition, le) (rate(sahara_controller_poll_duration_seconds_bucket[5m])))
```

Resource attributes are on `target_info`, not on the series. Join by `job`
and `instance`:

```
sum by (deployment_environment) (rate(sahara_controller_polls_total[5m]) * on (job, instance) group_left (deployment_environment) target_info)
```

## Documents where a label has an unexpected type

Prometheus has no types on labels; the split shows up as two metric names.
A metric emitted with unit `s` in one process and `ms` in another:

```
count by (__name__) ({__name__=~"sahara_controller_poll_duration.*"})
```

Two names means two units. Fix the vocabulary. A label emitted as `1` in
one place and `"1"` in another is one label; nothing to find.

## Cardinality, before it hurts

Series per metric name, top offenders:

```
topk(20, count by (__name__) ({__name__=~".+"}))
```

Distinct values of one label on one metric:

```
count(count by (sahara_entity_definition) (traces_spanmetrics_calls_total))
```

Series a `dimensions` entry would add, run before adding it: the same query
with the candidate key over TraceQL, `{ span:name = "entity.create" } | count() by (span.<candidate key>)`,
and multiply the number of groups by the current series count of the metric.

Tempo's own view: `tempo_metrics_generator_registry_active_series` and, when
the limit bites, `tempo_metrics_generator_registry_series_limited_total`.
Dry run: set the override `metrics_generator.disable_collection: true` and
watch `tempo_metrics_generator_registry_active_series` before writing
anything to Prometheus.

The server's own tally, no PromQL:

```
GET :9090/api/v1/status/tsdb?limit=20
```

Fields `headStats.numSeries`, `seriesCountByMetricName`,
`labelValueCountByLabelName`, `seriesCountByLabelValuePair`. Mimir:
`GET :8080/prometheus/api/v1/cardinality/label_names`,
`.../cardinality/label_values`, `.../cardinality/active_series`.

## Exemplars

```
GET :9090/api/v1/query_exemplars?query=traces_spanmetrics_latency_bucket{service="sahara-harness"}&start=<rfc3339>&end=<rfc3339>
```

Each hit has `exemplars[].labels.trace_id`. In a panel, the Exemplars toggle
draws them and `exemplarTraceIdDestinations` makes them links. Needs
`--enable-feature=exemplar-storage` and, for the generator's series,
`send_exemplars: true` on its `remote_write` entry.

## Never

- Never `rate()` after `sum()`. Aggregate the rate, not the counter.
- Never compare a generator series with a connector series on one panel.
- Never add a `dimensions` key without the count query above.

## Stop and ask

- `count by (__name__)` shows both spellings of a metric and neither producer
  can be turned off today.
