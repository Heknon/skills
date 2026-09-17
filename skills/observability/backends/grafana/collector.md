# OpenTelemetry Collector between the SDK and the Grafana stack

Stamp: opentelemetry-collector-contrib READMEs and `metadata.yaml` at main for
`otlp`, `otlphttp`, `prometheusremotewrite`, `span_metrics`, `service_graph`;
Grafana Alloy component references at latest; Tempo 3.0, Loki 3.7, Prometheus
3.14 and Mimir 3.2 ingest docs; read 2026-09-17.

**Verdict you produce:** `no collector`, or the path of the collector's
`config.yaml`, plus one line per processor that touches attributes, copied
into the vocabulary's *Backend spelling* column, plus the line
`derived by: <Tempo metrics-generator | collector connectors | nothing>`, the
same value as `span metrics derived by` in `backends/README.md`. Write them
under *Correlation keys* and *Metrics* in `vocabulary.md`.

## What the collector changes and what it does not

Same as in `elastic/collector.md`: the collector is a relay. It does not
rename keys; Loki and Prometheus do that on arrival, `mapping.md` has the
map. It does not drop or add attributes unless a processor says so. It
re-batches, drops on `memory_limiter`, and holds whole traces when
`tail_sampling` is in the pipeline. What is new here is fan-out: three
stores, three exporters, and every one of them must be in the right pipeline.

## Known-good `config.yaml`

SDK sends OTLP to `localhost:4317` or `localhost:4318`. Rename the
`${env:...}` values and nothing else. The `connectors` block and the two
extra pipelines are for the `collector connectors` verdict only; delete them
under the `Tempo metrics-generator` verdict.

```yaml
receivers:
  otlp:                                     # one receiver, both transports
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317              # default localhost:4317
      http:
        endpoint: 0.0.0.0:4318              # default localhost:4318; /v1/traces /v1/metrics /v1/logs

processors:
  memory_limiter:                           # first in every pipeline
    check_interval: 1s
    limit_mib: 512
    spike_limit_mib: 128
  resource:
    attributes:
      - key: deployment.environment.name    # the SDK recipe sets deployment.environment, which Loki keeps as structured
        value: ${env:DEPLOYMENT_ENVIRONMENT} # metadata; Loki's default index list carries deployment.environment.name, so this
        action: insert                      # adds that key too and the environment becomes a stream label. The other way,
                                            # promoting deployment.environment with otlp_config, is in mapping.md. Pick one.
  attributes/scrub:                         # span, metric and log attributes; not resource
    actions:
      - key: db.statement
        action: delete
  batch:                                    # last processor
    timeout: 1s
    send_batch_size: 512

connectors:                                 # collector connectors verdict only
  span_metrics:                             # type span_metrics; spanmetrics is the deprecated spelling
    histogram:
      unit: s                               # default ms; s matches Tempo's seconds
      explicit:
        buckets: [2ms, 4ms, 8ms, 16ms, 32ms, 64ms, 128ms, 256ms, 512ms, 1024ms, 2048ms, 4096ms, 8192ms, 16384ms]
    dimensions:
      - name: sahara.entity.definition      # label tier only; becomes sahara_entity_definition
    exemplars:
      enabled: true
    aggregation_temporality: AGGREGATION_TEMPORALITY_CUMULATIVE
    metrics_flush_interval: 15s
    resource_metrics_key_attributes: [service.name, service.namespace, service.instance.id]
  service_graph:                            # type service_graph; servicegraph is the deprecated spelling
    latency_histogram_buckets: [2ms, 4ms, 6ms, 8ms, 10ms, 50ms, 100ms, 200ms, 400ms, 800ms, 1s, 1400ms, 2s, 5s, 10s, 15s]
    store:
      ttl: 10s                              # default 2s; the pair must arrive inside it
      max_items: 10000                      # default 1000
    virtual_node_peer_attributes: [peer.service, db.name, db.system]
    virtual_node_extra_label: true          # adds the virtual_node label
    metrics_flush_interval: 15s

exporters:
  otlp/tempo:                               # OTLP/gRPC to Tempo's distributor
    endpoint: ${env:TEMPO_ENDPOINT}         # host:port, for example tempo:4317; no scheme
    tls:
      insecure: true
  otlphttp/loki:                            # OTLP/HTTP to Loki
    endpoint: http://${env:LOKI_ENDPOINT}/otlp   # exporter appends /v1/logs; Loki listens on 3100
    headers:
      X-Scope-OrgID: ${env:TENANT}          # required while auth_enabled is true
  otlphttp/prometheus:                      # OTLP/HTTP to Prometheus
    endpoint: http://${env:PROMETHEUS_ENDPOINT}/api/v1/otlp   # exporter appends /v1/metrics; needs --web.enable-otlp-receiver
  otlphttp/mimir:                           # OTLP/HTTP to Mimir; use this or otlphttp/prometheus, not both
    endpoint: http://${env:MIMIR_ENDPOINT}/otlp                # exporter appends /v1/metrics; Mimir listens on 8080
    headers:
      X-Scope-OrgID: ${env:TENANT}
  debug:                                    # verification ladder rung 2; remove in production
    verbosity: detailed
    sampling_initial: 5
    sampling_thereafter: 1

service:
  telemetry:
    logs:
      level: info
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, resource, attributes/scrub, batch]
      exporters: [otlp/tempo, debug]        # add span_metrics, service_graph for the connectors verdict
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, resource, attributes/scrub, batch]
      exporters: [otlphttp/prometheus, debug]
    metrics/derived:                        # connectors verdict only
      receivers: [span_metrics, service_graph]
      processors: [memory_limiter, batch]
      exporters: [otlphttp/prometheus]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, resource, attributes/scrub, batch]
      exporters: [otlphttp/loki, debug]
```

