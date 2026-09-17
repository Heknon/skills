# Metrics

Procedures and recipes for the `metric` verdict from `core/signal-choice.md`.
Target: opentelemetry-python 1.2x sending OTLP to Elastic Stack 8.x APM Server.

## Files

| File | Answers |
| --- | --- |
| `derived-or-emitted.md` | does Elastic already compute this from spans |
| `instrument-type.md` | counter, updowncounter, histogram or gauge; synchronous or observable |
| `labels.md` | which attributes may become metric labels, and how many series that makes |
| `units-and-buckets.md` | UCUM unit, histogram boundaries, temporality |
| `recipes/python_meter_setup.py` | `configure_metrics(...)`: MeterProvider, reader, OTLP exporter, Views |
| `recipes/python_instruments.py` | one instrument of each kind with vocabulary checked labels |

## Order for an Instrument task

1. Read `vocabulary.md` in the project. If the metric is already there, skip
   to step 5.
2. `derived-or-emitted.md`. A `derived` verdict ends the task: write the
   screen name into the vocabulary and stop.
3. `instrument-type.md`, then `labels.md`, then `units-and-buckets.md`. Write
   each verdict into the vocabulary as you go.
4. Stop and ask for any name or label the vocabulary lacks.
5. Copy `recipes/python_meter_setup.py` once per project, next to the tracing
   setup, and pass it the same `Resource`.
6. Copy the matching instrument from `recipes/python_instruments.py` into the
   module that holds the vocabulary strings. Change only what the top comment
   names.
7. Run with `console=True`, compare the output with the bottom comment of the
   recipe, then run the metrics checker in `checks/` on a real export and
   paste its output.

Every UNVERIFIED line in these files names a fact to confirm against the
running installation before relying on it.
