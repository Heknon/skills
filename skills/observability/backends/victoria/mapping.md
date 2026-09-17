# Victoria stack: OTLP to stored field map

Stamp: VictoriaMetrics v1.152.0, VictoriaLogs v1.52.0, VictoriaTraces
v0.11.1, read 2026-09-17. Rows marked `source:` come from the repositories
at master: `lib/protoparser/opentelemetry/pb/pb.go` in VictoriaMetrics,
`app/vlinsert/opentelemetry/opentelemetry.go` and
`lib/protoparser/opentelemetry/pb/pb.go` in VictoriaLogs,
`app/vtinsert/opentelemetry/opentelemetry.go` and
`lib/protoparser/opentelemetry/pb/trace_fields.go` in VictoriaTraces.

The rule in one line: **nothing is renamed unless a flag says so**. Logs
and spans keep every attribute key as it was sent, dots included, under a
signal-specific prefix. Metrics keep dots too, until you turn on
`-opentelemetry.usePrometheusNaming`, after which the OTLP to Prometheus
rules apply. Every value becomes a string, except a metric sample.

## The spelling of one key on each signal

| Key as sent | Metric label, default | Metric label, `-opentelemetry.usePrometheusNaming` | Log field | Span field, when a span attribute | Span field, when a resource attribute |
| --- | --- | --- | --- | --- | --- |
| `sahara.cycle.id` | `sahara.cycle.id` | `sahara_cycle_id` | `sahara.cycle.id` | `span_attr:sahara.cycle.id` | `resource_attr:sahara.cycle.id` |
| `sahara.entity.definition` | `sahara.entity.definition` | `sahara_entity_definition` | `sahara.entity.definition` | `span_attr:sahara.entity.definition` | `resource_attr:sahara.entity.definition` |
| `test.nodeid_hash` | `test.nodeid_hash` | `test_nodeid_hash` | `test.nodeid_hash` | `span_attr:test.nodeid_hash` | `resource_attr:test.nodeid_hash` |
| `service.name` | `service.name` | `service_name` | `service.name`, a stream field by default | `span_attr:service.name`, do not do this | `resource_attr:service.name`, always a stream field |
| `deployment.environment` | `deployment.environment` | `deployment_environment` | `deployment.environment`, a stream field by default | | `resource_attr:deployment.environment` |

A run id must never be a metric label. The first two columns exist so that a
mistake can be recognised in the cardinality explorer, not so it can be made.

## Metrics: VictoriaMetrics and vmagent

Endpoint `/opentelemetry/v1/metrics`, protobuf, optional
`Content-Encoding: gzip`. `/opentelemetry/api/v1/push` also exists but the
changelog calls it "the OpenTelemetry Firehose ingestion endpoint"; do not
send SDK or collector traffic there. The flags below "can be applied on
vmagent, vminsert or VictoriaMetrics single-node".

| OTLP | Stored as | Rule |
| --- | --- | --- |
| metric name, default | the name unchanged | "stores the ingested OpenTelemetry metric points as is without any transformations" |
| metric name, `-opentelemetry.usePrometheusNaming` | OTLP to Prometheus spelling | dots and other disallowed characters become `_`, the UCUM unit becomes a suffix, a monotonic sum gets `_total` unless the name already ends in `_total`. Doc example: `process.cpu.time` with unit `s` becomes `process_cpu_time_seconds_total` |
| metric name, `-opentelemetry.convertMetricNamesToPrometheus` | name converted, labels untouched | doc example `process_cpu_time_seconds_total{service.name="foo"}` |
| any name or label, `-usePromCompatibleNaming` | unsupported characters become `_` | applies to every ingestion protocol, adds no unit and no `_total`. Example `foo.bar{a.b='c'}` becomes `foo_bar{a_b='c'}` |
| data point attribute key | a label with the same key | dots kept by default; with `usePrometheusNaming` dots become `_`, and a key starting with `_` gets `key` prepended when `-opentelemetry.labelNameUnderscoreSanitization` is on |
| data point attribute value | the label value as a string | UNVERIFIED: how bool, int and array values are printed |
| resource attributes | one label per attribute on every point of that resource | default, `-opentelemetry.promoteAllResourceAttributes=true`. Narrow with `-opentelemetry.promoteResourceAttributes=service.name,deployment.environment` or drop some with `-opentelemetry.ignoreResourceAttributes`. There is no `target_info`, no `job`, no `instance`. UNVERIFIED: which value wins when a resource attribute and a data point attribute share a key |
| instrumentation scope | labels `scope.name`, `scope.version`, `scope.attributes.<key>` on every point | source; on by default, off with `-opentelemetry.promoteScopeMetadata=false`. UNVERIFIED: the spelling after `usePrometheusNaming` |
| Sum, cumulative | one series, raw values | the normal counter |
| Sum or Histogram, delta | stored as is from v1.132.0 | query with `sum_over_time()` and `rate_over_sum()`, never `rate()`. The doc says do not apply deduplication or downsampling to delta series. The doc's recommendation is the collector's delta to cumulative processor; see `collector.md` |
| Gauge | one series | |
| Histogram, explicit buckets | `<name>_bucket{le="..."}`, `<name>_sum`, `<name>_count` | source; cumulative bucket counts like Prometheus |
| ExponentialHistogram | `<name>_bucket{vmrange="<lower>...<upper>"}`, `<name>_sum`, `<name>_count` | doc: "automatically converted to VictoriaMetrics histogram format with `vmrange` labels" |
| Summary | `<name>_count`, `<name>_sum` and the quantile series | source |
| Exemplars | dropped | source: the decoder has no exemplar handling. UNVERIFIED: no doc page states it. Consequence: no metric to trace click-through, see `screens.md` |
| metric metadata | stored | vmagent accepts metadata since v1.137.0 |

