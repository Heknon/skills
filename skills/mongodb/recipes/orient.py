# /// script
# requires-python = ">=3.12"
# dependencies = ["pymongo>=4.11"]
# ///
"""Say what a MongoDB deployment is, read only: core/orient.md in one run.

    uv run orient.py --uri "mongodb://localhost:27017/" --db shop

Prints the server version, feature compatibility version, topology, the
default write concern, the profiler level, and for each collection of --db
its document count estimate, sizes and indexes. Every value comes from a
command named in the output. It sends no command that changes state and
scans no collection: counts are estimatedDocumentCount, from metadata.
"""

import argparse

from pymongo import MongoClient
from pymongo.errors import OperationFailure


def mb(n: float | int | None) -> str:
    return "?" if n is None else f"{n / 1024 / 1024:,.1f} MB"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--uri", default="mongodb://localhost:27017/")
    p.add_argument("--db", required=True)
    a = p.parse_args()

    client = MongoClient(a.uri, serverSelectionTimeoutMS=5000)
    admin, db = client.admin, client[a.db]

    info = admin.command("buildInfo")
    print(f"version:            {info['version']}   (buildInfo)")
    try:
        fcv = admin.command("getParameter", 1, featureCompatibilityVersion=1)
        print(f"FCV:                {fcv['featureCompatibilityVersion']['version']}"
              "   (getParameter featureCompatibilityVersion)")
    except OperationFailure as e:
        print(f"FCV:                not readable: {(e.details or {}).get('codeName', e.code)}")
    modules = info.get("modules") or ["none (Community)"]
    print(f"modules:            {', '.join(modules)}   (buildInfo; enterprise = Enterprise)")

    hello = admin.command("hello")
    if hello.get("setName"):
        kind = f"replica set {hello['setName']}, members {hello.get('hosts')}"
    elif hello.get("msg") == "isdbgrid":
        kind = "sharded cluster (connected to mongos)"
    else:
        kind = "standalone (no transactions)"
    print(f"topology:           {kind}   (hello)")
    print(f"connected to:       {hello.get('me', '?')} primary={hello.get('isWritablePrimary')}")
    try:
        rw = admin.command("getDefaultRWConcern")
        print(f"default w:          {rw.get('defaultWriteConcern')} "
              f"source={rw.get('defaultWriteConcernSource')}   (getDefaultRWConcern)")
    except OperationFailure as e:
        print(f"default w:          not readable: {(e.details or {}).get('codeName', e.code)}")
    try:
        prof = db.command("profile", -1)
        print(f"profiler on {a.db}:   level {prof['was']}, slowms {prof['slowms']}"
              "   (profile -1, read only)")
    except OperationFailure as e:
        print(f"profiler:           not readable: {(e.details or {}).get('codeName', e.code)}")

    stats = db.command("dbStats")
    print(f"\ndatabase {a.db}: data {mb(stats.get('dataSize'))}, "
          f"indexes {mb(stats.get('indexSize'))}, "
          f"collections {stats.get('collections')}   (dbStats)")
    for name in sorted(db.list_collection_names()):
        if name.startswith("system."):
            continue
        coll = db[name]
        try:
            st = next(coll.aggregate([{"$collStats": {"storageStats": {}}}]))["storageStats"]
        except OperationFailure:
            st = {}
        count = f"{coll.estimated_document_count():,}"
        print(f"\n{name}: ~{count} docs, avg {st.get('avgObjSize', '?')} B, "
              f"data {mb(st.get('size'))}, indexes {mb(st.get('totalIndexSize'))}"
              "   ($collStats storageStats)")
        sizes = st.get("indexSizes", {})
        for ix in coll.list_indexes():
            opts = {k: v for k, v in ix.items() if k not in ("v", "key", "name")}
            print(f"  {ix['name']}: {dict(ix['key'])} {opts or ''} "
                  f"{mb(sizes.get(ix['name']))}")


if __name__ == "__main__":
    main()
