# Sampling and volume

**Verdict you produce:** the sampler and its rate, the span limits, the rule
for where a large value goes, and the retention each signal is designed
against. All go into `vocabulary.md` under *Volume*.

Sampling removes whole traces. Limits remove parts of spans. Retention
removes everything after a date. Each changes what a chart says, so each is
decided here and written down, never at a call site.

All SDK names are from opentelemetry-python 1.2x.

## Questions

1. **How many root spans per hour at peak, and how many spans per root?**
   Count from a real run. Multiply. Compare with what the backend ingests
   without dropping. If it fits, the sampler is `parentbased_always_on` and
   you skip to question 5.
2. **Must every failure be kept?** Yes: head sampling is out, because it
   decides before the outcome is known. Use tail sampling, or reduce spans
   per root instead of roots.
3. **Do derived metrics need to be exact?** Test count, failure rate,
   throughput. Yes: head sampling is out unless the sampling rate reaches
   the backend, and from opentelemetry-python it does not. See below.
4. **Do all spans of one trace reach the same collector?** Tail sampling in
   the collector requires it. No: tail sample in the backend's own receiver
   when it has one; `backends/<backend>/overview.md` says whether it does.
5. **Is any attribute value longer than 1000 characters, or is any span
   carrying more than a few dozen attributes or events?** Read the export.
   Yes: go to *Where a large value goes*.
6. **How long must each question stay answerable?** "Which test failed last
   night" and "how did failure rate move this quarter" have different
   answers. Read the retention per data stream and match each question to a
   signal that lives long enough.

## Head sampling

- SDK: `opentelemetry.sdk.trace.sampling.ParentBased(root=TraceIdRatioBased(rate))`,
  or by environment `OTEL_TRACES_SAMPLER=parentbased_traceidratio` and
  `OTEL_TRACES_SAMPLER_ARG=0.1`. Default is `parentbased_always_on`.
  `ParentBased(root, remote_parent_sampled=ALWAYS_ON, remote_parent_not_sampled=ALWAYS_OFF, local_parent_sampled=ALWAYS_ON, local_parent_not_sampled=ALWAYS_OFF)`.
- The decision is made at the root. Children follow the parent's flag, so a
  trace is whole or absent. A dropped span is a `NonRecordingSpan`:
  `is_recording()` is `False`, attributes and events are discarded, nothing
  is exported.
- **The rate and derived counts.** The opentelemetry-python
  `TraceIdRatioBased` writes nothing into `tracestate`, so no backend can
  read the rate off the data, and every count the backend derives from spans
  is low by the sampling factor unless the backend is told the rate some
  other way. Write that in the vocabulary next to the rate, or do not head
  sample. How each backend weights is in `backends/<backend>/overview.md`
  and side by side in `backends/paradigms.md`.
- **Logs.** A log record inside a span carries the span's `trace_id` and
  `span_id` whether or not the span is sampled. When the span was dropped,
  the log line's `trace.id` points at a trace that does not exist. A line
  that must be found later belongs to `logs/` under `core/signal-choice.md`
  question 4, and does not depend on the span.
- **Errors.** Whether an exception outlives a dropped trace depends on the
  backend; see *On Elastic* below and the exceptions row in
  `backends/<backend>/mapping.md`. The span status and the trace around it
  are never kept.

## Tail sampling

- Collector: processor `tail_sampling`, keys `decision_wait`, `num_traces`,
  `expected_new_traces_per_sec`, `policies`. Policy types include
  `always_sample`, `probabilistic`, `status_code`, `latency`,
  `string_attribute`, `and`, `composite`. All spans of a trace must reach the
  same collector instance.
- A backend with its own receiver may tail sample there instead, and then
  derives its metrics from every event, so derived counts stay exact. Which
  backends can, and their keys, is in `backends/<backend>/overview.md`.

## Limits

The SDK's span limits, `opentelemetry.sdk.trace.SpanLimits`, with each
parameter's environment variable and default, are the table in
`traces/span-attributes-and-events.md`. Do not copy it here; read it there.
What matters for this verdict: over a count the SDK drops and counts the
drop in `dropped_attributes`, `dropped_events`, `dropped_links` on the span;
over a length it truncates, silently. Set `OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT`
explicitly so the cut is the same on every worker, and read the backend's
own cap on a stored value in `backends/<backend>/mapping.md`.

## Where a large value goes

