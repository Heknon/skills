# Kibana APM screens: what each one reads

verified against: Elastic Observability guide 8.17 pages Services, Service
overview, Transactions, Dependencies, Service map, Errors, Metrics, Logs,
Traces, Correlations, Transaction sampling; Kibana 8.17 APM settings and
advanced settings; Kibana guide Dependencies pages 8.1 to 8.9; APM data model
Metrics page. Rows marked UNVERIFIED name the part that no page states.

Read this before a Query task. Column "empty when" lists the conditions that
make the screen blank or wrong. Every one of them has a row in
`apm-server-mapping.md`.

## Index patterns behind every screen

The APM app reads the patterns in Kibana's APM settings, defaults:
transactions and spans `traces-apm*,apm-*,traces-*.otel-*`, errors
`logs-apm*,apm-*,traces-*.otel-*`, metrics `metrics-apm*,apm-*,metrics-*.otel-*`.
The environment selector filters every screen on `service.environment`.
`observability:apmDefaultServiceEnvironment` sets the default.
`observability:apmEnableServiceMetrics` makes the app use the low-cardinality
`service_transaction` metrics. `observability:apmEnableContinuousRollups`
makes it pick the `1m`, `10m` or `60m` interval by time range.
`observability:enableInspectEsQueries` shows the exact query behind a panel.
Turn it on when a screen is empty and you do not know why.

## The screens

| Screen or panel | Aggregates | Reads | Needs these fields | Produced by these OTLP facts | Empty or wrong when |
| --- | --- | --- | --- | --- | --- |
| Services list | one row per service: latency, throughput, failed transaction rate, health, alerts | `metrics-apm.service_transaction.*` and `metrics-apm.service_summary.*`, falling back to `traces-apm-*` transactions | `service.name`, `service.environment`, `transaction.type`, `transaction.duration.histogram`, `event.outcome`, `agent.name` | resource `service.name`, `deployment.environment`; a root span or `SERVER`/`CONSUMER` span per unit of work | no transaction was ever produced, only spans; wrong environment selected; the service produced only metrics or logs |
| Service overview | latency, throughput, failed rate charts; transactions, errors, dependencies, instances tables | as above, plus `service_destination` metrics for the dependencies table, `logs-apm.error-*` for the errors table | as above, plus `span.destination.service.resource`, `error.grouping_key`, `service.node.name` | as above; `peer.service` or `db.system` on exit spans; `exception` span events; resource `service.instance.id` for instances | Time spent by span type is blank for OpenTelemetry data in 8.x, a listed limitation |
| Transactions tab | transaction groups by `transaction.name` within one `transaction.type`; latency avg, p95, p99; throughput; failed rate; sorted by impact | `metrics-apm.transaction.*`, falling back to `traces-apm-*` `processor.event: transaction` | `transaction.name`, `transaction.type`, `transaction.duration.us` or `.histogram`, `event.outcome` | span name of the root span; `transaction.type` is `unknown` for a test root, so select `unknown` | the type selector is on `request` while the data is `unknown`; a name with unbounded cardinality overflows into `transaction.name: _other` |
| Transaction detail: latency distribution | histogram of `transaction.duration.us` for one group | `traces-apm-*` transactions | `transaction.duration.us`, `transaction.name` | one document per unit of work | fewer transactions than buckets; nothing to plot for a once-per-run session |
| Transaction detail: trace samples and waterfall | up to 500 sampled traces for the selected buckets; the waterfall of one `trace.id` | `traces-apm-*` transactions and spans | `trace.id`, `parent.id`, `transaction.id`, `span.id`, `span.name`, `span.type`, `span.subtype`, `span.duration.us`, `span.links` | parent context propagated by the SDK; links for the session root | a child span with a `parent.id` no document has, from a broken propagation; more than `xpack.apm.ui.maxTraceItems` children, default 5000 |
| Transaction detail: metadata tab | flat list of the document's fields | the one transaction document | `labels.*`, `numeric_labels.*`, `http.*`, `url.*`, `host.*`, `service.*`, `user.*` | every attribute that became a label | a label with a dot in the query; a dropped map attribute |
| Transaction detail: correlations | latency correlations, coefficient 0 to 1; failed transaction correlations, impact high, medium, low, on `event.outcome: failure` vs `success` | `traces-apm-*` transactions | `event.outcome`, `transaction.duration.us`, the candidate fields | span status set to `OK` or `ERROR`; labels with bounded values | outcome `unknown` everywhere because status was left `UNSET`. UNVERIFIED: the exact candidate field list; the guide says attributes and shows labels in examples |
| Dependencies tab, and the top-level Dependencies page | one row per `span.destination.service.resource`: latency, throughput, failed rate, impact | `metrics-apm.service_destination.*` | `span.destination.service.resource`, `service.target.type`, `service.target.name`, `span.destination.service.response_time.count`, `span.destination.service.response_time.sum.us`, `event.outcome`, `service.name` | the full chain in the next section | anything in the chain missing |
| Dependency detail: overview | the same three charts for one resource, with a trace sample timeline | `service_destination` metrics, then `traces-apm-*` spans for samples | as above plus `span.id`, `trace.id` | as above | no sampled span exists for the resource in the time range |
| Dependency detail: Operations tab | one row per `span.name` under the resource; beta | `service_destination` metrics, dimension `span.name` | `span.name` | a bounded span name per operation such as `entity.create` | `span.name` carries an id, one row per instance. Present in the Kibana 8.9 guide page, absent from the 8.8 page: treat 8.9 as the first minor |
| Dependency detail: Upstream services | one row per `service.name` that calls the resource | `service_destination` metrics, dimension `service.name` | `service.name`, `span.destination.service.resource` | as above | never empty when the overview has data |
| Service map | circles per instrumented service, diamonds per `span.type`/`span.subtype` of exit spans, edges from distributed traces | `traces-apm-*` sampled traces | `span.destination.service.resource`, `span.type`, `span.subtype`, `trace.id`, `parent.id` | exit spans with a destination; `traceparent` propagated between services | a service that is not instrumented or receives no `traceparent` has no edge; a `peer.service`-only span draws a diamond of type `unknown` |
| Errors tab | error groups by `error.grouping_key`, occurrences over time, culprit, message, first and last seen | `logs-apm.error-*` | `error.grouping_key`, `error.grouping_name`, `error.exception.type`, `error.exception.message`, `error.culprit`, `service.name`, `trace.id` | `record_exception` on the span, which emits an `exception` span event with `exception.type` and `exception.message` | the exception was only set in the status description; the event carries neither `exception.type` nor `exception.message` |
| Metrics tab | agent runtime metrics: CPU, memory, and per-language panels | `metrics-apm.app.<service.name>-*` and `metrics-apm.internal-*` | `system.cpu.total.norm.pct`, `system.memory.actual.free`, and the runtime fields the agent emits | UNVERIFIED: which OTLP metric names the 8.17 panels accept. The guide lists Java agent panels only | the OpenTelemetry SDK emits no runtime metrics by itself. Expect this tab blank |
| Logs tab | log lines for the service | `logs-*` filtered on `service.name` | `service.name`, `@timestamp`, `message`, `log.level`, `trace.id` | resource `service.name` on the log exporter; `trace.id` injected into records | logs shipped by a different pipeline with a different `service.name` spelling |
| Traces page | root transactions grouped by name, sorted by impact | `traces-apm-*` transactions with `parent.id` absent | `transaction.name`, `transaction.duration.us`, `event.outcome` | root spans | a search on a field only child transactions carry: the page says only root transaction properties are searchable |
| Trace explorer | KQL or EQL over traces; results are the matching root transactions | `traces-apm-*` | any indexed field on the trace | enable `observability:apmTraceExplorerTab` | the setting is off; the query uses a dotted label key |

