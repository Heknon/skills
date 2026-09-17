# vmagent between the SDK and VictoriaMetrics

Stamp: vmagent v1.152.0, stream aggregation and relabeling docs, read
2026-09-17.

**Verdict you produce:** `vmagent: none`, or the vmagent flags that touch
names, one per line, copied into the vocabulary: every `-remoteWrite.label`,
every `-remoteWrite.relabelConfig` rule, every `-streamAggr.config` entry
with its output name.

## What vmagent is on this path

A relay for metrics only. It accepts OTLP at
`http://<vmagent>:8429/opentelemetry/v1/metrics`, the same flags as the
storage apply to what it accepts, and it forwards over Prometheus remote
write to every `-remoteWrite.url`. It never sees a span or a log line.


Point `metrics_endpoint` at `http://<vmagent>:8429/opentelemetry/v1/metrics`
and run vmagent with `-remoteWrite.url=http://<vmsingle>:8428/api/v1/write`.
That buys three things the collector does not have:

- `-remoteWrite.relabelConfig=relabel.yml` to drop a label before storage:
  ```yaml
  - action: labeldrop
    regex: "sahara_cycle_id|test_nodeid_hash"
  ```
  and `-remoteWrite.label=datacenter=foobar` to add one everywhere.
- `-streamAggr.config=aggr.yml` to derive cheap aggregates from **metrics**:
  ```yaml
  - match: 'sahara_tests_total'
    interval: 1m
    by: [service_name, sahara_test_status]
    outputs: [total, rate_sum]
  ```
  writes `sahara_tests_total:1m_by_service_name_sahara_test_status_total`
  and `..._rate_sum`. Output name rule:
  `<metric_name>:<interval>[_by_<labels>][_without_<labels>]_<output>`.
  `histogram_bucket` gives `vmrange` buckets from a gauge, `quantiles(0.5,
  0.99)` adds a `quantile` label. Raw input is still written unless
  `-streamAggr.dropInput` is set. Compare `span_metrics`: that one reads
  spans; this one never sees a span.
- A disk queue at `-remoteWrite.tmpDataPath`, bounded by
  `-remoteWrite.maxDiskUsagePerURL`, when storage is down.

The OTLP naming flags apply on vmagent too; set
`-opentelemetry.usePrometheusNaming` there and not on the storage, or on
both, never on neither with a relabel rule that expects underscores.


## How to see that one sample left vmagent

- `http://<vmagent>:8429/metrics`: `vmagent_remotewrite_bytes_sent_total`
  rising, `vmagent_remotewrite_push_failures_total` and
  `vmagent_remotewrite_samples_dropped_total` still, `vmagent_remotewrite_pending_data_bytes` near zero.
- `-remoteWrite.showURL` prints the destination URLs in the log at start;
  without it they are hidden.
- Then rung 3 of `verification-ladder.md` against the storage. vmagent
  keeps nothing to query.

## Never

- Never relabel to make a name look like the vocabulary. Change the
  vocabulary, or the flag that produced the name.
- Never aggregate with `by:` on a label that is an id.
- Never run two vmagents with the same `-streamAggr.config` behind a load
  balancer; each aggregates half the samples.

## Stop and ask

- A relabel rule is wanted that no vocabulary row explains.
- `-remoteWrite.maxHourlySeries` is wanted as a fix for cardinality. It
  drops silently; the id in the label is the fix.
