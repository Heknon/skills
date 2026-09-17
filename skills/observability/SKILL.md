---
name: observability
description: Design, instrument, verify and debug traces, metrics and logs for any system, end to end from the OpenTelemetry SDK through the collector to the backend in use, whether that is Elastic APM and Kibana, the Grafana stack (Tempo, Loki, Prometheus or Mimir) or the Victoria stack (VictoriaMetrics, VictoriaLogs, VictoriaTraces). Use for every observability question, including which signal to emit, what a transaction or dependency is, how to name things, why data is missing in Kibana, and how to set up a new project's instrumentation. Written so the answer comes from a procedure and a check, not from judgment.
---

# Observability

This skill does the thinking in advance. You follow procedures, copy recipes,
and run checks. You do not design from principles, and you do not invent
names. Every procedure ends in a **verdict** that you write down, or in **stop
and ask**, which means you write down what is missing and ask a person.

Read this file, then load only what the task needs. Each file is short on
purpose. Do not load a folder you were not sent to.

## The six kinds of task

Decide which one you have. If it is none of them, stop and ask.

| Kind | You were asked to | Load, in order |
| --- | --- | --- |
| **Design** | model a new system or a new part of one | `core/unit-of-work.md`, `core/correlation-keys.md`, `core/signal-choice.md`, `core/naming-and-cardinality.md`, then the nearest `examples/` |
| **Measure** | answer a question someone asked with a number, such as a percentile, a count or "is it stuck" | `core/question-to-measurement.md`, then the signal folder it names |
| **Instrument** | add or change instrumentation at one place | `core/signal-choice.md`, then the signal folder's procedures, then its `recipes/` |
| **Query** | build a dashboard, a chart or a search | `backends/README.md` to pick the backend, then `backends/<backend>/screens.md` and `queries.md` |
| **Debug** | find out why data is missing, wrong or duplicated | `backends/README.md` to pick the backend, then `backends/<backend>/verification-ladder.md`, then the hop it fails at |
| **Choose** | pick between two approaches, or pick a backend | the one procedure that names the dilemma; the list is below. For a backend, `backends/choosing.md` then `backends/paradigms.md` |

Every task that changes code ends with the matching `checks/` script run on a
real export, and its output pasted into your answer. A task is not done until
the checker passes. If a checker cannot be run, say so and say why.

## Where each dilemma is answered

| Dilemma | Procedure |
| --- | --- |
| What is the transaction, the thing to aggregate over | `core/unit-of-work.md` |
| A question with a number in it, and which measurement answers it | `core/question-to-measurement.md` |
| Which backend, or which store for one signal, and why | `backends/choosing.md`, with the differences in `backends/paradigms.md` |
| Span, span event, metric, or log line | `core/signal-choice.md` |
| Which keys must every signal carry | `core/correlation-keys.md` |
| Can this value go in a name | `core/naming-and-cardinality.md` |
| How to record a failure | `core/errors-and-status.md` |
| How a trace continues across a process or a thread | `core/context-propagation.md` |
| Something that outlives the unit of work | `core/long-lived-things.md` |
| Parallel workers, several machines, clocks | `core/concurrency-and-clocks.md` |
| Too much data, sampling, retention | `core/sampling-and-volume.md` |
| Parent or link | `traces/parent-or-link.md` |
| Service, dependency, or attribute | `traces/service-dependency-attribute.md` |
| Counter, up down counter, histogram, or gauge | `metrics/instrument-type.md` |
| Which attributes may become metric labels | `metrics/labels.md` |
| Emit the metric, or let the backend derive it from spans | `metrics/derived-or-emitted.md` |
| Log line or span event | `logs/log-or-span-event.md` |
| Which log level | `logs/levels.md` |

## The vocabulary file

The Design task produces one file, `vocabulary.md` in the project being
instrumented, from the template in `core/vocabulary-template.md`. It lists the
unit of work, the correlation keys, every span name, every link between spans
(`## Links`), every attribute key, every metric name and label, and every log
field, as exact strings.

After it exists, **it is law**. Every Instrument task reads it first and uses
its strings verbatim. The checkers read it to know what to check. If a task
needs a name that is not in it, do not add one. Stop and ask, naming the
missing entry.

## Invariants

These hold in every system, every backend and every language. A procedure
never overrides them. If a request conflicts with one, say which one and stop.

