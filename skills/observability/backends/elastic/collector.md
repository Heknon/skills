# OpenTelemetry Collector between the SDK and APM Server

Stamp: opentelemetry-collector-contrib, config verified against the component
READMEs on 2026-09-17. Elastic 8.x target. 9.x notes at the end.

**Verdict you produce:** either `no collector` or the path of the collector's
`config.yaml`, plus one line per processor that touches attributes, copied
into the vocabulary's *Backend spelling* column. Write it under *Correlation
keys* in `vocabulary.md` as `collector: <path or none>`.

## What the collector changes and what it does not

The collector is a relay. It forwards OTLP as OTLP. Left alone it changes
nothing a document holds.

- It does **not** rename keys. `cycle.id` leaves the collector as `cycle.id`.
  APM Server is what writes it as `labels.cycle_id`. The rename map is in
  `apm-server-mapping.md`.
- It does **not** drop or add attributes unless a processor says so.
- It **does** re-batch. A span leaves the collector up to `batch.timeout`
  after it arrived.
- It **does** drop data when `memory_limiter` fires, and logs that it did.
- It **does** hold on to whole traces for `decision_wait` when `tail_sampling`
  is in the pipeline, and drops the traces it decides against.

## Known-good `config.yaml`

SDK sends OTLP to `localhost:4317` or `localhost:4318`. Collector sends OTLP to
APM Server on port `8200`. Rename the two `${env:...}` values and nothing else.

```yaml
receivers:
  otlp:                                     # one receiver, both transports
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317              # default is localhost:4317; 0.0.0.0 lets other hosts in
      http:
        endpoint: 0.0.0.0:4318              # default is localhost:4318; paths /v1/traces /v1/metrics /v1/logs

processors:
  memory_limiter:                           # must be the first processor in every pipeline
    check_interval: 1s                      # how often heap is measured
    limit_mib: 512                          # hard limit; data is refused above it
    spike_limit_mib: 128                    # soft limit is limit_mib minus this
  resource:                                 # resource attributes only, same on every signal
    attributes:
      - key: deployment.environment         # APM Server maps this to service.environment
        value: ${env:DEPLOYMENT_ENVIRONMENT}
        action: insert                      # insert: only when the SDK did not set it
  attributes/scrub:                         # span, metric and log attributes; not resource
    actions:
      - key: user.email                     # example sensitive key; use your vocabulary's
        action: hash                        # value becomes its SHA1 hex; key stays
      - key: db.statement                   # example of removal
        action: delete                      # key and value are gone before export
  batch:                                    # last processor; after memory_limiter and any sampler
    timeout: 1s                             # send at least this often
    send_batch_size: 512                    # or as soon as this many items are queued

exporters:
  otlp:                                     # OTLP/gRPC to APM Server
    endpoint: ${env:ELASTIC_APM_SERVER_ENDPOINT}   # host:port, for example apm-server:8200; no scheme, no path
    headers:
      Authorization: "Bearer ${env:ELASTIC_APM_SECRET_TOKEN}"   # or "ApiKey <base64 id:key>"
    tls:
      insecure: true                        # plain HTTP APM Server; delete this line for TLS
      # ca_file: /etc/ssl/apm-ca.pem        # TLS with a private CA
  otlphttp:                                 # OTLP/HTTP alternative; same port on APM Server
    endpoint: http://${env:ELASTIC_APM_SERVER_ENDPOINT}   # exporter appends /v1/traces /v1/metrics /v1/logs
    headers:
      Authorization: "Bearer ${env:ELASTIC_APM_SECRET_TOKEN}"
  debug:                                    # verification ladder rung 2; remove in production
    verbosity: detailed                     # prints every span, attribute and resource attribute
    sampling_initial: 5                     # first 5 batches in full
    sampling_thereafter: 1                  # then every batch; raise to 200 to thin it

service:
  telemetry:
    logs:
      level: info                           # debug shows every export attempt
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, resource, attributes/scrub, batch]   # order is execution order
      exporters: [otlp, debug]              # swap otlp for otlphttp to use HTTP
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, resource, attributes/scrub, batch]
      exporters: [otlp, debug]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, resource, attributes/scrub, batch]
      exporters: [otlp, debug]
```

Environment the collector reads: `DEPLOYMENT_ENVIRONMENT`,
`ELASTIC_APM_SERVER_ENDPOINT`, `ELASTIC_APM_SECRET_TOKEN`. Set them in the
shell or the systemd unit before starting it.

## The `spanmetrics` connector

A connector is an exporter of one pipeline and a receiver of another. Wired
as `traces: exporters: [spanmetrics]` and `metrics: receivers: [spanmetrics]`,
it emits, per `service.name`, `span.name`, `span.kind` and `status.code`:

- `traces.span.metrics.calls`, a counter of spans,
- `traces.span.metrics.duration`, a histogram of span duration in `ms`,
- `traces.span.metrics.events` when enabled.

