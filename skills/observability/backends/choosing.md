# Choosing a backend

**Verdict you produce:** one backend folder per signal, traces, metrics and
logs, with the reason in one sentence each, written into the *This
installation* block of `backends/README.md` and into the header of
`vocabulary.md`. Mixing is allowed per signal. Splitting one signal across
two stores is not.

Nobody chooses a stack from a feature list. They choose from facts about
their situation: what is already running, how much data there is, who will
query it, and how many hands there are to operate it. Answer the questions
with those facts, then read the verdict table. Do not argue with the table;
if your situation is not in it, stop and ask.

## What the four options are

| Option | What it is | Signals it holds | Span metrics derived by |
| --- | --- | --- | --- |
| **Elastic** | one product: Elasticsearch, Kibana, APM Server | traces, metrics, logs, in one store, with full text search over all of them | `APM Server` |
| **Grafana stack** | four products: Tempo, Prometheus or Mimir, Loki, Grafana | traces, metrics, logs, in three stores built for each | `Tempo metrics-generator` or `collector connectors`, once enabled |
| **Victoria stack** | VictoriaMetrics, VictoriaLogs, VictoriaTraces, Grafana on top | metrics first, logs second, traces newest | `collector connectors`, once enabled |
| **Prometheus alone** | one binary that scrapes and stores metrics | metrics only | `nothing`; there are no spans |

The last column is the value of the `span metrics derived by` line in
`backends/README.md`. What each of them derives, where the numbers land and
what is on by default is the first table of `paradigms.md`; this table does
not repeat it.

Prometheus alone is in the table on purpose. Many systems need metrics and
alerts and nothing else, and adding a trace store to them is cost without a
question to answer.

## Questions

Answer each with a number, a name or a yes. Write the answers down; the
verdict table reads them.

1. **What is already running and who operates it?** An installed and
   operated store beats a better one that nobody runs. Name the product, its
   version, and the number of people who can fix it at three in the morning.
2. **Which signal carries the questions people actually ask?** Look at the
   last ten questions asked in incidents. Count how many were answered by a
   trace, a metric, or a log search. The signal with the most is the one the
   store must be best at.
3. **How much data per day?** Spans per day, active time series, log bytes
   per day. Read them from the current system or estimate from the unit of
   work times its rate times spans per unit.
4. **How high is the cardinality?** The number of distinct label
   combinations you want to group by, from `core/naming-and-cardinality.md`.
   Under ten thousand series is small. Over a million is large.
5. **Do people need full text search over logs?** Free text, regular
   expressions over the message, "find every line containing this id" across
   a month. Yes or no.
6. **Do people need to go from a metric to the trace behind it?** A latency
   spike on a chart, click, the slow trace. That is exemplars. Yes or no.
7. **Is there a collector in the path, and will someone own its config?**
   Some stacks need one to have span metrics at all. Yes or no.
8. **How long must each signal stay queryable?** Days for traces, months for
   metrics, weeks for logs is common. Write the three numbers.
9. **What hardware and network?** Air gapped or not, one machine or a
   cluster, object storage available or only local disk.
10. **Pull or push?** Can the store reach the workloads to scrape them, or
    must the workloads push out? Batch jobs and short lived workers cannot
    be scraped.

## Verdict table

Read the rows in order. The first row whose condition is true names the
default. Then check the rows below it for a signal that should move.

| If | Then | Because |
| --- | --- | --- |
| Elastic is already running and operated (Q1) | Elastic for all three | the APM app derives span metrics and dependencies with no collector config, and one store means one query language and one set of hands |
| Nothing is running and the questions are mostly metrics and alerts (Q2), with no trace or log search need (Q5, Q6 no) | Prometheus alone | it is one binary, it scrapes, it alerts, and it has nothing to operate that you do not use |
| Nothing is running and the questions are mostly log search with free text (Q2, Q5 yes) | Elastic for logs; then Elastic for the rest unless Q4 or Q9 pushes metrics out | Elasticsearch is a full text index; Loki and VictoriaLogs index labels and fields and grep the rest, which is cheaper and slower for free text |
| Cardinality is large (Q4 over a million) or metrics retention is long (Q8) or hardware is tight (Q9) | Victoria for metrics, whatever holds traces and logs | VictoriaMetrics compresses better, holds more series per gigabyte of memory, and runs as a single binary; this is the case it exists for |
| People need metric to trace clicks (Q6 yes) and open source is a requirement | Grafana stack for metrics and traces | exemplars from Prometheus open in Tempo inside Grafana; Elastic does not do this through exemplars |
| Volume of spans is large (Q3) and traces must be cheap to keep (Q8) with object storage available (Q9) | Tempo for traces | Tempo stores traces in object storage with no index to feed, so cost tracks bytes, not documents |
| Workloads cannot be scraped (Q10 push) | any store with an OTLP receiver; not Prometheus alone unless through its OTLP receiver or a push gateway | the pull model is the one thing Prometheus alone does not bend on |
| The team is one person and the system is air gapped on one machine (Q1, Q9) | Victoria stack, or Elastic if it is already there | three single binaries and Grafana is the smallest surface that holds all three signals; one product you already run is smaller still |