Environment the collector reads: `DEPLOYMENT_ENVIRONMENT`, `TEMPO_ENDPOINT`,
`LOKI_ENDPOINT`, `PROMETHEUS_ENDPOINT` or `MIMIR_ENDPOINT`, `TENANT`.

Sending the derived metrics over OTLP means Prometheus names them by its own
translation: `traces.span.metrics.calls` becomes
`traces_span_metrics_calls_total`, the histogram with unit `s` becomes
`traces_span_metrics_duration_seconds_bucket`, and `service.name` becomes
`service_name`. The `prometheusremotewrite` exporter, `endpoint:
http://prometheus:9090/api/v1/write` or `http://mimir:8080/api/v1/push`,
produces the same spellings and drops anything non-cumulative. Either way the
names differ from the metrics-generator's; `screens.md` says which Grafana
views care.

## The two connectors, and the one rule

`span_metrics` emits `traces.span.metrics.calls` and
`traces.span.metrics.duration` per `service.name`, `span.name`, `span.kind`,
`status.code`, plus each `dimensions` entry. `service_graph` emits
`traces_service_graph_request_total`, `_request_failed_total`,
`_request_server`, `_request_client`, `_unpaired_spans_total`,
`_dropped_spans_total` per `client`, `server`, `connection_type`, pairing a
`CLIENT` span with the `SERVER` span it parented, or `PRODUCER` with
`CONSUMER`, and naming an unpaired peer from `virtual_node_peer_attributes`.

Run them only under the `collector connectors` verdict from `overview.md`:
a sampler stands between the SDK and Tempo. Then order the traces pipeline so
the connectors see every span: `exporters: [span_metrics, service_graph,
otlp/tempo]` on a pipeline without the sampler, and a second traces pipeline
`traces/sampled` with `tail_sampling` feeding `otlp/tempo`. UNVERIFIED: the
exact two-pipeline layout with a `forward` connector; the README shows only
the one-pipeline wiring. Under the `Tempo metrics-generator` verdict the
connectors are off and Tempo does the same work on the spans it stored.

## `tail_sampling` in one paragraph

As in `elastic/collector.md`: `decision_wait`, `policies`, `num_traces`, whole
traces or nothing, `loadbalancing` in front when there are two instances. On
this stack the counts on every screen follow the sampled set unless the
connectors ran first. Tempo has no tail sampler of its own.

