# Schema

**Verdict you produce:** document shapes, the queries each serves, and
what grows, with its bound.

```
collection: <name>: <one document per what>
shape:      <fields, embedded sub-documents, arrays with their bound>
serves:     <each query or write of the code, with its index>
grows:      <which array or document grows, how fast, its bound, or "nothing">
verdict:    <fine | change: <which shape> because <growth or query cost>>
```

## 1. Start from the reads and writes

List what the application does, with rates: "show one device's readings
for a day", "append a reading every 10 s per device", "list a customer's
open orders". A shape is right when each frequent read is one indexed
query and each frequent write touches one small document.

## 2. Embed or reference

| Embed (a sub-document or array in the parent) when | Reference (another collection, an id) when |
| --- | --- |
| the child is read with the parent, almost always | the child is read on its own, or by other parents |
| the number of children has a small, known bound | the number of children grows with time or use |
| the child changes with the parent | the child changes often and on its own |

An order embeds its items and its delivery address; a customer does not
embed their orders. A Beanie `Link` is a reference stored as a DBRef
(`beanie/links.md`).

## 3. What grows

A document has a hard limit of 16 MB (`server/limits-and-defaults.md`).
*lab, 8.0.32*: pushing 1 MB strings into one array failed on the 16th
push: `Resulting document after update is larger than 16777216` (code
10334). Long before that, a growing array costs time on every write:
*lab*, 20,000 `$push`es of a small reading into one document took 74.8 s
in all; the first 1,000 took 1.5 s, the rest about 3.9 ms each, and the
document had reached 608,925 bytes.

Compute the growth before choosing: readings every 10 s are 8,640 a day
per device, about 6.3 million in two years. At the lab's ~30 bytes a
reading that is about 190 MB for one device, twelve times the limit.

## 4. The bucket pattern

One document per device and period, with a bound on its size:

```python
def add_reading(db, device_id, ts, value, per_bucket=200):
    day = ts.replace(hour=0, minute=0, second=0, microsecond=0)
    db.buckets.update_one(
        {"device_id": device_id, "day": day, "count": {"$lt": per_bucket}},
        {"$push": {"readings": {"ts": ts, "v": value}}, "$inc": {"count": 1},
         "$min": {"first": ts}, "$max": {"last": ts}},
        upsert=True,
    )
```

Index `{device_id: 1, day: 1, count: 1}`; read a day with `find({"device_id":
d, "day": day})`. *lab*: 1,000 readings for one device and day made five
buckets of exactly 200. When a bucket is full the filter no longer
matches and the upsert starts a new one. A day holds `8,640 / 200` = 44
buckets per device.

The alternative is one document per reading with an index `{device_id: 1,
ts: 1}`: simplest, more index entries. MongoDB also has **time series
collections**: *lab*, `db.createCollection("ts", {timeseries: {timeField:
"ts", metaField: "device_id", granularity: "seconds"}})` worked on 8.0.32
and answered a range query by device and time; the server keeps its own
buckets in `system.buckets.ts`. This skill has not measured them further;
say so if you propose one.

## 5. Other shapes that fail

- **Field names that are data** (`{"2026-01-01": 42, "2026-01-02": 17}`):
  no index can serve them. Use an array of `{date, value}` or documents.
- **Renaming a stored field** is a data migration (every document), not a
  refactoring; plan it with a read path that accepts both names until
  the migration finishes.

## Never

- Never let an array grow with time or traffic inside one document.
- Never design a shape without the queries it must serve and their index.