Type rule: a label value is always a string. A number sent as an attribute
does not create a second field as on Elastic; it creates a **new series**
per distinct value. A key sent as `"1"` once and `1` later is the same
label value. The vocabulary still fixes the type because the collector and
Grafana compare strings.

Character rule without the naming flag: any UTF-8 key is accepted and
stored, and `/api/v1/label/<name>/values` decodes UTF-8 label names per the
Prometheus API. UNVERIFIED: the MetricsQL selector syntax for a dotted label
name, such as `{"service.name"="x"}`. Turn on
`-opentelemetry.usePrometheusNaming` and the question never arises; every
query in `queries.md` assumes it is on.

## Logs: VictoriaLogs

Endpoint `/insert/opentelemetry/v1/logs`, protobuf only, port `9428`.

| OTLP log record | VictoriaLogs field | Rule |
| --- | --- | --- |
| `Body`, string | `_msg` | source: the body is decoded under the message field. If it is empty, `_msg` becomes the `-defaultMsgValue` flag value, default `missing _msg field; see https://docs.victoriametrics.com/victorialogs/keyconcepts/#message-field` |
| `Body`, map | one field per key, nested keys joined with `.` | flattening rule of the data model; keep a value whole with `VL-Preserve-JSON-Keys` |
| `TimeUnixNano`, else `ObservedTimeUnixNano`, else arrival time | `_time` | source |
| `SeverityNumber` | `severity_number`, a string such as `"9"` | source; renamed from a custom `severity` field in v1.50.0 |
| `SeverityText` | `severity_text`; when empty, filled from the number as `Info`, `Warn`, `Error`, `Debug`, `Trace`, `Fatal`, with `2` to `4` suffixes for the finer levels | source |
| `TraceId`, `SpanId` | `trace_id`, `span_id`, lowercase hex | source; "properly parse `trace_id` and `span_id` log fields as hex numbers" |
| `EventName` | `event_name`, added to the stream fields | source and changelog |
| resource attributes | fields with the attribute key, dots kept, **all of them stream fields by default** | doc: "treats all the resource labels as log stream fields". Override with the `VL-Stream-Fields` header or `_stream_fields` query arg, comma separated |
| scope | `scope.name`, `scope.version`, `scope.attributes.<key>` | source and changelog |
| log record attributes | fields with the attribute key, dots kept | nested maps flatten with `.`; arrays, numbers and booleans become strings |
| any empty value | the field is absent | "Empty values are treated the same as missing values" |

Stream rule: a stream is the set of fields named by `VL-Stream-Fields`. The
default takes **every** resource attribute, so `process.pid`,
`service.instance.id` or `host.name` on the resource means one stream per
process per host. The docs say never associate high-cardinality fields with
streams; `vl_streams_created_total` growing fast is the symptom and
`-logNewStreams` prints each new one. Set the header in the exporter and
in the SDK to the bounded resource keys, for example
`VL-Stream-Fields: service.name,deployment.environment`.

