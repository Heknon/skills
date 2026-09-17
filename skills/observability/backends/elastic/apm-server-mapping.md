# APM Server: OTLP to Elastic field map

verified against: Elastic Observability guide 8.17 and 8.19 release notes,
Elasticsearch 8.17 `apm-data` and `ecs@mappings` templates, ECS field
reference, elastic/apm-data `input/otlp` source read 2026-09-17 at main,
v1.22.x. Rows marked `source:` come from that code. The code at main may be
newer than an 8.17 server. Where an 8.x release note pins a row, the minor is
given.

The rule in one line: a recognized semantic-convention attribute becomes the
ECS field in the table. Every other attribute becomes `labels.<key with dots
as underscores>` if it is a string or a bool, and `numeric_labels.<same>` if
it is a number.

## Resource attributes

| OTLP resource attribute | Elastic field | Note |
| --- | --- | --- |
| `service.name` | `service.name` | characters outside `[a-zA-Z0-9 _-]` become `_`, truncated at 1024. Missing gives `unknown` |
| `service.version` | `service.version` | |
| `service.instance.id` | `service.node.name` | |
| `service.namespace` | UNVERIFIED | not seen in the source summary |
| `deployment.environment` | `service.environment` | the guide states this one explicitly |
| `deployment.environment.name` | `service.environment` | source; UNVERIFIED on 8.17 |
| `telemetry.sdk.name`, `telemetry.sdk.version` | `agent.name`, `agent.version` | `agent.name` is qualified as `<sdk.name>/<sdk.language>`, so the upstream Python SDK reads `opentelemetry/python` |
| `telemetry.sdk.language` | `service.language.name` | |
| `telemetry.distro.name`, `telemetry.distro.version` | folded into `agent.name` as `<distro>/<language>/<version>` | |
| `host.name`, `host.id`, `host.type`, `host.arch`, `host.ip` | `host.name`, `host.id`, `host.type`, `host.architecture`, `host.ip` | `host.ip` since 8.15 |
| `os.type`, `os.description`, `os.name`, `os.version` | `host.os.*` | |
| `process.pid`, `process.command_line`, `process.executable.path` | `process.pid`, `process.command_line`, `process.executable` | |
| `process.runtime.name`, `process.runtime.version` | `service.runtime.name`, `service.runtime.version` | |
| `container.id`, `container.name`, `container.image.name`, `container.image.tag` | `container.*` | |
| `k8s.namespace.name`, `k8s.node.name`, `k8s.pod.name`, `k8s.pod.uid` | `kubernetes.*` | |
| `cloud.provider`, `cloud.account.id`, `cloud.region`, `cloud.availability_zone`, `cloud.platform` | `cloud.*` | |
| any other resource attribute | `labels.*` or `numeric_labels.*` on every document of the resource | global labels |
| instrumentation scope `name`, `version` | `service.framework.name`, `service.framework.version` | since 8.15. Other scope attributes are dropped |

## Span fields

