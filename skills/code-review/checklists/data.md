# Data

Run when the change adds or changes a query, a write, a stored model or
an index (`core/checklist.md`). The mongodb skill owns every fact here:
how a query uses an index, what `explain` says, what a write does to
concurrent writes, what a schema change needs. This pass asks the
question and sends you to the file that answers it.

| ID | Ask | Sign | Facts (mongodb) | Default severity |
| --- | --- | --- | --- | --- |
| DAT1 | Is a query run once per item of a loop, or per `Link`? | `await` inside a `for` | `beanie/links.md`, `core/queries.md` table 1 | major when the loop grows with data |
| DAT2 | Can the read return the whole collection? Is there a limit and a projection? | `.to_list()`, `.find()` or `find({})` with no limit | `core/queries.md` | major on a collection that grows |
| DAT3 | Does an index serve the new filter and sort? Read the `explain`, not the code | `$regex`, `$ne`, `$nin`, a new `sort` | `core/explain.md`, `core/index-design.md` | major for a hot path that scans |
| DAT4 | Does the write send only what changed, or the whole document it read? | `.save()`, `replace_one(`, `$set` of a dump | `core/writes.md`, `beanie/writes.md` | major, see concurrency CON1 |
| DAT5 | Does a stored field change name, type or meaning without a plan for the documents already stored? | a changed field in a `Document` | `core/schema.md` | major; blocker when reads fail on old documents |
| DAT6 | Is an index built at startup or on a large live collection? | `create_index(`, `Indexed(`, `IndexModel(` | `core/index-live.md`, `beanie/indexes.md` | major for a big collection |
| DAT7 | Do several writes that belong together run in one transaction, and who owns it? | two writes in one function | `core/transactions.md`; architecture L5 | see CON5 |

A query's cost is measured, not guessed: when the question matters to
the verdict and no database is reachable, write it under `## Not
reviewed` ("index use of the new filter not measured").

## Signs

```
DAT1  +  ^\s+.*await\s+\w+(\.\w+)*\.(find_one|get|fetch_link|fetch_all_links)\(
DAT2  +  \.to_list\(\s*\)|\.find\(\s*(\{\s*\})?\s*\)
DAT3  +  \$regex|\$ne\b|\$nin\b|\.sort\(|\bsort\s*=
DAT4  +  \.save\(\)|replace_one\(|\$set["']?\s*:\s*\w+\.model_dump\(
DAT6  +  create_index\(|\bIndexed\(|IndexModel\(
```