## The Dependencies chain, spelled out

Every link must hold or the row is missing. Check them in this order.

1. The span is an exit span: `SpanKind.CLIENT` or `SpanKind.PRODUCER`, and
   it has a parent. A root `CLIENT` span becomes a transaction and is never a
   dependency.
2. The span carries a destination attribute. `peer.service` is the direct
   route: it becomes `span.destination.service.resource` verbatim. Otherwise
   `db.system`, `messaging.system`, `rpc.system` or HTTP attributes derive
   one. An `INTERNAL` span with no such attribute has no resource.
3. APM Server writes the span document with
   `span.destination.service.resource` set. Confirm with the query "spans with
   a destination" in `queries.md`.
4. APM Server's aggregation adds the span to a `service_destination` bucket
   keyed by `service.name`, `service.environment`, resource, target type and
   name, `span.name` and `event.outcome`, for `1m`, `10m` and `60m`. The
   documents appear in `metrics-apm.service_destination.1m-<namespace>`
   within about one interval.
5. The Dependencies table is a `terms` aggregation over those metrics on
   `span.destination.service.resource`. Latency is `sum.us / count`,
   throughput is `count / minutes`, failed rate is the `event.outcome:
   failure` share.

What breaks it:

- `SpanKind.INTERNAL` on the operation span with only `peer.service`.
  UNVERIFIED: the source keys the resource on attributes, not on kind, so
  the row may still appear with `span.type: unknown`. Do not depend on it.
- No destination attribute at all. `span.type` becomes `app` or `unknown`
  and there is no resource.
- Head-based sampling drops the whole trace at the SDK, so the span never
  arrives. The metric is scaled by `transaction.representative_count` only
  when the sampler writes `ot=p:<n>` into `tracestate`. A plain ratio
  sampler does not, so throughput reads low by the sample rate.
- Span compression. Only Elastic APM agents compress; the OpenTelemetry SDK
  does not, so this cannot happen on this path. If an Elastic agent is in
  play, a composite span carries `span.composite.count` and the individual
  spans are gone from the waterfall. UNVERIFIED: whether the aggregation
  multiplies by `span.composite.count`.
- A resource with unbounded cardinality, such as an instance id in
  `peer.service`, gives one row per instance and overflows the aggregation.
  The definition name goes in `peer.service`; the instance id is a label.
- The wrong environment selected, or `service.environment` unset on the
  caller while the selector is not "All".

## Never

- Never judge from the Services list that spans are missing. It reads
  transactions and metrics only.
- Never expect a span event on the waterfall. It is a log document.
- Never search the Traces page for a child-only field.

## Stop and ask

- The Dependencies row is present but Operations is empty and the version is
  below 8.9.
- A screen is empty and `observability:enableInspectEsQueries` shows a query
  over an index pattern that does not match this installation's namespace.
