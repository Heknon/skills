# Unit of work

**Verdict you produce:** the name of the thing that becomes a root span, which
Elastic calls a transaction and Tempo and Jaeger call a trace root, and the attribute that identifies one instance of it.
Both go into `vocabulary.md` under *Unit of work*.

Everything the backend aggregates, latency distribution, failure rate,
throughput, correlations, is computed per unit of work. Choose it wrong and
every screen is empty or meaningless. A pytest session as the only transaction
is the classic wrong choice: it happens once per run, so there is nothing to
aggregate.

## Questions

List every thing that happens in the system. For each one, answer with a fact.

1. **Does it happen many times per run, or once?** Count. Once means it is not
   a unit.
2. **Does it have the same name every time it happens?** The name must be
   knowable before it runs, such as a route, a job type, a test function. If
   the only name you can give it contains an id, a timestamp or a parameter
   value, it does not have a stable name yet. Go to
   `core/naming-and-cardinality.md` to find the stable part, then come back.
3. **Does it start and end inside one process?** If it crosses processes, the
   unit is the part inside the first process, and the rest continues it through
   `core/context-propagation.md`.
4. **Would a person name it when asked "what failed"?** A request, a message,
   a test, a batch item. Not a thread, not a fixture, not a database call.

A thing with yes to 1, 2, 3 and 4 is a candidate.

## Choosing among candidates

5. **Do the candidates nest?** For example a batch contains items, a test
   session contains tests. The unit is the **innermost** candidate that still
   passes question 4. The outer ones become roots of their own traces, linked
   from the inner ones. They are not parents. See `traces/parent-or-link.md`.
6. **Are there two candidates that do not nest?** For example an HTTP request
   and a background job in the same service. Then there are two units. Write
   both, with a `type` that tells them apart, such as `request` and `job`.

## Verdict

Write into `vocabulary.md`:

```
unit: <what it is, one noun>
root span name: <the stable name rule, from naming-and-cardinality>
instance key: <attribute key holding the id of one occurrence>
outer roots: <things that contain the unit and get their own linked root, or none>
```

## Never

- Never choose the process, the run, the session or the deployment. They
  happen once.
- Never choose something whose name you cannot write down before it runs.
- Never make the outer thing the parent of the unit. A trace with thousands of
  transactions in it is unreadable and slow to load.
- Never have a unit with no instance key. Without an id you cannot open one
  occurrence from a chart.

## Stop and ask

- Nothing passes questions 1 to 4. The system may have no natural unit yet,
  such as a daemon that only loops. A person decides what to measure.
- Two people would name different things for question 4. Write both and ask.

## Examples

| System | Unit | Instance key | Outer roots |
| --- | --- | --- | --- |
| HTTP API | request | `http.request.id` | none |
| Queue consumer | message | `messaging.message.id` | none |
| Batch pipeline | item, when items are named; otherwise batch | `item.id` or `batch.id` | batch, when the unit is item |
| Test harness | test | `test.nodeid_hash` | session |