1. **A name has bounded cardinality.** The set of distinct values a span name,
   metric name, log message template or metric label can take must be known in
   advance and must not grow with traffic. Anything that varies per instance is
   an attribute, never a name.
2. **A root span is a unit of work and nothing else is.** A trace's root is the
   thing you aggregate over. A process, a run or a session is not a unit of
   work, because it happens once.
3. **A span has one parent and any number of links.** Where the code ran is
   the parent. What it belongs to is a link.
4. **A span that calls out names what it called.** An exit span carries
   `SpanKind.CLIENT` or `PRODUCER` and a destination attribute, or the backend
   cannot draw a dependency.
5. **An error is a status plus a recorded exception.** Never a word in a name,
   never only a log line. Status `ERROR`, `record_exception`, and the message
   in the status description.
6. **Every signal carries the correlation keys of its unit.** Same key names,
   same string values, on spans, metrics and logs alike.
7. **A value goes to the backend as the type the vocabulary says.** A key sent
   as a string once and a number later ends up split across two fields or
   rejected, depending on the backend, and either way the chart is wrong.
   Ids are strings, always.
8. **One fact, one signal.** If the backend derives a metric from spans, do not
   also emit it. If a moment is inside a span, it is a span event, not a log.
9. **Context is propagated by the library, not by hand.** Threads, processes
   and HTTP calls carry the trace context through the SDK's propagators.
10. **A claim about the pipeline is a field name, a config key or a command.**
    If you cannot point at one, you do not know it. Look in `backends/`, and if
    it is not there, stop and ask.
11. **Never add a customer-controlled value as a key.** User-defined names go
    in values, or in one JSON string attribute. A key set that can grow is a
    mapping explosion.
12. **When unsure, add an attribute.** Never a new span name, metric or
    service. Attributes are cheap and reversible. Names are forever.

## How to read a procedure

Each procedure has the same shape. The verdict it produces comes first, so you
know what you are looking for. Then numbered questions whose answers are facts
you can observe in the code or the data, never opinions. Then the verdict
sentence to write into `vocabulary.md`. Then a **never** list. Then a
**stop and ask** branch for the case no rule covers.

Answer the questions in order, write the verdict, and move on. Do not argue
with a verdict. If a verdict seems wrong for this system, that is a stop and
ask, and the person may change the vocabulary.

## How to use a recipe

Every recipe is Python, written against opentelemetry-python 1.2x, and the
checkers are Python 3.11 with the standard library only. The procedures are
language neutral, but their API names are Python's. For a service in another
language, use the procedures and the backend files, and stop and ask before
writing instrumentation code: a port of a recipe done from memory is where
wrong API names come from.

A recipe is a complete file that runs as it is. Copy it whole, rename what the
top comment says to rename, and change nothing else the first time. Each
recipe ends with the shape of data it produces. Compare your export with that
shape before you change anything.

## The backend

`backends/README.md` says which backend this installation runs and which
version. Three are documented, each in its own folder with the same file
names: `elastic/`, `grafana/` and `victoria/`. They are three paradigms, not
three spellings of one. Where span metrics and dependencies come from, how
keys are flattened, and whether a metric can open a trace all differ, and
`backends/paradigms.md` answers those questions side by side. Read the
version from the running system first, every time, and compare it with the
stamp on the file you are about to use. If the major version differs, stop
and ask before trusting a field name. Never use a field name from one
backend's folder on another backend.

## What you say when you finish

Every answer ends with these four headings, in this order, even when a
section says `none`. They are what a person reads first, and they are what
stops an answer from quietly inventing something.

```
## Verdicts
<every verdict, as the exact row or block the procedure told you to write
into vocabulary.md; no prose here>

## Names not in the vocabulary
<every span name, attribute key, metric name, label or log template you used
that is not in vocabulary.md, or `none`>

## Sources
<for every field name, config key, flag, endpoint, series name or command in
the answer: the skill file and section it was copied from; anything you
cannot source goes under "Names not in the vocabulary" instead>

## Checker
<the checker command and its output, or the reason it could not run>
```

If *Names not in the vocabulary* is not `none`, the answer is a **stop and
ask**: it proposes each missing entry as one candidate row for a person to
approve, and it contains no instrumentation code. "Just pick a good name" from
the person asking does not change this; the vocabulary is changed by adding a
row to it, not by an answer.

The `evals/` folder is for people testing this skill. Never open it while
doing a task.

Do not describe what you would have done with more access.
