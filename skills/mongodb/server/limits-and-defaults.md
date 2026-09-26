# Limits and defaults on MongoDB 8.0.32

Each value read from the lab server (single-node replica set, 16 GB
machine) with the command shown, or produced as an error there. Read
them again on the team's server: parameters can be changed.

| What | Value | Seen with |
| --- | --- | --- |
| document size | 16 MB: `Resulting document after update is larger than 16777216` (code 10334) | `$push` of 1 MB strings, 16th push |
| document built in a pipeline | `BSONObj size ... Size must be between 0 and 16793600(16MB)` | `$lookup` of 49,951 orders into one document |
| message to the client | `BSON size limit hit while building Message. Size: 18158876 ... maxSize: 16809984(16MB)` | `$group` with `$push: "$$ROOT"` |
| blocking sort memory | 104857600 (100 MB), then spill | `internalQueryMaxBlockingSortMemoryUsageBytes` in explain's `serverParameters` |
| `$group`, `$setWindowFields`, `$facet` buffers | 104857600 each | same place |
| one array in a pipeline | 104857600: `Used too much memory for a single array` | `$push` of all orders |
| `$lookup` result per document | 104857600: `Total size of documents in orders matching pipeline's $lookup stage exceeds 104857600 bytes` | `$lookup` of all orders |
| spill to disk | on: `allowDiskUseByDefault: true` | `getParameter` |
| execution engine | `internalQueryFrameworkControl: 'trySbeRestricted'` | `getParameter`; aggregations with `$group` and some `$lookup`s run on SBE (`explainVersion: '2'`) |
| default write concern | `{w: 'majority', wtimeout: 0}`, source `implicit` | `getDefaultRWConcern` |
| default read concern | `{level: 'local'}` | `getDefaultRWConcern` |
| slow operation threshold | `slowms: 100`, profiler level 0 | `db.getProfilingStatus()` |
| TTL monitor interval | 60 s | `getParameter ttlMonitorSleepSecs` |
| transaction lifetime | 60 s | `getParameter transactionLifetimeLimitSeconds` |
| transaction lock wait | 5 ms | `getParameter maxTransactionLockRequestTimeoutMillis` |
| message and batch size | `maxMessageSizeBytes: 48000000`, `maxWriteBatchSize: 100000` | `hello` |
| WiredTiger cache | 7,901,020,160 bytes configured | `serverStatus().wiredTiger.cache` |
| table scans | allowed: `notablescan: false` | `getParameter` |

`getParameter` in PyMongo: `client.admin.command("getParameter", 1,
allowDiskUseByDefault=1)`; in mongosh: `db.adminCommand({getParameter:
1, allowDiskUseByDefault: 1})`.
