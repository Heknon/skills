# Build or drop an index on a live collection

**Verdict you produce:** a plan a person can approve, not an action.

```
change:    <create | hide | unhide | drop> <spec or name> on <db.collection>, <n> documents, <size>
why:       <the queries and their explain before (core/explain.md)>
where:     <development: done | production: a one-off job, run by <who>, at <when>>
command:   <the exact createIndexes / collMod / dropIndexes command>
watch:     <$currentOp progress; $indexStats on every member>
undo:      <drop the new index | unhide in one command>
app code:  <Beanie model declares it? init_beanie at startup? skip_indexes?>
```

On production this procedure prepares; the person runs it or tells you
to. On development, do it.

## Build

1. **Size it**: document count and collection size (`core/orient.md`).
   On the lab, 1,000,000 orders (340 MB) took 5.8 s for a three-field
   multikey index; production at 40 times the size takes minutes to
   hours, and more on a loaded server.
2. **The command**, with the commit quorum stated:

   ```
   db.runCommand({createIndexes: "orders", indexes: [{key: {status: 1, created_at: -1}, name: "status_1_created_at_-1"}], commitQuorum: "votingMembers"})
   ```

   PyMongo: `db.command("createIndexes", "orders", indexes=[{"key":
   {"status": 1, "created_at": -1}, "name": "status_1_created_at_-1"}],
   commitQuorum="votingMembers")`. *lab*, three-member set: returned
   `numIndexesBefore: 1, numIndexesAfter: 3, commitQuorum:
   'votingMembers'`.
3. **The command waits** until the build commits (*lab*: 6.0 s). Reads
   and writes carried on meanwhile: 40 update-and-read pairs during that
   build took at most 6 ms. The client that sent `createIndexes` is the
   one that waits, which is why it must not be an application's startup.
4. **Watch it** from another shell (`mongosh/current-op.md`):
   `msg: 'Index Build: scanning collection Index Build: scanning
   collection: 640363/1000000 64%'`, `progress: {done: 640363, total:
   1000000}`.
5. **Where it runs**: a one-off job or a person at a shell, before the
   release whose code needs the index. The deployment skill owns the job.
6. **Check**: the query's explain now shows the index
   (`core/explain.md`).

`background: true` is from old servers: *lab*, 8.0.32 accepted it and
stored `background: True` in the spec, and the build took the same time
and blocked the command the same way. It helps nothing.

**Abort**: dropping an index that is still building stops the build.
*lab*: the building client got `Index build failed: ... caused by ::
dropIndexes command`, and the index was gone.

## Beanie apps

`init_beanie` sends `listIndexes` and then `createIndexes` for every
declared index, at every start, and awaits it (`beanie/indexes.md`). A
new `Indexed` field on a large collection therefore makes the first pod
of a release wait for the whole build, and every other pod's
`createIndexes` wait with it (*lab*: a second `createIndexes` for the
same index, sent 1 s after the first, returned when the first did, 4.0
s, with `note: 'all indexes already exist'`). Do this instead:

1. Declare the index in the model (the model is the record).
2. Build it with the job above, or with `recipes/beanie_app/
   build_indexes.py`, before the release.
3. Start the service with `init_beanie(..., skip_indexes=True)`
   (*lab*: then it sends only `buildInfo` and `listCollections`).

## Drop

1. **Every query that might use it**: search the code (all services
   sharing the database), and the reports and jobs that read from
   secondaries.
2. **`$indexStats` on every member**, and read `since`: counters reset at
   restart and when the index is hidden or unhidden
   (`mongosh/index-stats.md`). Zero on the primary proves nothing: *lab*,
   `country_1` showed `ops: 0` on the primary and 3 and 4 on the two
   secondaries that served the reads.
3. **Hide it** and wait a full business cycle (month end, reports):

   ```
   db.runCommand({collMod: "orders", index: {name: "country_1", hidden: true}})
   ```

   *lab*: `hidden_old: false, hidden_new: true`; the query that used it
   became a COLLSCAN; `hint("country_1")` failed with `hint provided does
   not correspond to an existing index`. Unhide with `hidden: false`,
   instantly, no rebuild.
4. **A Beanie model that declares a hidden index breaks startup**:
   *lab*, `init_beanie` raised `OperationFailure: An equivalent index
   already exists with the same name but different options ... hidden:
   true`, code 85 `IndexOptionsConflict`. Remove the declaration from
   the model in the same release, or start with `skip_indexes=True`.
5. **Drop**, when asked: `db.orders.dropIndex("country_1")`.

`init_beanie(..., allow_index_dropping=True)` drops every index the
models do not declare, including ones a person created by hand. *lab*:
it sent `dropIndexes` for `price_by_ops` before `createIndexes`. Keep it
off unless the models are the only source of indexes.

## Never

- Never build an index on a large production collection at application
  startup, from a request handler, or without a person's go-ahead.
- Never drop an index from one member's `$indexStats`, or without hiding
  it first.
