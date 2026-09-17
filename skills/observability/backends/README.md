# Backends

One backend is documented: Elastic Stack 8.x, receiving OTLP from the
OpenTelemetry SDK, through an optional OpenTelemetry Collector, into APM Server
running under Elastic Agent, stored in Elasticsearch data streams, read in the
Kibana APM app. Every file under `backends/elastic/` is written for that path.

## This installation

Fill this block once and keep it current. A Query or Debug task reads it
first, then reads the running version again, every time.

```
backend name:            Elastic Stack
major version:           8
exact version:           <fill, e.g. 8.17.3>
apm server runs as:      <Fleet-managed under Elastic Agent | standalone binary>
collector in the path:   <yes | no>
kibana url:              <fill>
elasticsearch url:       <fill>
default namespace:       default
verified on:             <date>
```

## How to read the running version

Read all three. They must agree on the major version.

| Component | Command or place | Field to read |
| --- | --- | --- |
| Elasticsearch | `GET /` against the Elasticsearch URL | `version.number` |
| Kibana | `GET /api/status` against the Kibana URL | `version.number` |
| Kibana, in the UI | UNVERIFIED: the Help menu, the question mark icon at the top right, shows the version. Prefer `/api/status`. | |
| APM Server, standalone | `apm-server version` | the printed version |
| APM Server, under Elastic Agent | `elastic-agent version` on the host, and in Kibana **Integrations > Installed integrations > Elastic APM > Settings** | the agent version, and the integration version on the Settings tab |
| Elastic Agent state | `elastic-agent status` | the status of each process, including `apm-server` |

`elastic-agent inspect` prints the running agent configuration, which includes
the APM integration policy that reached the host.

## The version-stamp rule

From `SKILL.md`: read the version from the running system first, every time,
and compare it with the stamp at the top of the file you are about to use. If
the major version differs, stop and ask before trusting a field name. Each
file under `elastic/` starts with a `verified against:` line. That line is the
stamp.

A 9.x installation may run in one of two modes. Classic APM mode keeps every
field name in these files. OTel-native mode, written by the EDOT Collector or
the Elasticsearch exporter in OTel mapping mode, stores span attributes under
`attributes.*` with dots preserved and no `labels.*` at all. The note
"9.x and EDOT differences" in `apm-server-mapping.md` says how to tell.

## Files

| File | Read it when | Owner of the facts |
| --- | --- | --- |
| `elastic/overview.md` | you need to know which hop a signal passes, which data stream it lands in, or why one OTLP span became a transaction and another a span | this folder |
| `elastic/apm-server-mapping.md` | you need the exact field name an attribute becomes, the spelling of a label key, or the type a value will have in the index | this folder |
| `elastic/kibana-screens.md` | you are asked to make a Kibana screen show something, or to explain why a screen is empty | this folder |
| `elastic/queries.md` | you need a KQL or Elasticsearch DSL query to paste | this folder |
| `elastic/collector.md` | there is a Collector between the SDK and APM Server | another writer |
| `elastic/elastic-agent.md` | you configure or inspect APM Server under Elastic Agent | another writer |
| `elastic/verification-ladder.md` | data is missing, wrong or duplicated, and you must find the hop where it stops | another writer |

Read `overview.md` before the other files the first time. After that, go
straight to the file the task names.

## Never

- Never quote a field name from memory. Point at a row in
  `apm-server-mapping.md`, or at the mapping API output.
- Never assume the version. `GET /` costs nothing.
- Never mix the classic `labels.*` spelling and the OTel-native
  `attributes.*` spelling in one vocabulary.

## Stop and ask

- The running major version is not 8.
- The three version reads disagree on the major version.
- The installation is 9.x and you cannot tell which mode it runs in.
