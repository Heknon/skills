# Checks

Three scripts that judge an export mechanically. Run the one that matches the
signal you changed, on a real export, and paste its output into your answer.
Standard library only, Python 3.11. Keep `check_common.py` next to them.

| Script | Reads | Rules |
| --- | --- | --- |
| `check_spans.py --spans FILE [--vocabulary vocabulary.md] [--max-name-cardinality 200] [--time-tolerance-ms 1] [--json]` | span export | input-not-empty, ids-well-formed, vocabulary-sane, roots-are-units, one-parent, orphans (WARN), name-cardinality, names-in-vocabulary, kind-matches-vocabulary, required-attributes, attribute-types, label-values, forbidden-values, exit-spans-have-destination, errors-are-recorded, errors-without-exception (WARN), exceptions-set-status (WARN), time-sane, children-inside-parents (WARN), links-resolve, dotted-keys-note (INFO) |
| `check_metrics.py --metrics FILE [--vocabulary vocabulary.md] [--max-series 1000] [--json]` | OTLP/JSON metrics export | input-not-empty, vocabulary-sane, names-in-vocabulary, name-shape, instrument-type, unit-present, labels-allowed, series-count, id-like-values, label-types, derived-metrics (WARN) |
| `check_logs.py --logs FILE [--vocabulary vocabulary.md] [--spans FILE] [--max-messages 200] [--json]` | JSON Lines logs | input-not-empty, vocabulary-sane, fields-present, level-values, message-templates, trace-correlation, trace-ids-in-spans (WARN), required-fields, forbidden-keys, secrets, field-types |

Every rule prints `PASS`, `FAIL`, `WARN`, `SKIP` or `INFO`, a count, up to
five offenders and a note. `--json` prints the same as one JSON object.

`vocabulary-sane` is the same rule in all three scripts. It fails the
vocabulary file itself, before any export is judged, when a table still holds
a template placeholder (a first cell starting with `<`), when a Where clause
matches none of the forms below, when a label lists no values or an attribute
lists some, when a type, kind, instrument or log level is not one of the
words the template allows. Each of those would otherwise make a later rule
check nothing and print `PASS`.

## Exit codes

`0` when no rule is `FAIL`. `1` when any rule is `FAIL`. `WARN` and `INFO`
never change the exit code; read them anyway. `2` is an argument error.

## How to produce each input

- **Spans.** Register `traces/recipes/python_file_exporter.py` as a span
  processor. It writes one JSON object per span, one per line. The checker
  also reads OTLP/JSON (`resourceSpans[]`, hex ids, integer enums, 64 bit
  numbers as strings) and the `ConsoleSpanExporter` output of
  opentelemetry-python (`context.trace_id` as `0x...`).
- **Metrics.** Use an exporter that writes OTLP/JSON: the OpenTelemetry
  Collector `file` exporter (`path:` required, `format: json` is the default,
  one JSON object per line), fed by `otlphttp` from the SDK. Verify the first
  line of the file starts with `{"resourceMetrics"`.
  `OTEL_METRICS_EXPORTER=console` redirected to a file is not OTLP/JSON; it is
  `MetricsData.to_json()` with `resource_metrics` and plain dict attributes.
  The checker reads that shape too, best effort, but the OTLP file is the
  reference.
- **Logs.** Point the ECS JSON handler from `logs/recipes/` at a file. One
  object per line with `@timestamp`, `log.level`, `message`, `trace.id` and
  `span.id`. Nested objects such as `{"log": {"level": "INFO"}}` are read as
  dotted keys. The shipped level is upper case `ERROR`, `WARN`, `INFO`,
  `DEBUG`; the checker compares case insensitively and reads `warning` as
  `warn`, but the vocabulary table spells it `warn`.
- **Vocabulary.** The project's `vocabulary.md`, filled from
  `core/vocabulary-template.md`. Tables are read by their header names, so
  keep the template's headers; extra columns, such as the Spans table's
  *Fails when*, and sections the checkers do not read, such as *Boundaries*
  or *Volume*, are ignored. A Spans row whose Name contains `*` is a glob,
  for a root span rule that builds the name, for example `tests/*::test_*`.
  In Correlation keys, Where is exactly one of `resource`, `every span`,
  `every span except <name> <name>` (names separated by spaces), `every log`,
  `every log inside a span`, or a span clause and a log clause joined by a
  comma, for example `every span except session.run, every log inside a span`.
  In Metrics, the Instrument cell is one bare word: `counter`,
  `updowncounter`, `histogram`, `gauge`, or `none` when the backend derives
  the metric; a metric whose row says `none` fails `instrument-type` if it
  arrives. The `## Links` table (`From span`, `To span`, `link.relation`) is
  read and exposed on the parsed vocabulary; no rule uses it yet. Forbidden
  entries ending in `.*` are prefixes; a Forbidden line with spaces in it is
  prose and is not an entry. Without a vocabulary the vocabulary rules print
  `SKIP` and say so, except `roots-are-units`, which then only counts the
  distinct root names and prints `INFO`, or `WARN` when there are no roots
  or more distinct names than `--max-name-cardinality`.

## Fixtures

`fixtures/` holds a passing and a failing export for each signal plus the
vocabulary they are checked against, all spelled as the running example in
`examples/test-harness.md`. `sh fixtures/run_fixtures.sh` runs all of them,
then pulls the golden trace, metric and logs out of each of the three
`examples/*.md` with `fixtures/extract_golden.py` and runs the three checkers
on them against the example's own vocabulary. It prints `HARNESS PASS` when
the good runs exit 0 and the bad ones exit 1. Run it once after copying the
folder somewhere new, and after editing an example.

`python3 fixtures/extract_golden.py <example.md> <outdir>` on its own writes
`vocabulary.md` (the fenced markdown block under the example's *The
vocabulary* heading), `spans.jsonl` (every JSON line with `span_id` and
`kind`), `metrics.json` (the fenced block that is one OTLP/JSON document) and
`logs.jsonl` (every JSON line with `message` and `log.level`) into `<outdir>`,
and exits 1 naming whatever it could not find.

## What you paste into your answer

Paste the full output of every checker you ran, then this sentence with the
blanks filled in:

`Checked <file> with <checker> against <vocabulary.md or "no vocabulary">: exit <0 or 1>, <n> FAIL, <n> WARN, <n> SKIP.`

If you could not run a checker, write which one and why, and do not say the
task is done.

## Backend note

The checkers judge OpenTelemetry names, what the SDK emitted. What the index
holds after the pipeline's renames differs per backend, and the vocabulary's
Backend spelling column records it from `backends/<backend>/mapping.md`. On
Elastic, span attributes that are not ECS fields are stored under `labels.*`
with dots replaced by underscores; the `dotted-keys-note` rule lists the keys
this applies to. Other backends: the verdicts do not change; the stored shape
is in `backends/<backend>/mapping.md` and the differences in
`backends/paradigms.md`.
