# Naming and cardinality

**Verdict you produce:** for each name, the exact string or the exact rule
that builds it, and for each value, whether it is a **name**, an **attribute**
or a **label**. All three go into `vocabulary.md`.

Cardinality is the number of distinct values a field can take over the life of
the index. Backends group by names and by labels, and each distinct value is a
group. A name with unbounded cardinality makes every chart a list of
singletons and eventually breaks the index.

## The three tiers

| Tier | Grouped by the backend | Cardinality allowed | Examples |
| --- | --- | --- | --- |
| **name** | always, on every screen | small and fixed, tens to low thousands | span name, metric name, transaction name, log message template |
| **label** | when a person filters or groups | bounded and known in advance, under a few hundred values each | environment, definition, operation, status, region |
| **attribute** | never grouped; filtered and displayed | unbounded | ids, hashes, parameters, paths, payloads |

A metric label is stricter than a span attribute because every distinct
combination of label values is a separate time series kept forever. Metric
labels come only from the label tier. See `metrics/labels.md`.

## Questions, for each value you want to record

1. **Can you list every value it will ever take, today, in the vocabulary?**
   Yes: it may be a **name** or a **label**. No: it is an **attribute**.
2. **Does it change per occurrence of the unit of work?** Ids, timestamps,
   parameters, user input. Yes: **attribute**, whatever question 1 said.
3. **Is it controlled by someone outside this codebase?** Customer-defined
   names, free text, file paths from input. Yes: **attribute**, as a value,
   never as a key. If it is a whole dictionary, one attribute holding a JSON
   string. See invariant 11.
4. **Will a person group by it on a chart?** Yes and it passed 1 and 2:
   **label**. No: **attribute** is enough, even if it is bounded.

## Building a stable name

A name is built from the parts that are the same every time, joined with a
fixed separator, and nothing else.

- **Span name:** `<noun>.<verb>` in lower case, such as `entity.create`,
  `http.request`, `job.run`. The noun is the thing acted on, from a fixed list.
  The verb is the operation, from a fixed list.
- **Root span name for a unit of work:** the stable identity of the occurrence
  with every varying part removed. For an HTTP route it is the route template,
  `GET /users/{id}`, never the URL. For a test it is the nodeid with the
  parametrization removed. For a job it is the job type.
- **Metric name:** `<namespace>.<noun>.<measure>` with the unit in the
  instrument, not in the name, such as `sahara.controller.poll.duration`
  with unit `s`.
  See `metrics/units-and-buckets.md`.
- **Log message template:** a fixed sentence with named placeholders, and the
  values in fields. `entity create failed` with `sahara.entity.definition`
  as a field, never `tank-7 create failed`.

## Removing the varying part

Given a raw identity that contains a varying part:

| Raw | Varying part | Name | Attribute |
| --- | --- | --- | --- |
| `GET /users/1234` | the id | `GET /users/{id}` | `http.target=/users/1234` |
| `tests/a.py::test_x[admin-1]` | the parameters | `tests/a.py::test_x` | `test.parameter_id=admin-1` |
| `nightly-2026-09-17` | the date | `nightly` | `job.run_id=nightly-2026-09-17` |
| `SELECT * FROM t WHERE id=5` | the literal | `SELECT t` | `db.statement=...` |

If you cannot find the stable part, the thing has no name yet. Stop and ask.

## Verdict

A **name** goes into the *Name* cell, or the *Message template* cell, of its
signal's table in `vocabulary.md`, as the exact string or the glob that states
the rule; the procedure for that signal fills the rest of the row. A value
that is a **label** or an **attribute** is one row of the *Span attributes*
table:

```
| <key> | <string, int, float, bool> | <label or attribute> | <allowed values, or unbounded> | <stored spelling per backends/<backend>/mapping.md> |
```

## Never

- Never put an id, a hash, a timestamp, a parameter value, a URL, a file path
  or a user-supplied string in a name or a label.
- Never let a name be built by string formatting at the call site. The name
  is a constant or comes from a function in the vocabulary module.
- Never send a value as a number in one place and a string in another. On
  Elastic the two land in different fields, `labels.*` and `numeric_labels.*`,
  and no chart sees both. The vocabulary fixes the type.
- Never use a key that a customer chose. Their key goes in the value.

## Stop and ask

- The stable part of a name is not obvious, for example a queue whose names
  are generated per deployment.
- A label would have more than a few hundred values and someone still wants to
  group by it. That is a design question with a cost, not a naming question.
