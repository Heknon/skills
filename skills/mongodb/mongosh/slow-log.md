# The slow query log

Every operation slower than `slowms` (default 100) is written to the
mongod log as one JSON line with `"msg":"Slow query"`, at every profiler
level, including 0. Reading it changes nothing. MongoDB 8.0.32, *lab*.

## Where to read it

| From | How |
| --- | --- |
| mongosh | `db.adminCommand({getLog: "global"}).log.filter(l => l.includes('"Slow query"'))` |
| PyMongo | `[l for l in c.admin.command("getLog", "global")["log"] if '"Slow query"' in l]` |
| the log file | the `--logpath` file (`db.adminCommand({getCmdLineOpts: 1}).parsed.systemLog.path`); on Windows, read it with `Select-String -Path <file> -Pattern '"Slow query"'` (not run on Windows) |

`getLog` returns only recent lines held in memory (*lab*: 1,023 of
2,560 written); older ones are in the file.

## One line, read

*lab* (abridged; the line is one JSON object):

```
{"t":{"$date":"2026-09-26T05:52:54.302+00:00"},"s":"I","c":"COMMAND","id":51803,
 "msg":"Slow query","attr":{"type":"command","ns":"shop.orders","appName":"mongosh 2.12.0",
 "command":{"find":"orders","filter":{"address.city":"Lyon","total_cents":{"$gte":390000}},
            "comment":"lab-slow-2", ...},
 "planSummary":"COLLSCAN","planningTimeMicros":198,"keysExamined":0,"docsExamined":1000000,
 "nreturned":0,"queryHash":"58D52542","queryFramework":"classic",
 "durationMillis":342,"workingMillis":342}}
```

| Field | Read |
| --- | --- |
| `ns`, `command` | the statement: its filter, sort, limit go into an explain (`core/explain.md`) |
| `planSummary` | `COLLSCAN`, or `IXSCAN { status: 1 }` |
| `keysExamined`, `docsExamined`, `nreturned` | the ratio, as in explain |
| `durationMillis` | wall time on the server |
| `appName` | which client sent it |
| `queryHash` | groups lines of the same query shape |

Parse lines with `json.loads`; group by `queryHash` and sum
`durationMillis` to find the shape that costs most in total, not the one
slowest once.

## Changing the threshold

`db.setProfilingLevel(0, {slowms: 50})` lowers the log threshold for the
whole server without profiling (`mongosh/profiler.md`). It changes server
state and log volume: ask first on production.
