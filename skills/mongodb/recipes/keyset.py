# /// script
# requires-python = ">=3.12"
# dependencies = ["pymongo>=4.11"]
# ///
"""Keyset pagination on (created_at, _id), newest first: core/pagination.md.

The index: {created_at: -1, _id: -1}; with an equality filter in front,
{status: 1, created_at: -1, _id: -1}. The cursor the client gets back is
the last row's (created_at, _id); how it is encoded in the API is the api
skill's contract.

    uv run keyset.py --uri mongodb://localhost:27017/ --db shop --check 200

--check N walks N pages both ways (keyset and skip) and says whether the
pages match and how many keys each examined on the last page. Read only.
"""

import argparse
from typing import Any

from pymongo.collection import Collection

SORT = [("created_at", -1), ("_id", -1)]


def page(coll: Collection, size: int, after: tuple[Any, Any] | None = None,
         where: dict | None = None, projection: dict | None = None) -> list[dict]:
    """One page. `after` is (created_at, _id) of the previous page's last row."""
    flt = dict(where or {})
    if after is not None:
        t, i = after
        flt["$or"] = [{"created_at": {"$lt": t}}, {"created_at": t, "_id": {"$lt": i}}]
    return list(coll.find(flt, projection).sort(SORT).limit(size))


def cursor_of(rows: list[dict]) -> tuple[Any, Any] | None:
    return (rows[-1]["created_at"], rows[-1]["_id"]) if rows else None


def main() -> None:
    from pymongo import MongoClient

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--uri", default="mongodb://localhost:27017/")
    p.add_argument("--db", required=True)
    p.add_argument("--coll", default="orders")
    p.add_argument("--size", type=int, default=50)
    p.add_argument("--check", type=int, default=20, metavar="PAGES")
    a = p.parse_args()
    db = MongoClient(a.uri)[a.db]
    coll = db[a.coll]

    after, same = None, True
    for n in range(a.check):
        rows = page(coll, a.size, after, projection={"created_at": 1})
        skip = list(coll.find({}, {"created_at": 1}).sort(SORT).skip(n * a.size).limit(a.size))
        same &= [r["_id"] for r in rows] == [r["_id"] for r in skip]
        after = cursor_of(rows)
    print(f"{a.check} pages of {a.size}: keyset and skip pages identical: {same}")

    last = a.check - 1
    ks = {"find": a.coll, "sort": dict(SORT), "limit": a.size, "filter": {}}
    if after is not None:
        # the explain for the page after the last one walked
        t, i = after
        ks["filter"] = {"$or": [{"created_at": {"$lt": t}}, {"created_at": t, "_id": {"$lt": i}}]}
    sk = {"find": a.coll, "filter": {}, "sort": dict(SORT), "skip": (last + 1) * a.size,
          "limit": a.size}
    for name, cmd in (("keyset", ks), ("skip", sk)):
        es = db.command("explain", cmd, verbosity="executionStats")["executionStats"]
        print(f"page {last + 2} by {name}: keys {es['totalKeysExamined']}, "
              f"docs {es['totalDocsExamined']}, returned {es['nReturned']}, "
              f"{es['executionTimeMillis']} ms")


if __name__ == "__main__":
    main()