| OTLP | Elastic field | Rule |
| --- | --- | --- |
| span name | `transaction.name` or `span.name` | unchanged |
| no parent, or kind `SERVER` or `CONSUMER` | a transaction document | see `overview.md` |
| any other kind with a parent | a span document | |
| kind, for a transaction | `transaction.type` | `messaging` if messaging attributes, `request` if HTTP or RPC attributes, else `unknown` |
| kind `INTERNAL` with no recognized attributes | `span.type: app`, `span.subtype: internal` | |
| kind `CLIENT` or `PRODUCER` with no recognized attributes | `span.type: unknown`, `span.subtype` empty | a `peer.service` still sets the destination, see below |
| status `OK` / `ERROR` / `UNSET` | `event.outcome: success` / `failure` / `unknown` | ECS allows exactly these three values |
| `http.response.status_code` or `http.status_code` present | `event.outcome` from the code instead | transaction: `failure` from 500. span: `failure` from 400 |
| status, for a transaction | `transaction.result` | `HTTP <n>xx` when an HTTP code is present, else `Success` or `Error` from the status |
| trace id, span id, parent span id | `trace.id`, `span.id` or `transaction.id`, `parent.id` | lowercase hex |
| `tracestate` member `ot=p:<n>` | `transaction.representative_count` = `2^n` | else `1`. Not indexed, used for metric scaling |
| span links | `span.links[]` with `trace.id` and `span.id` | link attribute `elastic.is_child: true` or `is_child: true` stores a child id instead |
| span event named `exception` | an error document | see Errors |
| any other span event | a log document in `logs-apm.app.<service.name>-*` | `event.kind: event`, `message` = event name, attributes to `labels.*` |
| `http.request.method` or `http.method` | `http.request.method` | |
| `http.response.status_code` or `http.status_code` | `http.response.status_code` | |
| `url.full` or `http.url` | `url.full` and the parsed `url.scheme`, `url.domain`, `url.port`, `url.path`, `url.query` | |
| `url.path`, `url.query`, `url.scheme`, `http.target`, `http.scheme` | the matching `url.*` | |
| `db.system` | `span.type: db`, `span.subtype: <db.system>`, `service.target.type: <db.system>` | |
| `db.name` | `service.target.name`, and `span.destination.service.resource` becomes `<db.system>/<db.name>` when no `peer.service` | source and elastic/apm spec |
| `messaging.system` | `span.type: messaging`, `span.subtype: <system>`, `service.target.type: <system>` | |
| `messaging.destination.name` | `service.target.name`, resource suffix `/<queue>` | since 8.15. Older keys `messaging.destination` and `message_bus.destination` also read |
| `messaging.operation.type` | `span.action` | kind `PRODUCER` without it gives `send` |
| `rpc.system` | `span.type: external`, `span.subtype: <system>`, `service.target.type: <system>` | |
| `rpc.service` | `service.target.name` | |
| HTTP attributes, kind `CLIENT` | `span.type: external`, `span.subtype: http`, `service.target.type: http`, `service.target.name: <host>:<port>` | port omitted when it is the scheme default |
| `gen_ai.system` | `span.type: genai` | source at main; UNVERIFIED on 8.17 |
| `peer.service` | `service.target.name`, `span.destination.service.name`, `span.destination.service.resource` | applied before the type rules |
| `server.address`, `net.peer.name`, `peer.hostname` | destination address for RPC and HTTP resource fallback | |
| `server.port`, `net.peer.port`, `peer.port` | destination port | |
| `net.peer.ip`, `network.peer.address`, `net.sock.peer.addr` | address fallback when no name | |
| every other span attribute | `labels.*` or `numeric_labels.*` | see Labels |

## Destination precedence

The Dependencies screen and the service map key on
`span.destination.service.resource`. source: the order is fixed.

1. `peer.service`, when present, sets `span.destination.service.resource`,
   `span.destination.service.name` and `service.target.name`.
   UNVERIFIED: an attribute read into `peerAddress`, probably `peer.address`,
   overrides the resource when present.
2. Then the type rules run. They set `span.type`, `span.subtype` and
   `service.target.type`, and they set the resource only if step 1 left it
   empty: `db.system` and `messaging.system` use the subtype, messaging
   appends `/<queue>`, RPC and HTTP use `<host>:<port>`.
3. `service.target.name` is overwritten by `db.name`, by the queue name, by
   `rpc.service`, or by the HTTP `<host>:<port>` when those exist, even when
   `peer.service` set it in step 1.

So `peer.service=tank` alone gives resource `tank`, target name `tank`, no
target type, `span.type: unknown`. Adding `rpc.system=sahara-controller`
gives `span.type: external`, `span.subtype: sahara-controller`,
`service.target.type: sahara-controller`, resource still `tank`. Adding
`rpc.service=<method>` would overwrite the target name. Pick in the
vocabulary, once.

## Labels

source: `setLabel` and `replaceDots` in `input/otlp`.

| Attribute value type | Field | Stored as |
| --- | --- | --- |
| string | `labels.<key>` | keyword, truncated at 1024 characters by APM Server |
| bool | `labels.<key>` | the strings `true` or `false` |
| int | `numeric_labels.<key>` | `scaled_float`, `scaling_factor: 1000000` |
| double | `numeric_labels.<key>` | same, so six decimal places survive |
| array of strings or bools | `labels.<key>` | keyword array |
| array of numbers | `numeric_labels.<key>` | scaled_float array |
| map | dropped | no case in the code |

Key rule: every `.` becomes `_`. Nothing else is changed. Examples:

