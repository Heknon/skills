# Long lived things

**Verdict you produce:** for each thing that outlives the unit of work, one
of `own linked root span` or `inferred from attributes`, plus the attribute
key that names one instance of it. It goes into `vocabulary.md` under *Long
lived things*.

A session, a connection pool, an environment, an entity that many tests
share. None of them is a unit of work, by `core/unit-of-work.md`. Yet a
person will ask "what happened to this entity" or "how long did the session
take". The answer comes either from one span that covers the whole life, or
from the attribute the viewer filters by. The wrong choice is a span that is
never exported, or a parent with thousands of children.

## Questions, for each thing

1. **Does one process open it and close it?** The same process runs a start
   hook and an end hook, such as `pytest_sessionstart` and
   `pytest_sessionfinish`, or a fixture's setup and teardown. No: verdict
   `inferred from attributes`. A `Span` cannot be ended by another process.
2. **Does the close happen before the process exits normally?** A span is
   exported on `end()`, and `BatchSpanProcessor` flushes on
   `TracerProvider.shutdown()`. A thing that is closed by process death, a
   `kill`, or never, loses its span. No: `inferred from attributes`.
3. **Is the life short enough that a person can wait to see it?** An open
   span is invisible in the backend until it ends. A span that stays open for
   hours shows nothing during the hours. If a person needs to see the thing
   while it lives, the verdict is `inferred from attributes`, and the open and
   close become spans of their own under whatever unit performed them.
4. **Does anything inside it have a parent already?** Every test inside a
   session has its own root. Every operation on a shared entity belongs to
   the test that called it. The long lived thing is never the parent of those.
   If the only reason for the span was to be their parent, the verdict is
   `inferred from attributes`.
5. **Does the backend show links?** Elastic stores links under `span.links`
   with `trace.id` and `span.id`. UNVERIFIED: whether the Kibana APM span
   flyout in 8.x surfaces them so a person can click through. Until verified,
   assume the walk from a unit to the long lived thing goes through the
   attribute filter, and put the identity key on every span either way.

Yes to 1, 2 and 3: verdict `own linked root span`. Otherwise `inferred from
attributes`. Both verdicts put the identity key on every span inside.

## What each verdict means

**own linked root span**

- A root span with a fixed name from `core/naming-and-cardinality.md`, kind
  `INTERNAL`, opened in the start hook, ended in the end hook. Keep a
  reference to the span object, not to a context manager, so both hooks can
  reach it. End it with `span.end()`.
- In Elastic a root span becomes a transaction. Give it its own
  `transaction.type` string so it does not mix with the unit's charts.
- Every unit inside it carries `links=[Link(long_lived_span.get_span_context())]`
  and the identity key. The long lived span is never passed as `context=`.
- Operations that belong to the thing itself, such as environment setup, are
  children of this span. Operations a unit performs on it are children of
  the unit.

**inferred from attributes**

- No span for the thing. The identity key goes on every span that touches
  it, set by the `SpanProcessor` from `core/correlation-keys.md` when it is a
  correlation key, or at the call site when it is per operation.
- The open and the close, when they exist, are spans named for the
  operation, such as `entity.create` and `entity.destroy`, under whatever
  unit ran them.
- A number about the thing over time, such as pool size or entities alive,
  is a metric with labels from the label tier.

## Verdict

Write into `vocabulary.md` under *Long lived things*:

```
thing: <noun>
verdict: own linked root span | inferred from attributes
identity key: <attribute key>, on every span that touches it
root span name: <name and transaction.type, or none>
opened at / closed at: <hook or call pair, or none>
linked from: <which spans carry a Link to it, or none>
```

## Never

- Never make the long lived span the parent of the units inside it.
- Never open a span in one process and end it in another.
- Never leave a long lived span to be closed by `atexit` alone. Call
  `end()` in the end hook, then `TracerProvider.shutdown()`.
- Never give the long lived span a name containing its id or its date.
- Never invent a span for a thing whose only events are open and close. Two
  operation spans and one attribute say the same thing.

## Stop and ask

- The thing is opened in one process and closed in another by design, and a
  person still wants one span for it. That needs a new key or a collector
  side join. A person decides.
- The thing has no identity key. Without one the attribute filter finds
  nothing, and a person names it first.

## Examples

| Thing | 1 | 2 | 3 | Verdict | Identity key |
| --- | --- | --- | --- | --- | --- |
| pytest session on one worker | yes, `pytest_sessionstart` and `pytest_sessionfinish` | yes | yes | own linked root span `session.run`, every test root links to it | `session.id` |
| Entity shared by many tests | no, created in one fixture, destroyed later or never | no | no | inferred from attributes; `entity.create` and `entity.destroy` are spans under the test that ran them | `entity.id`, with `entity.definition` as label |
| Environment owned by a worker | yes, session hooks | yes | no, lives for the whole run | inferred from attributes; `environment.setup` and `environment.teardown` are children of `session.run` | `environment.id` |
| Connection pool | yes, `__enter__` and `__exit__` | yes | no | inferred from attributes; `pool.acquire` spans under the unit, `sahara.pool.connections` as an updowncounter | `pool.name` |
| Cycle across many hosts | no, closed by the orchestrator elsewhere | no | no | inferred from attributes | `cycle.id` |
