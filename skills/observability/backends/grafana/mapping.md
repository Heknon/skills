# OTLP to stored field map: Tempo, Loki, Prometheus

Stamp: Tempo 3.0 docs and v2.8.x docs, Loki 3.7 docs and `docs/sources/shared/otel.md`
at main, Prometheus 3.14 configuration reference and the OpenTelemetry
Prometheus compatibility specification, Mimir 3.2 docs, grafana/tempo source
at main for label values, read 2026-09-17.

The rule in one line per store. **Tempo** stores every key as sent, dots
included, and you name the scope when you query. **Loki** turns dots into
underscores everywhere, indexes a fixed short list of resource attributes as
labels and keeps the rest as structured metadata. **Prometheus** turns dots
into underscores, appends a unit suffix and `_total`, and moves resource
attributes into `target_info`.

## Tempo: spans

| OTLP | Stored as | Queried as | Note |
| --- | --- | --- | --- |
| span name | intrinsic | `span:name`, legacy `name` | unchanged |
| span kind | intrinsic | `span:kind` = `server`, `client`, `producer`, `consumer`, `internal`, `unspecified` | lower case in TraceQL |
| status code | intrinsic | `span:status` = `ok`, `error`, `unset` | |
| status message | intrinsic | `span:statusMessage` | |
| duration | intrinsic | `span:duration`, units `ns us ms s m h` | `{ span:duration > 500ms }` |
| span id, parent id | intrinsic | `span:id`, `span:parentID` | root span: empty parent |
| trace id | intrinsic | `trace:id` | 32 lower case hex |
| whole trace | intrinsics | `trace:duration`, `trace:rootName`, `trace:rootService` | root span's name and `service.name` |
| span attribute `k` | attribute, typed | `span.k` | dots kept: `span.sahara.cycle.id` |
| resource attribute `k` | attribute, typed | `resource.k` | `resource.service.name` |
| scope name, version | intrinsic | `instrumentation:name`, `instrumentation:version` | |
| scope attribute `k` | attribute | `instrumentation.k` | |
| span event | event | `event:name`, `event:timeSinceStart`, `event.k` for its attributes | one span may match on any of its events |
| span link | link | `link:traceID`, `link:spanID`, `link.k` for its attributes | the session root is found from a test span by `link:traceID` |
| exception | an event named `exception` | `{ event:name = "exception" && event.exception.type = "..." }` | no error store; this is the only place it lives |
| unscoped `.k` | attribute in either scope | `.k` | slower, ambiguous when both scopes carry the key |

Key spelling: a key with characters outside letters, digits, `.` and `_` is
quoted, `span."attribute name with space"`. Mixed form is allowed,
`span.attribute."sub.name"`. `sahara.cycle.id` needs no quotes.

Value types survive: string, int, float, bool. TraceQL compares each with its
own operators, so `span.sahara.retry.count > 2` works only when the value was
sent as a number, and `span.sahara.retry.count = "3"` matches only the string.
Invariant 7 holds here too. UNVERIFIED: how array-valued attributes are
matched in TraceQL.

Limits: `distributor.max_attribute_bytes`, default `2048`, truncates any
longer attribute value. `overrides.defaults.global.max_bytes_per_trace` refuses
a trace past that size with the reason `TRACE_TOO_LARGE` in
`tempo_discarded_spans_total`. Spans arriving after the trace was already cut
from the live path are refused too; see `verification-ladder.md`.

Domain spellings in Tempo:

| Attribute key | TraceQL |
| --- | --- |
| `sahara.cycle.id` | `span.sahara.cycle.id` |
| `sahara.environment.id` | `span.sahara.environment.id` |
| `sahara.entity.definition` | `span.sahara.entity.definition` |
| `sahara.entity.instance.id` | `span.sahara.entity.instance.id` |
| `test.nodeid_hash` | `span.test.nodeid_hash` |
| `peer.service` | `span.peer.service` |
| `service.name` | `resource.service.name` |
| `deployment.environment` | `resource.deployment.environment` |

## Loki: log records

| OTLP | Loki | Spelling rule |
| --- | --- | --- |
| resource attribute in the default index list | stream label | `service.name` becomes `service_name` |
| any other resource attribute | structured metadata | `deployment.environment` becomes `deployment_environment` |
| scope name, version, dropped count | structured metadata `scope_name`, `scope_version`, `scope_dropped_attributes_count` | |
| scope attribute | structured metadata | dots to underscores |
| log record attribute | structured metadata | `sahara.cycle.id` becomes `sahara_cycle_id` |
| nested map attribute | flattened | `_` joins the levels |
| `TraceId`, `SpanId` | structured metadata `trace_id`, `span_id` | lower case hex |
| `SeverityText`, `SeverityNumber` | structured metadata `severity_text`, `severity_number` | `discover_log_levels`, default on since 3.1, also sets `detected_level` |
| `Flags`, `ObservedTimestamp`, dropped count | structured metadata `flags`, `observed_timestamp`, `dropped_attributes_count` | |
| `Body` | the log line | non-string bodies are stringified |
| `TimeUnixNano`, else `ObservedTimestamp` | the line timestamp | |