Limits: `-insert.maxFieldsPerLine` default `1000` fields per entry;
`-insert.maxLineSizeBytes` default `262144`, and entries above 2 MB are
ignored regardless; `-opentelemetry.maxRequestSize` default `67108864`
bytes per request. Field names have a hardcoded maximum length and longer
ones make the entry ignored; the FAQ does not print the number.

## Traces: VictoriaTraces

Endpoint `/insert/opentelemetry/v1/traces`, protobuf, port `10428`;
OTLP/gRPC on `-otlpGRPCListenAddr=:4317`, TLS on by default, off with
`-otlpGRPC.tls=false`. Every span **must** carry `service.name` in its
resource and a span `name`; they are the two stream fields.

| OTLP span | VictoriaTraces field | Rule |
| --- | --- | --- |
| `EndTimeUnixNano` | `_time` | doc |
| `TraceId`, `SpanId`, `ParentSpanId` | `trace_id`, `span_id`, `parent_span_id`, lowercase hex | source; a root span has an empty `parent_span_id`, which VictoriaLogs stores as absent |
| `Name` | `name`, stream field | |
| `Kind` | `kind`, the OTLP enum number as a string: `1` INTERNAL, `2` SERVER, `3` CLIENT, `4` PRODUCER, `5` CONSUMER, `0` UNSPECIFIED | source; the number is from the OTLP proto |
| `StartTimeUnixNano`, `EndTimeUnixNano` | `start_time_unix_nano`, `end_time_unix_nano` | |
| end minus start | `duration`, nanoseconds | doc: computed at ingestion, "not part of OTLP" |
| `Status.Code`, `Status.Message` | `status_code` as `0` UNSET, `1` OK, `2` ERROR; `status_message` | source |
| `TraceState`, `Flags` | `trace_state`, `flags` | source |
| resource attributes | `resource_attr:<key>`; `resource_attr:service.name` is a stream field | doc |
| scope | `scope_name`, `scope_version`, `scope_attr:<key>` | doc and source |
| span attributes | `span_attr:<key>` | doc |
| attribute value types | strings; an array or map value becomes its JSON text, a nested map flattens to `key.subkey` | doc example `resource_attr:process.command_args` holds a JSON array; source flattens `KeyValueList` with `.` |
| empty attribute value | `-` | doc: "Empty attribute values in trace spans are replaced with `-`" |
| event `<index>` | `event:event_name:<index>`, `event:event_time_unix_nano:<index>`, `event:event_dropped_attributes_count:<index>`, `event:event_attr:<key>:<index>` | source; index starts at `0` |
| link `<index>` | `link:link_trace_id:<index>`, `link:link_span_id:<index>`, `link:link_trace_state:<index>`, `link:link_flags:<index>`, `link:link_attr:<key>:<index>` | source |
| dropped counts | `dropped_attributes_count`, `dropped_events_count`, `dropped_links_count` | |
| `_msg` | `-` | source; VictoriaLogs requires a message |

Exception rule: `record_exception` writes an event named `exception`, so it
lands as `event:event_name:0` equal to `exception`,
`event:event_attr:exception.type:0`, `event:event_attr:exception.message:0`,
`event:event_attr:exception.stacktrace:0`. There is no error document and no
grouping key. UNVERIFIED: whether the Jaeger API returns events as span
`logs` and links as `references`, and therefore whether Grafana shows them
on the span.

Jaeger `tags` filter spelling: a span attribute is `key=value`, a resource
attribute is `resource_attr:key=value`, a scope attribute
`scope_attr:key=value`, regex with `key=~re`. Example from the docs:
`span.kind=client resource_attr:os.type=linux`.

## Never

- Never put an unbounded value in a metric label. Each distinct value is a
  series forever, and `-storage.maxHourlySeries` drops the excess silently
  except for a sampled `WARNING` line.
- Never leave `VL-Stream-Fields` unset when the resource carries a per
  process or per host key.
- Never write a query with `service.name` after choosing
  `usePrometheusNaming`. The label is `service_name`.
- Never omit `service.name` from a span's resource. VictoriaTraces needs it
  for the stream.

## Stop and ask

- Someone wants dots kept in metric labels and Grafana queries that Grafana
  ships. Its Tempo views query `traces_service_graph_request_total` and
  friends with underscores; see `screens.md`.
- A field is needed that no row above produces.