| Value | Verdict |
| --- | --- |
| A bounded dictionary a person reads on the span's screen, under the length limit as JSON | one attribute, one JSON string, key from the vocabulary |
| A dictionary whose keys a customer controls | the same one JSON string, never one attribute per key |
| A list of moments inside the span | span events, one per moment, up to `max_events` |
| Anything over the length limit, a body, a file, a screenshot, a full response | out of the trace; store it where it belongs and put its locator on the span as one string attribute such as `artifact.url` |
| A number that repeats every second inside the span | a metric |

## Retention

Each store keeps each signal for its own time, set per backend and read from
the running system with the commands in `backends/<backend>/overview.md`. A
question that outlives the trace store must be answered by a derived or
emitted metric in the metric store, decided in `metrics/derived-or-emitted.md`.

## Verdict

Write into `vocabulary.md` under *Volume*. The histogram boundaries line is
filled by `metrics/units-and-buckets.md` and stays in this block:

```
sampler: <parentbased_always_on | parentbased_traceidratio rate=<r> | tail: collector | tail: backend> ; derived counts exact: <yes | low by 1/r>
span limits: OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT=<n>, OTEL_SPAN_EVENT_COUNT_LIMIT=<n>, others default
large values: <attribute key> as JSON string ; <attribute key> as locator, stored at <where>
histogram boundaries: <metric name>: <upper bounds in the metric's unit> ; ...
retention: traces <days>, metrics <days>, logs <days> ; questions past trace retention: <metric names>
```

## Never

- Never sample at a call site by skipping `start_span` on a condition. The
  sampler is the one place, and a missing child breaks the waterfall.
- Never head sample and then read a count chart as exact.
- Never rely on the length limit to protect the index. Decide where the
  value goes before it reaches the SDK.
- Never split a payload over many attributes to dodge the length limit.
- Never depend on a log line's `trace.id` under head sampling.
- Never let two workers run with different `OTEL_TRACES_SAMPLER_ARG`.

## Stop and ask

- The volume does not fit and failures must all be kept and no tail sampling
  is available in the collector or the backend. A person picks what to lose.
- A person wants a payload on the span that is over the length limit and
  refuses a locator. That is a cost decision for them.
- Retention for a stream is unknown and the cluster APIs are not reachable.

## Examples

| Situation | Verdict |
| --- | --- |
| 50 000 tests per night, 12 spans each, backend takes it | `parentbased_always_on` |
| 5 million tests per night, every failure must be kept | tail sampling with a `status_code` or `trace.outcome` policy keeping `failure` at rate 1 |
| Entity fields dictionary, customer keys, 2 KB | `sahara.entity.fields_json` as one string attribute; a JSON payload attribute always ends in `_json` |
| Controller response body, 400 KB | stored as a run artifact, `artifact.url` on `entity.create` |
| Failure rate per test over a quarter | derived metric in the metric store, checked against its retention |
| Retry loop adding 300 events to one span | 128 kept, 172 dropped; make each attempt a child span instead |

## On Elastic

- **Head sampling and the rate.** Elastic computes throughput and latency
  from sampled events, weighted by the inverse sampling rate through
  `transaction.representative_count`. From `elastic/apm-data`,
  `input/otlp/traces.go`, the rate for OTLP is read from `tracestate`,
  vendor key `ot`, field `p:`, and the count is `2^p`. With
  opentelemetry-python the count stays `1`.
- **Errors.** Error documents are kept regardless of the sampling decision.
- **Tail sampling in APM Server.** `apm-server.sampling.tail.enabled`,
  `interval`, `ttl`, `policies`, `storage_limit`,
  `discard_on_write_failure`. Policy keys: `sample_rate`, `trace.name`,
  `trace.outcome`, `service.name`, `service.environment`. The last policy
  carries only `sample_rate`. Fleet shows the same settings under `Enable
  tail-based sampling` and `Policies`. With tail sampling Elastic computes
  metrics from all events, so derived counts stay exact.
- **Stored length.** UNVERIFIED: the `ignore_above` value Elastic's APM
  index templates apply to `labels.*` keyword fields, past which a value is
  stored but not searchable.
- **Retention.** Each data stream, `traces-apm-<namespace>`,
  `metrics-apm-<namespace>`, `logs-apm.error-<namespace>`, has its own
  lifecycle policy. Read them with `GET _data_stream/<name>` and
  `GET _ilm/policy/<policy name>`.

Other backends: the verdicts do not change; the stored shape is in
`backends/<backend>/mapping.md` and the differences in `backends/paradigms.md`.
The collector's `span_metrics` connector counts what the collector saw, so
place it before any sampler.