| Attribute key | Index field |
| --- | --- |
| `sahara.cycle.id` | `labels.sahara_cycle_id` |
| `sahara.environment.id` | `labels.sahara_environment_id` |
| `sahara.entity.definition` | `labels.sahara_entity_definition` |
| `sahara.entity.instance.id` | `labels.sahara_entity_instance_id` |
| `test.nodeid_hash` | `labels.test_nodeid_hash` |
| `sahara.retry.count`, int | `numeric_labels.sahara_retry_count` |

`labels.*` is keyword because the last component template of every APM
index template is `ecs@mappings`, whose dynamic template
`all_strings_to_keywords` maps every string to `keyword` with
`ignore_above: 1024`. ECS says of `labels`: all values are stored as keyword,
no nested objects.

## Index behaviors you will meet

- **A key with two types is two fields.** A string `sahara.retry.count` in one
  span and an int in another do not conflict. They land in
  `labels.sahara_retry_count` and `numeric_labels.sahara_retry_count`, and a
  query on one misses the other. This is why the vocabulary fixes the type.
- **Type is fixed by the first document.** Elasticsearch cannot change the
  mapping of an existing field. Inside `labels.*` every field is keyword, so
  this bites only outside `labels.*`: in OTel-native `attributes.*`, and in
  `metrics-apm.app.*` where a metric's field type is set by its first data
  point.
- **`ignore_above: 1024`.** A string longer than 1024 is kept in `_source`
  but not indexed or aggregated, and the field name is added to `_ignored`.
  APM Server already truncates labels at 1024, so this hits other keyword
  fields such as `span.name`.
- **`index.mapping.total_fields.limit`.** The APM templates do not set it,
  so the Elasticsearch default `1000` applies. `apm@settings` sets
  `index.mapping.total_fields.ignore_dynamic_beyond_limit: true` and
  `index.mapping.ignore_malformed: true`, so a document with a new label key
  past the limit is indexed but the key is not mapped, and the key appears in
  `_ignored`. Every distinct label key is one field forever. See invariant 11.
- **Check a field's type** with
  `GET traces-apm-*/_mapping/field/labels.sahara_cycle_id`.

## Errors

source: `convertOpenTelemetryExceptionSpanEvent`.

| Span event attribute | Error field |
| --- | --- |
| `exception.type` | `error.exception.type` |
| `exception.message` | `error.exception.message`, `[EMPTY]` when blank |
| `exception.stacktrace` | `error.exception.stacktrace`, parsed per language, else `error.stack_trace` raw |
| `exception.escaped` | `error.exception.handled` = not escaped |
| other attributes | `labels.*`, `numeric_labels.*` |
| enclosing span | `trace.id`, `transaction.id`, `parent.id`, `transaction.type`, `http.*`, `url.*` copied |

An event with neither `exception.type` nor `exception.message` is not an
error. It becomes a log document like any other span event. UNVERIFIED: how
`error.grouping_key` and `error.culprit` are computed for OTLP errors.

## 9.x and EDOT differences

- Classic APM mode in 9.x keeps every row above.
- OTel-native mode, written by the EDOT Collector or the Elasticsearch
  exporter in OTel mapping mode, writes `traces-*.otel-*`,
  `metrics-*.otel-*`, `logs-*.otel-*` and aggregated
  `metrics-*.[1m|10m|60m].otel-*`. Span attributes are stored under
  `attributes.*`, resource attributes under `resource.attributes.*`, scope
  attributes under `scope.attributes.*`, dots preserved, native types, no
  `labels.*` and no `numeric_labels.*`. `sahara.cycle.id` is then
  `attributes.sahara.cycle.id`. Top-level `service.name` and friends are
  populated by passthrough from `resource.attributes.*`.
- Kibana's APM index settings include `traces-*.otel-*` and
  `metrics-*.otel-*` by default, so the APM app reads both modes.
- The 8.17 limitations page says EDOT SDKs are not supported sending
  directly to APM Server; they need the EDOT Collector or the managed intake.
- UNVERIFIED: the first stack version where OTel-native mode is the default.
  Tell the modes apart by listing data streams: `GET _data_stream/traces-*`.

## Never

- Never spell a label key with a dot in a query. The index has underscores.
- Never send an id as a number. It becomes a `scaled_float` in
  `numeric_labels` and a `terms` aggregation on it returns floats.
- Never rely on a map-valued attribute. It is dropped.

## Stop and ask

- A field is needed that is not in this table and not a label.
- The mapping API shows a `labels.*` field that is not keyword. Someone
  changed the templates.