## Grafana Alloy

Alloy is the collector with a different syntax and the same components. The
equivalent file, once, is `collector-alloy.md`. Same verdicts, same rule about
the connectors.

## Rule: processors rewrite the vocabulary

Every `resource`, `attributes`, `transform` or `redaction` entry is a change
to what the stores hold. For each `key`, update *Backend spelling* in
`vocabulary.md` per store: Tempo keeps the key, Loki and Prometheus underscore
it, `delete` becomes `not stored`. A checker cannot see this file.

## Running it locally

```sh
otelcol-contrib validate --config config.yaml   # exit 0, no output, means it parses
otelcol-contrib --config config.yaml             # foreground; logs and debug output on stderr
otelcol-contrib --version                        # source: otelcol/command.go sets cobra Version
```

Under the deb or rpm package the collector's config is
`/etc/otelcol-contrib/config.yaml` and the unit `otelcol-contrib`, as in
`elastic/collector.md`. Alloy's commands and paths are in `collector-alloy.md`.

## Errors, verbatim, and their cause

| Log text | Cause |
| --- | --- |
| `Exporting failed. Will retry the request after interval.` with `code = Unavailable` ... `connect: connection refused` | nothing listening at `endpoint`; Tempo's `distributor.receivers.otlp` default binds `localhost`, so a remote collector needs `endpoint: 0.0.0.0:4317` on Tempo too |
| `Exporting failed. Dropping data.` with `Permanent error` and HTTP `404` from `otlphttp/prometheus` | `--web.enable-otlp-receiver` not set, or `endpoint` missing the `/api/v1/otlp` prefix. UNVERIFIED: exact body text |
| HTTP `401` or a body containing `no org id` from Loki or Mimir | `X-Scope-OrgID` header missing while multitenancy is on. UNVERIFIED: exact body text |
| `RATE_LIMITED: ingestion rate limit (30000000 bytes) exceeded while adding 10 bytes` from Tempo | Tempo `overrides.defaults.ingestion.rate_limit_bytes` and `burst_size_bytes` too low for the burst |
| `pusher failed to consume trace data` in Tempo's distributor log | the refusal reason is in `tempo_discarded_spans_total{reason=...}`: `trace_too_large`, `live_traces_exceeded`, `rate_limited`. source: `modules/overrides/discarded_spans.go` |
| HTTP `429` from Loki, body `Ingestion rate limit exceeded` or `Maximum active stream limit exceeded` | `ingestion_rate_mb`, `ingestion_burst_size_mb`, or `max_global_streams_per_user`; a stream label with unbounded values, such as an id promoted to `index_label` |
| HTTP `400` from Loki, body `entry too far behind` or `timestamp too new` | clock skew or a late flush past `reject_old_samples_max_age` or `creation_grace_period` |
| HTTP `400` from Loki, reason `structured_metadata_too_many` or `structured_metadata_too_large` | more than `max_structured_metadata_entries_count` attributes, default 128, or over `max_structured_metadata_size`, default 64KB, on one line |
| HTTP `400` from Loki, reason `disallowed_structured_metadata` | `allow_structured_metadata` is false; OTLP ingest needs it true |
| `x509: certificate signed by unknown authority` | private CA and no `tls.ca_file` |
| `data refused due to high memory usage` | `memory_limiter` fired; the SDK retries |
| `Error: invalid configuration:` at start | a pipeline names a component not declared, or `spanmetrics` was spelled `span_metrics` on an old build, or the reverse; run `validate` |

## Never

- Never send the derived metrics and turn on Tempo's generator for the same
  tenant.
- Never put `batch` before `memory_limiter` or before a sampler.
- Never send logs to Loki without `service.name` on the resource. The stream
  becomes `service_name="unknown_service"` and every screen filters on it.
- Never leave `debug` at `detailed` in production.

## Stop and ask

- A processor is wanted that the vocabulary has no row for.
- The collector must fan out to a second Tempo or a second Prometheus. Two
  producers, two spelling columns.
- Traces are sampled before Tempo and someone wants the metrics-generator
  anyway. The counts will be of the sample.
