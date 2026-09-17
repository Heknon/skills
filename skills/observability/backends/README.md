# Backends

Three backends are documented, one folder each, with the same file names so
the router can say `backends/<backend>/<file>` without caring which one is in
use. They are three paradigms, not three spellings. `paradigms.md` answers
the questions that differ between them side by side. Read it once.

| Folder | Stack | Traces | Metrics | Logs | UI |
| --- | --- | --- | --- | --- | --- |
| `elastic/` | Elastic Stack 8.x | APM Server into `traces-apm*` | APM Server into `metrics-apm*` | APM Server into `logs-apm*` | Kibana APM app |
| `grafana/` | Grafana stack | Tempo | Prometheus or Mimir | Loki | Grafana |
| `victoria/` | Victoria stack | VictoriaTraces | VictoriaMetrics, vmagent | VictoriaLogs | Grafana and vmui |

## The same files in every folder

| File | Read it when |
| --- | --- |
| `overview.md` | you need the hops, where each signal lands, what a root span is called, how OTLP arrives, and how to read the running version |
| `mapping.md` | you need the exact stored name an attribute becomes, the spelling of a key, or the type a value will have |
| `screens.md` | you are asked to make a screen or panel show something, or to explain why it is empty |
| `queries.md` | you need a query to paste, in that stack's languages |
| `collector.md` | there is a Collector between the SDK and the stack, or the stack needs one to derive span metrics |
| `verification-ladder.md` | data is missing, wrong or duplicated, and you must find the hop where it stops |

Elastic has two files more: `queries-dsl.md` for Elasticsearch aggregations
and `elastic-agent.md` for APM Server under Fleet.

## This installation

Fill this block once and keep it current. A Query or Debug task reads it
first, then reads the running version again, every time.

```
backend folder:          <elastic | grafana | victoria>
components and versions: <fill, e.g. Elasticsearch 8.17.3, Kibana 8.17.3, APM integration 8.17.3>
                         <or Grafana 11.6, Tempo 2.7, Loki 3.4, Prometheus 3.2>
                         <or VictoriaMetrics 1.115, VictoriaLogs 1.20, Grafana 11.6>
collector in the path:   <yes | no>, <otelcol-contrib version | Alloy version>
span metrics derived by: <APM Server | Tempo metrics-generator | collector spanmetrics connector | nothing>
ui url:                  <fill>
verified on:             <date>
```

The `span metrics derived by` line is the one that changes the verdicts in
`metrics/derived-or-emitted.md`. Get it right before any metrics task.

## How to read the running version

Each `overview.md` has a table with one row per component, the endpoint or
command, and the field to read. For Elastic, the short form:

| Component | Command or place | Field to read |
| --- | --- | --- |
| Elasticsearch | `GET /` against the Elasticsearch URL | `version.number` |
| Kibana | `GET /api/status` against the Kibana URL | `version.number` |
| APM Server, standalone | `apm-server version` | the printed version |
| APM Server, under Elastic Agent | `elastic-agent version`, and Kibana **Integrations > Installed integrations > Elastic APM > Settings** | the agent version and the integration version |

## The version-stamp rule

From `SKILL.md`: read the version from the running system first, every time,
and compare it with the stamp at the top of the file you are about to use. If
the major version differs, stop and ask before trusting a field name. Each
file starts with a stamp line. That line is the contract.

Elastic 9.x may run in one of two modes. Classic APM mode keeps every field
name in `elastic/`. OTel-native mode, written by the EDOT Collector or the
Elasticsearch exporter in OTel mapping mode, stores span attributes under
`attributes.*` with dots preserved and no `labels.*` at all. The note "9.x
and EDOT differences" in `elastic/mapping.md` says how to tell.

## Never

- Never quote a field name from memory. Point at a row in the backend's
  `mapping.md`, or at the store's own schema API.
- Never use a field name, a query language or a screen name from one
  backend's folder while working on another.
- Never assume the version. The version endpoint costs nothing.
- Never mix two stored spellings of one key in one vocabulary.

## Stop and ask

- The installation block is empty and nobody can say which backend runs.
- The running major version differs from the stamp.
- The stack mixes folders, for example Tempo for traces and Elastic for
  logs. That is legitimate, and the vocabulary then names a backend per
  signal, but a person confirms it.
