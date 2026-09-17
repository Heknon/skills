---
name: observability
description: Design, instrument, verify and debug traces, metrics and logs for any system, end to end from the OpenTelemetry SDK through the collector and Elastic APM to the Kibana screen. Use for every observability question, including which signal to emit, what a transaction or dependency is, how to name things, why data is missing in Kibana, and how to set up a new project's instrumentation. Written so the answer comes from a procedure and a check, not from judgment.
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
| **Query** | build a dashboard, a chart or a search | `backends/README.md`, then the backend's `kibana-screens.md` and `queries.md` |
| **Debug** | find out why data is missing, wrong or duplicated | `backends/elastic/verification-ladder.md`, then the hop it fails at |
| **Choose** | pick between two approaches | the one procedure that names the dilemma; the list is below |

Every task that changes code ends with the matching `checks/` script run on a
real export, and its output pasted into your answer. A task is not done until
the checker passes. If a checker cannot be run, say so and say why.

## Where each dilemma is answered

| Dilemma | Procedure |
| --- | --- |
| What is the transaction, the thing to aggregate over | `core/unit-of-work.md` |
| A question with a number in it, and which measurement answers it | `core/question-to-measurement.md` |
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
unit of work, the correlation keys, every span name, every attribute key, every
metric name and label, and every log field, as exact strings.

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
7. **A value goes to the backend as the type the vocabulary says.** Attribute
   types are fixed by the first document that arrives. Ids are strings, always.
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

A recipe is a complete file that runs as it is. Copy it whole, rename what the
top comment says to rename, and change nothing else the first time. Each
recipe ends with the shape of data it produces. Compare your export with that
shape before you change anything.

## The backend

`backends/README.md` says which backend this installation runs and which
version. Read the version from the running system first, every time, and
compare it with the stamp on the file you are about to use. If the major
version differs, stop and ask before trusting a field name.

## What you say when you finish

State the verdicts you wrote. Paste the checker output. Name anything you
could not verify. Do not describe what you would have done with more access.