The default index list, `default_resource_attributes_as_index_labels`:
`cloud.availability_zone`, `cloud.region`, `container.name`,
`deployment.environment.name`, `k8s.cluster.name`, `k8s.container.name`,
`k8s.cronjob.name`, `k8s.daemonset.name`, `k8s.deployment.name`,
`k8s.job.name`, `k8s.namespace.name`, `k8s.pod.name`, `k8s.replicaset.name`,
`k8s.statefulset.name`, `service.instance.id`, `service.name`,
`service.namespace`. Note the environment key: `deployment.environment.name`
is indexed, the older `deployment.environment` is not. Pick one in the
vocabulary and, if it is the older key, promote it:

```yaml
limits_config:
  allow_structured_metadata: true        # required for OTLP; schema v13 and tsdb index
  otlp_config:
    resource_attributes:
      attributes_config:
        - action: index_label            # index_label | structured_metadata | drop
          attributes: [deployment.environment]
    log_attributes:
      - action: structured_metadata
        regex: sahara\..*                # the default anyway; shown for the shape
```

Sanitization, from the Loki docs: dots become underscores, and every other
character Prometheus label names do not allow is replaced with `_`. Label
limits: `max_label_names_per_series`, `max_label_name_length` default `1024`,
`max_label_value_length`. Structured metadata limits:
`max_structured_metadata_size` default 64KB per line,
`max_structured_metadata_entries_count` default 128 per line. Past either the
line is refused with HTTP 400.

Structured metadata is not a stream label: it cannot appear in the stream
selector, only in a label filter after it. `{service_name="sahara-harness"} | sahara_cycle_id="c-1"`.

## Prometheus and Mimir: metrics