## Why one over another, the cases people hit

- **Elastic over the Grafana stack** when the thing that matters most is
  that a screen exists without configuring anything. Services, transactions,
  dependencies, errors and correlations appear from the spans alone. The
  price is one store doing three jobs, memory per document, and field
  mappings that must be planned. `core/naming-and-cardinality.md` matters
  more here than anywhere.
- **Grafana stack over Elastic** when each signal is large enough to want
  its own store, when object storage is available and cost per byte matters,
  when TraceQL and PromQL are the languages people know, or when exemplars
  are the workflow. The price is four products, a collector or the
  metrics-generator that someone must configure before any APM screen
  exists, and label names rewritten into Prometheus form.
- **Victoria over Prometheus or Mimir** when series count or retention makes
  Prometheus swap, when one binary must do what a cluster did, or when you
  want the same PromQL with less memory. The price is a smaller ecosystem
  around it and a trace store that is new; read `backends/victoria/overview.md`
  for the current readiness statement before putting traces there.
- **Prometheus alone over everything** when the questions are "is it up,
  is it slow, is it full" about infrastructure and services you can scrape.
  The price is that the first "why was this one slow" question has no
  answer, and that is the moment to add Tempo beside it, not to replace it.
- **Loki or VictoriaLogs over Elasticsearch for logs** when logs are high
  volume, mostly filtered by a few labels and a time range, and read next to
  traces. The price is that free text over a month is a scan, not an index
  lookup.
- **Elasticsearch over Loki or VictoriaLogs for logs** when people search
  words, when the same store must answer analytics over log fields, or when
  the logs are the product's audit record. The price is the index, which is
  memory and disk per line.

## Mixing

A store per signal is normal. Tempo for traces beside Elastic for logs, or
Prometheus for metrics beside Elastic APM for traces, both work, because the
join between signals is the correlation keys from
`core/correlation-keys.md`, not the store. What breaks is the click from
one screen to another across products, which then needs a data source link
in Grafana or a URL template in Kibana. Write the join in the vocabulary
when signals live apart.

## Verdict

Write into `backends/README.md` under *This installation*:

```
traces:                  <elastic | grafana | victoria> because <one sentence from the table>
metrics:                 <elastic | grafana | victoria> because <one sentence>
logs:                    <elastic | grafana | victoria> because <one sentence>
span metrics derived by: <APM Server | Tempo metrics-generator | collector connectors | nothing>
```

These are the same lines, spelled the same way, as the *This installation*
block in `backends/README.md`; the same three signal lines go into the header
of `vocabulary.md`.

## Never

- Never choose by what is fashionable, by what a vendor page says, or by
  which name you recognise. Every row above is a fact about the situation.
- Never split one signal across two stores. Half the traces in Tempo and
  half in Elastic answers no question.
- Never run two metric stores for the same workloads. Pick one, migrate,
  turn the other off.
- Never put traces in a store whose docs call trace support preview or
  beta without a person accepting that in writing.
- Never choose Elastic for a metrics only need, or Prometheus alone for a
  trace need. Both fit the wrong shape.
- Never put configuration in the choice. The verdict names folders and
  reasons. Flags, keys and endpoints come later, copied from that folder's
  files, never from memory.

## Stop and ask

- The answers point at two rows with equal strength. Write both rows and
  the facts, and a person picks.
- Question 1 names a store that the team cannot operate. That is a staffing
  fact, not a technical one.
- The volume or cardinality numbers are guesses. Measure for a day first.

## Examples

| Situation | Verdict |
| --- | --- |
| Elastic already runs for logs, a test harness now needs traces | Elastic for all three; APM Server derives the screens for free |
| A Kubernetes platform team, metrics and alerts, no application tracing | Prometheus alone, add Tempo when the first trace question arrives |
| Ten million active series on one machine, air gapped | VictoriaMetrics for metrics; traces and logs wherever they already are |
| A product team wants latency chart to slow trace in one click, open source only | Grafana stack: Prometheus with exemplars, Tempo, Loki |
| Logs are the audit record and people search words across a quarter | Elasticsearch for logs, whatever the rest is |
