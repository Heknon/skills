# Service, dependency, or attribute

**Verdict you produce:** for a thing the code talks to or talks about, one of
`service`, `dependency` or `attribute`. A service gets a `service.name` value
in the vocabulary's `Correlation keys`. A dependency gets a `peer.service`
value, or a `db.system` or `messaging.system` value, in the `Destination
attribute` column of `Spans`. An attribute gets a row in `Span attributes`.

The backend draws a node on its service map and a row on its dependencies
screen for every distinct destination value that arrives. Nothing is
registered anywhere. So the values that reach the destination field decide
what the screen looks like, and an unbounded value there is a screen with ten
thousand nodes. Which stored field that is, per backend, is in
`backends/<backend>/mapping.md`.

## Questions

1. **Does it run as its own process and emit its own telemetry?** It has its
   own TracerProvider with its own `service.name`, and a `traceparent` header
   arrives at it. Yes: **service**. No: go on.
2. **Does this code call it, over a socket, a driver, a queue or a
   controller, in a span that starts and ends around the call?** Yes: go to 3.
   No: **attribute**. A thing that is only mentioned is a fact about a span.
3. **Can you list every value its name will take, today, in the vocabulary?**
   Yes: **dependency**. Write the exit span with `SpanKind.CLIENT` or
   `SpanKind.PRODUCER` and one of:
   - `peer.service=<logical name of the callee>` for anything without a
     better convention. The entity definition name is the example: bounded,
     chosen by the customer but from a short list, and each definition is a
     thing a person would call "what failed".
   - `db.system=<database product>` for a database. Add `server.address`.
   - `messaging.system=<broker product>` for a queue. Add
     `messaging.destination.name`.
   No, the set of names grows with traffic or with objects: **attribute**.
   Put the name in a span attribute on an exit span whose `peer.service` is
   the *kind* of thing, not the instance.
4. **Is the thing you decided is a dependency also a service?** Both can be
   true. The caller's exit span gives it a dependencies row and a node from
   that caller's side; its own telemetry gives it a service node; the
   `traceparent` header joins the two so the map draws one edge to the
   service node instead of a dangling node. Keep `peer.service` equal to
   the callee's `service.name` so they join.

## Verdict

Write into `vocabulary.md`, `Spans` table:

```
| <noun.verb> | CLIENT | no | <attribute keys> | peer.service | <what a failed call looks like on this span> |
```

with the allowed values of `peer.service` as a `label` row in
`Span attributes`, or for a service, `Correlation keys`:

```
| service.name | string | resource | service.name | <fixed value for this process> |
```

## On Elastic

APM Server 8.x, from `elastic/apm-data`, `input/otlp/traces.go`:

- `SpanKind.SERVER`, `SpanKind.CONSUMER`, or any root span becomes a
  **transaction**. Any other kind becomes a **span**.
- `peer.service` on a span is copied to `span.destination.service.name`,
  `span.destination.service.resource` and `service.target.name`.
- `db.system` sets `span.subtype=<db.system>` and the destination name;
  `messaging.system` sets `span.subtype=<messaging.system>` likewise.
  UNVERIFIED: that `span.type` becomes `db` and `messaging` for those two.
  UNVERIFIED: the resulting `span.destination.service.resource` for a span
  with `db.system` and no `peer.service`; the agent spec says
  `<type>/<name>`, for example `postgresql/mydb`.
- A `CLIENT` span with only `peer.service` gets `span.type=unknown`. It still
  appears in Dependencies. Its map icon is the generic one.
- `server.address`, and the older `net.peer.name`, set `destination.address`.
- The Dependencies screen and the service map are keyed by
  `span.destination.service.resource`. APM Server rolls up metrics per
  distinct value of that field. Each distinct value is one node.
- Attributes that map to none of these are `labels.*`, dots to underscores.

## Other backends

Other backends: the verdicts do not change; the stored shape is in
backends/<backend>/mapping.md and the differences in backends/paradigms.md.

## Never

- Never one service per customer-defined object, per entity instance, per
  worker or per test. A service is a deployable piece of code.
- Never put a run id, a branch, a worker id or an environment id in
  `service.name`. Those are correlation keys.
- Never let `peer.service` take an instance id, a host name with a port, a
  URL or anything from question 3's "no" branch. One value per distinct
  string is one mapping and one node; that is a mapping explosion and a map
  nobody can read.
- Never set `db.system` or `messaging.system` on a call that is not a
  database or a broker to get a nicer icon.
- Never omit the destination attribute on a `CLIENT` or `PRODUCER` span. With
  no destination there is no dependency, invariant 4.
- Never use `SpanKind.CLIENT` on a span that stays inside the process.

## Stop and ask

- The callee is a service but its `service.name` is not known to this code,
  so `peer.service` cannot equal it. A person aligns the two names.
- The set of callee names is bounded today but a customer can add to it. Say
  how many there are and how fast it grows; a person decides whether it stays
  a dependency or becomes an attribute on a generic `peer.service`.
- A thing is called both in process and over the network depending on
  configuration. Two span names, or one with a mode attribute; a person picks.

## Examples

| Thing | Verdict | Exact strings |
| --- | --- | --- |
| The pytest worker process | service | `service.name=sahara-harness` |
| An entity definition, such as `tank` | dependency | `entity.create`, `CLIENT`, `peer.service=tank` |
| An entity instance `tank-7` in environment `environment-3` | attribute | `sahara.entity.id=environment-3/tank-7/1` on the `entity.create` span |
| The result store behind the harness, if it is Postgres | dependency | `db.system=postgresql`, `server.address=<host>` |
| The APM Server, Tempo or VictoriaTraces itself | neither, it is the pipeline | do not instrument the exporter |
| A customer-named controller method | attribute | `sahara.entity.controller.method=<method name>` on the `entity.controller` span, whose `sahara.entity.operation` label is `controller` |
| A second instrumented service the harness calls over HTTP | service and dependency | its own `service.name=sahara-api`; the caller's `peer.service=sahara-api` |
