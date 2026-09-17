# Instrument type

**Verdict you produce:** one of `counter`, `updowncounter`, `histogram`,
`gauge`, plus `synchronous` or `observable`, plus the field it becomes in
Elastic. It goes into the *Metrics* table of `vocabulary.md`.

Come here only after `core/signal-choice.md` said `metric` and
`metrics/derived-or-emitted.md` said `emit`. A value that already has a span is
not measured twice.

## Questions

Answer with a fact about the value. The first yes is the verdict.

1. **Does the value only ever go up?** A total of things that happened:
   polls sent, bytes written, retries. It never needs to go down. A restart
   setting it back to zero is fine.
   **Yes: `counter`.** Monotonic. You add positive amounts.
2. **Is it a set of individual measurements you will ask percentiles of?**
   A duration, a size, a queue wait. You care about p50, p95, p99, not the
   total.
   **Yes: `histogram`.** Then go to `metrics/units-and-buckets.md`.
3. **Is it a current level that goes up and down, and is the sum across label
   values meaningful?** Live entities, open connections, items in a queue you
   add to and remove from. Two workers with 3 and 4 live entities mean 7.
   **Yes: `updowncounter`.** Non monotonic. You add positive and negative
   amounts at the moment the level changes.
4. **Is it a current level whose sum across labels means nothing?**
   Heap bytes of one process, a ratio, a temperature, a value read from
   somewhere else.
   **Yes: `gauge`.**

Then answer one more:

5. **Do you have a line of code at the moment the value changes?**
   **Yes: synchronous.** `create_counter`, `create_up_down_counter`,
   `create_histogram`, `create_gauge`.
   **No, you can only read it when asked: observable.** `create_observable_counter`,
   `create_observable_up_down_counter`, `create_observable_gauge`, each with a
   callback the SDK calls once per export. A histogram is never observable.

## The Python names

opentelemetry-python 1.2x line, package `opentelemetry-api`, on a `Meter`:

| Verdict | Call | Since |
| --- | --- | --- |
| counter | `meter.create_counter(name, unit="", description="")` | 1.0 |
| updowncounter | `meter.create_up_down_counter(name, unit="", description="")` | 1.0 |
| histogram | `meter.create_histogram(name, unit="", description="", explicit_bucket_boundaries_advisory=None)` | advisory since 1.30.0 |
| gauge, synchronous | `meter.create_gauge(name, unit="", description="")` | 1.23.0 |
| any, observable | `meter.create_observable_gauge(name, callbacks=None, unit="", description="")` and the counter forms | 1.0 |

A callback has the signature `def callback(options: CallbackOptions) -> Iterable[Observation]`
and yields `Observation(value, attributes)`. Both classes come from
`opentelemetry.metrics`. A counter refuses a negative amount: the SDK logs
`Add amount must be non-negative on Counter` and drops it. A histogram refuses
one the same way.

## What each becomes in Elastic 8.x

Every OTLP metric lands in `metrics-apm.app.<service.name>-<namespace>` with
`metricset.name: app`. The metric name becomes a top level field of that name.
Source for these rows: `elastic/apm-data` `input/otlp/metrics.go` and the
`metrics-apm@pipeline` ingest pipeline.

| Verdict | OTLP data | Elastic field | Mapping |
| --- | --- | --- | --- |
| counter | Sum, `is_monotonic: true` | `<name>` | `double`, dynamic template `double_metrics` |
| updowncounter | Sum, `is_monotonic: false` | `<name>` | `double` |
| gauge | Gauge | `<name>` | `double` |
| histogram | Histogram | `<name>.values`, `<name>.counts` | `histogram` field type, dynamic template `histogram_metrics` |
| exponential histogram | ExponentialHistogram | nothing | dropped as unsupported |

A histogram is stored as the Elasticsearch `histogram` type: paired `values`
and `counts` arrays, one pair per document, not searchable, usable by the
`percentiles`, `avg`, `sum`, `min`, `max` and `value_count` aggregations. The
`values` are the midpoints of your bucket boundaries, so percentile precision
is exactly your boundaries. See `metrics/units-and-buckets.md`.

## Verdict

Write into the *Metrics* table of `vocabulary.md`:

```
| <namespace.noun.measure> | <counter, updowncounter, histogram, gauge> <synchronous or observable> | <unit> | <labels> | no |
```

## Never

- Never use a histogram for something that has a span. The backend has it.
- Never use a gauge for something you can count. A gauge sampled at export
  loses everything that happened between two exports.
- Never use a counter for a level. A counter of "entities created" minus a
  counter of "entities destroyed" is two series and a subtraction nobody does.
- Never read a value back from an instrument. Instruments are write only.
- Never create an instrument at the call site. Create it once at import time
  in the module that holds the vocabulary strings, and import it.
- Never send an exponential histogram to Elastic 8.x. It is dropped.

## Stop and ask

- The value is summable on some labels and not on others.
- The value goes up but is reset on purpose inside one process, for example
  per cycle. A counter with a reset that is not a restart confuses rate
  functions. A person decides whether it is a gauge instead.
- The distribution has fewer than about ten measurements per export
  interval. A histogram of ten values is ten span attributes wearing a
  costume. See `core/signal-choice.md`.

## Examples

| Value | Verdict | Why |
| --- | --- | --- |
| Controller status polls sent | counter, synchronous | only goes up, too frequent for spans |
| Live entities per definition | updowncounter, synchronous | goes up on create, down on destroy, sums across definitions |
| Tests still queued on a worker | gauge, observable | a level read from the scheduler, not summable in a useful way per worker |
| Poll round trip time | histogram | percentiles wanted, no span around a poll |
| Test duration | none, derived | the test is a transaction; see `metrics/derived-or-emitted.md` |
| Worker heap bytes | gauge, observable | read from the runtime on demand |