Do not add it in front of APM Server. APM Server already aggregates the same
spans into `metrics-apm.transaction.*` and `metrics-apm.service_destination.*`
and Kibana draws its latency and throughput charts from those. The connector's
metrics land in `metrics-apm.app.*` as a second count of every span. A chart
built on both counts every span twice. Invariant 8: one fact, one signal.

## `tail_sampling` in one paragraph

`tail_sampling` buffers every span of a trace for `decision_wait`, default
`30s`, then applies its `policies` in order, such as `status_code` with
`status_codes: [ERROR]`, `latency` with `threshold_ms`, and `probabilistic`
with `sampling_percentage`. It holds at most `num_traces` traces. It must see
whole traces: a trace whose spans reach two collector instances is decided
twice and can be half kept. The README's answer is two layers, a
`loadbalancing` exporter in front keyed by trace id and `tail_sampling` behind
it. Prefer APM Server's own tail sampling from `elastic-agent.md` when the
collector is a single box, and read `core/sampling-and-volume.md` before
turning either on. Whatever samples, Kibana's counts follow the sampled set.

## Rule: processors rewrite the vocabulary

Every `resource`, `attributes`, `transform` or `redaction` processor entry is a
change to what the index holds. For each `key` it names, update the row's
*Backend spelling* in `vocabulary.md`: `delete` becomes `not indexed`, `hash`
becomes `labels.<spelling> (SHA1 hex)`, `insert` adds a row. A checker that
reads the vocabulary cannot see the collector config. If the two disagree, the
vocabulary is wrong.

## Running it locally

```sh
otelcol-contrib validate --config config.yaml   # exit 0 and no output means the file parses
otelcol-contrib --config config.yaml             # foreground; logs go to stderr
```

Its own logs, and the `debug` exporter's output, go to **stderr** through the
internal logger. Redirect with `2> collector.log`. Under the deb or rpm package
the config is `/etc/otelcol-contrib/config.yaml`, the unit is
`otelcol-contrib`, and the logs are `journalctl -u otelcol-contrib`.
`UNVERIFIED:` the docs page fetched names the core package paths
`/etc/otelcol/config.yaml` and unit `otelcol`; the contrib package uses the
same layout with `otelcol-contrib` in place of `otelcol`.

## Errors, verbatim, and their cause

| Log text | Cause |
| --- | --- |
| `Exporting failed. Dropping data.` with `Permanent error: rpc error: code = Unauthenticated desc = authentication failed: missing or improperly formatted Authorization header: expected 'Authorization: Bearer secret_token' or 'Authorization: ApiKey base64(API key ID:API key)'` | no `Authorization` header reached APM Server, or the value is not `Bearer <token>` or `ApiKey <base64>` with one space |
| `code = Unauthenticated` with a different `desc` | header present, token or key wrong. `UNVERIFIED:` exact `desc` text for a mismatched token |
| `Exporting failed. Will retry the request after interval.` with `rpc error: code = DeadlineExceeded desc = context deadline exceeded` | exporter `timeout` expired, default `5s` for `otlp` and `30s` for `otlphttp`; APM Server slow, unreachable, or a firewall dropping packets |
| `rpc error: code = Unavailable desc = connection error` ending in `connect: connection refused` | nothing listening at `endpoint`; wrong host or port, or APM Server not running |
| `x509: certificate signed by unknown authority` | APM Server TLS with a private CA and no `tls.ca_file` |
| `first record does not look like a TLS handshake` | exporter has TLS on and APM Server is plain HTTP; set `tls.insecure: true` |
| `Exporting failed. No more retries left. Dropping data.` | retries ran past `retry_on_failure.max_elapsed_time`; the batch is gone |
| `data refused due to high memory usage` from `memory_limiter` | over `limit_mib`; SDK sees an error and retries |
| `Error: invalid configuration:` at start | a pipeline names a component not declared, or a key is misspelled; run `validate` |

## Never

- Never rename a key in the collector to make it look like the index. The
  index spelling is APM Server's job and is recorded in the vocabulary.
- Never put `batch` before a sampler or before `memory_limiter`.
- Never leave `debug` with `verbosity: detailed` on in production. It writes
  every attribute of every span to the log.
- Never run two `tail_sampling` collectors behind a round-robin load balancer.

## Stop and ask

- A processor is wanted that the vocabulary has no row for.
- Someone wants `spanmetrics` for a chart Kibana already draws.
- The collector must fan out to a second backend. That is a second exporter
  and a second spelling column.

## Elastic 9.x

Elastic Agent 9.2 ships an OpenTelemetry Collector inside it, and from 9.5 the
EDOT Collector is that built-in one. Its default config writes to
Elasticsearch through the `elasticsearch` exporter with `mapping: mode: otel`,
not through APM Server. Documents then keep dotted keys under `attributes.*`
instead of `labels.*` with underscores. That is a different spelling column;
stop and ask before mixing the two paths in one vocabulary.