Names, per the OpenTelemetry compatibility specification, applied by
Prometheus's OTLP endpoint under the default `otlp.translation_strategy:
UnderscoreEscapingWithSuffixes` and by the collector's `prometheusremotewrite`
exporter:

| Rule | Example |
| --- | --- |
| characters outside `[a-zA-Z0-9_:]` become `_`, runs of `_` collapse | `sahara.tests.duration` becomes `sahara_tests_duration` |
| unit appended as a word | `s` `seconds`, `ms` `milliseconds`, `By` `bytes`, `1` `ratio` on gauges only, `{poll}` dropped, `m/s` `meters_per_second` |
| monotonic sum gets `_total` unless it already ends in it | `sahara.controller.polls` unit `{poll}` becomes `sahara_controller_polls_total` |
| histogram becomes `_bucket` with `le`, `_count`, `_sum` | `sahara_tests_duration_seconds_bucket{le="1.024"}` |
| exponential histogram becomes a native histogram | one series, no `_bucket`; needs native histogram ingestion on |
| summary becomes `_count`, `_sum`, and `quantile` | |
| attribute key to label: same character rule | `sahara.entity.definition` becomes `sahara_entity_definition` |
| scope becomes labels | `otel_scope_name`, `otel_scope_version`, `otel_scope_schema_url` |
| resource becomes `target_info{...}` | plus `job` = `service.namespace/service.name` or `service.name`, `instance` = `service.instance.id` on every series |
| resource attribute as a label | only when listed in `otlp.promote_resource_attributes`, or `promote_all_resource_attributes: true` with `ignore_resource_attributes` |

Prometheus 3.x strategies: `UnderscoreEscapingWithSuffixes` default,
`UnderscoreEscapingWithoutSuffixes`, `NoUTF8EscapingWithSuffixes` keeps the
dots and quotes the name in PromQL as `{"sahara.tests.duration_seconds"}`,
`NoTranslation` experimental. Mimir: `-distributor.otel-translation-strategy`,
experimental, plus `-distributor.otel-promote-resource-attributes`,
`-distributor.otel-keep-identifying-resource-attributes`,
`-distributor.otel-promote-scope-metadata`. Write the strategy into the
vocabulary; the spelling column depends on it.

Temporality: cumulative only by default. Prometheus drops delta unless
`--enable-feature=otlp-deltatocumulative` converts it or
`--enable-feature=otlp-native-delta-ingestion` stores it raw. Mimir:
`distributor.otel-native-delta-ingestion`, experimental. The collector's
`prometheusremotewrite` exporter drops non-cumulative monotonic sums and
histograms. Leave the SDK on cumulative.

Histograms: classic buckets always work. Native histograms are stable since
Prometheus 3.8 with `scrape_native_histograms`; before 3.8 they need
`--enable-feature=native-histograms`. Mimir:
`-ingester.native-histograms-ingestion-enabled=true` or the per-tenant
`native_histograms_ingestion_enabled: true`. UNVERIFIED: whether Prometheus
3.8+ ingests OTLP exponential histograms as native histograms with no flag.

Exemplars: the OTLP translator keeps exemplars with `trace_id` and `span_id`
labels, source: `storage/remote/otlptranslator/prometheusremotewrite/helper.go`.
Storing them needs `--enable-feature=exemplar-storage`.

Domain spellings in Prometheus:

| Vocabulary | Instrument, unit | Prometheus |
| --- | --- | --- |
| `sahara.tests.duration` | histogram, `s` | `sahara_tests_duration_seconds_bucket`, `_count`, `_sum` |
| `sahara.controller.polls` | counter, `{poll}` | `sahara_controller_polls_total` |
| `sahara.entities.live` | updowncounter, `{entity}` | `sahara_entities_live` |
| label `sahara.entity.definition` | | `sahara_entity_definition` |
| resource `service.name` | | `job`, and `target_info{service_name=...}` |
| resource `deployment.environment` | | `target_info{deployment_environment=...}` only, unless promoted |

## Derived series: the two producers side by side

| Fact | Tempo metrics-generator | Collector connectors after `prometheusremotewrite` |
| --- | --- | --- |
| call count | `traces_spanmetrics_calls_total` | `traces_span_metrics_calls_total` |
| duration | `traces_spanmetrics_latency_bucket`, seconds, buckets `0.002` to `16.384` | `traces_span_metrics_duration_milliseconds_bucket`, unit `ms` default, `s` with `histogram.unit: s` |
| size | `traces_spanmetrics_size_total` | none |
| labels | `service`, `span_name`, `span_kind`, `status_code`; `status_message` off by default; `job`, `instance` with `enable_target_info` | `service_name`, `span_name`, `span_kind`, `status_code` |
| kind values | `SPAN_KIND_CLIENT` ... source: `modules/generator/processor/spanmetrics/spanmetrics.go` | `SPAN_KIND_CLIENT` ... |
| status values | `STATUS_CODE_OK`, `STATUS_CODE_ERROR`, `STATUS_CODE_UNSET` source: same file | same strings |
| extra labels | `dimensions: [sahara.entity.definition]` becomes label `sahara_entity_definition`; a clash with a default label is prefixed `__` | `dimensions: [{name: sahara.entity.definition}]` becomes `sahara_entity_definition` |
| resource info | `traces_target_info` with `enable_target_info: true` | `target_info` from the exporter |
| service graph | `traces_service_graph_request_total`, `_request_failed_total`, `_request_server_seconds_bucket`, `_request_client_seconds_bucket`, `_unpaired_spans_total`, `_dropped_spans_total` | same names; the histograms are declared in seconds so the exporter appends `_seconds` |
| service graph labels | `client`, `server`, `connection_type` = unset, `virtual_node`, `messaging_system`, `database` | `client`, `server`, `connection_type` = unset, `messaging_system`, `database`; `virtual_node` label with `virtual_node_extra_label: true` |
| uninstrumented peer | `peer_attributes` default `peer.service`, `db.name`, `db.system`, `db.system.name` on 3.0 | `virtual_node_peer_attributes` default `peer.service`, `db.name`, `db.system` |

Cardinality of span metrics is the product of distinct `service`, `span_name`,
`span_kind`, `status_code` and every `dimensions` value, times the bucket
count for the histogram. A `dimensions` entry from the attribute tier, such as
an instance id, multiplies the series by the number of instances forever.
Only label tier keys go in `dimensions`. `metrics/labels.md` decides.

## Never

- Never write `span.sahara_cycle_id` in TraceQL or `sahara.cycle.id` in
  LogQL. Tempo keeps the dots, Loki and Prometheus do not.
- Never put an id in `dimensions` or in `promote_resource_attributes`.
- Never switch `translation_strategy` after series exist. Old and new names
  are two families.

## Stop and ask

- The Loki index label list was changed with `ignore_defaults: true`. Every
  LogQL stream selector in `queries.md` assumes `service_name` is a label.
- Prometheus runs `NoTranslation` or `NoUTF8EscapingWithSuffixes`. Every
  metric name in this folder is written in the underscore spelling.
