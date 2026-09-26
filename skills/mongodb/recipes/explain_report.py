# /// script
# requires-python = ">=3.12"
# dependencies = ["pymongo>=4.11"]
# ///
"""Summarise an explain output and give the verdict of core/explain.md.

Two ways in:

  1. Run the explain (development server, or production with a limit):
     uv run explain_report.py --uri mongodb://localhost:27017/ --db shop \
         --find orders --filter '{"status": "paid"}' \
         --sort '{"created_at": -1}' --limit 20
     uv run explain_report.py --db shop --aggregate orders \
         --pipeline '[{"$match": {"status": "paid"}}, {"$count": "n"}]'

  2. Read an explain someone saved as JSON (mongosh: EJSON.stringify):
     uv run explain_report.py --file explain.json

Read only: it sends the explain command and nothing else. An explain at
executionStats runs the query to completion; give production a limit.
Filters and pipelines are Extended JSON: {"$date": "2026-01-01T00:00:00Z"},
{"$oid": "..."}.
"""

import argparse
import json
import sys
from pathlib import Path

from bson import json_util

RATIO = 10  # examined per returned above this is a finding


def chain(node: dict | None) -> list[dict]:
    """The stages of a plan tree, root first; follows inputStage(s)."""
    out = []
    while node:
        out.append(node)
        if "inputStage" in node:
            node = node["inputStage"]
        elif node.get("inputStages"):
            for sub in node["inputStages"][1:]:
                out.extend(chain(sub))
            node = node["inputStages"][0]
        else:
            node = None
    return out


def plan_of(qp: dict) -> dict:
    """The winning plan tree: explain version 2 nests it under queryPlan."""
    wp = qp.get("winningPlan", {})
    return wp.get("queryPlan", wp)


def cursor_part(explain: dict) -> tuple[dict, list[dict]]:
    """(the part with queryPlanner and executionStats, later pipeline stages)."""
    if "stages" in explain:
        first = explain["stages"][0]
        return first.get("$cursor", first), explain["stages"][1:]
    return explain, []


def summarise(explain: dict) -> tuple[list[str], str, list[str]]:
    lines, reasons, rewrites = [], [], []
    head, later = cursor_part(explain)
    qp = head.get("queryPlanner", {})
    es = head.get("executionStats")
    info = explain.get("serverInfo", {})
    lines.append(f"server:          {info.get('version', '?')}")
    lines.append(f"namespace:       {qp.get('namespace', '?')}")
    lines.append(f"explainVersion:  {explain.get('explainVersion', '?')}")
    stages = chain(plan_of(qp))
    lines.append("winning plan:    " + " <- ".join(s["stage"] for s in stages))
    for s in stages:
        if s["stage"] in ("IXSCAN", "DISTINCT_SCAN", "COUNT_SCAN"):
            lines.append(f"  index:         {s.get('indexName')} {json.dumps(s.get('keyPattern'))}"
                         f" multikey={s.get('isMultiKey')}")
            bounds = json.dumps(s.get("indexBounds"))
            lines.append(f"  bounds:        {bounds}")
            if '[\\"\\", {})' in bounds:
                rewrites.append("regex bounds [\"\", {}): an unanchored or case-insensitive "
                                "$regex scans every string key")
            if "[MinKey, " in bounds and ", MaxKey]" in bounds and ")\", \"(" in bounds:
                reasons.append("bounds on both sides of one value: the index is used "
                               "only for $ne or $nin, which reads almost all of it")
        if s["stage"] == "SKIP" and s.get("skipAmount", 0) > 1000:
            rewrites.append(f"SKIP {s['skipAmount']}: skip pagination; use a keyset query")
        if s["stage"] == "EQ_LOOKUP":
            lines.append(f"  lookup:        {s.get('foreignCollection')} on {s.get('foreignField')}"
                         f" strategy={s.get('strategy')} index={s.get('indexName')}")
            if s.get("strategy") != "IndexedLoopJoin":
                reasons.append(f"$lookup into {s.get('foreignCollection')} uses "
                               f"{s.get('strategy')}: no index on {s.get('foreignField')}")
    lines.append(f"rejected plans:  {len(qp.get('rejectedPlans', []))}")
    names = [s["stage"] for s in stages]
    if es is None:
        lines.append("executionStats:  none (queryPlanner verbosity: no numbers, no verdict)")
        return lines, "cannot tell: run explain(\"executionStats\")", rewrites + reasons
    n = es.get("nReturned", 0)
    keys, docs = es.get("totalKeysExamined", 0), es.get("totalDocsExamined", 0)
    lines.append(f"nReturned:       {n}")
    lines.append(f"keys examined:   {keys}")
    lines.append(f"docs examined:   {docs}")
    lines.append(f"time ms:         {es.get('executionTimeMillis')}")
    per = max(n, 1)
    lines.append(f"per returned:    keys {keys / per:.1f}, docs {docs / per:.1f}")
    covered = docs == 0 and "IXSCAN" in names and "FETCH" not in names
    lines.append(f"covered:         {'yes' if covered else 'no'}")
    for node in chain(es.get("executionStages")):
        if node.get("usedDisk") or node.get("spills"):
            lines.append(f"  spilled:       {node['stage']} usedDisk={node.get('usedDisk')}"
                         f" spills={node.get('spills')}")
    for st in later:
        name = next(k for k in st if k.startswith("$"))
        lines.append(f"  then {name}: nReturned {st.get('nReturned')}, "
                     f"~{st.get('executionTimeMillisEstimate')} ms")
        if name == "$lookup" and st.get("collectionScans"):
            reasons.append(f"$lookup ran {st['collectionScans']} collection scans: "
                           "index the foreign field")
        if name == "$sort" and st.get("usedDisk"):
            reasons.append("$sort spilled to disk")

    later_names = [next(k for k in st if k.startswith("$")) for st in later]
    summarising = bool({"GROUP", "COUNT", "COUNT_SCAN"} & set(names)
                       or {"$group", "$count", "$bucket", "$bucketAuto"} & set(later_names))
    if summarising:
        # One row per group: examined per returned means nothing here.
        lines.append("summarising:     yes (a $group or count: ratios not used)")
        scan = next((st for st in stages if st["stage"] == "COLLSCAN"), None)
        if scan and scan.get("filter"):
            reasons.append("COLLSCAN with a filter feeds the summary: index the filter fields")
        if rewrites:
            return lines, "needs a rewrite", rewrites + reasons
        return lines, ("needs an index" if reasons else "fine"), reasons
    if "COLLSCAN" in names and docs > RATIO * per:
        reasons.append(f"COLLSCAN read {docs} documents for {n} returned")
    if "SORT" in names or "sort" in names:
        reasons.append("blocking SORT stage: no index gives this order")
    if "COLLSCAN" not in names and keys > RATIO * per:
        reasons.append(f"{keys} keys examined for {n} returned: the index does not "
                       "match the filter (field order, or a range before the sort)")
    if "COLLSCAN" not in names and docs > RATIO * per:
        reasons.append(f"{docs} documents fetched for {n} returned: filter fields "
                       "missing from the index")
    if later and n > RATIO * max(later[-1].get("nReturned", 0), 1):
        reasons.append(f"the cursor stage returned {n} documents that later stages "
                       "cut down: move $match/$project earlier or index for them")
    if rewrites:
        return lines, "needs a rewrite", rewrites + reasons
    return lines, ("needs an index" if reasons else "fine"), reasons


def run_explain(a: argparse.Namespace) -> dict:
    from pymongo import MongoClient

    db = MongoClient(a.uri)[a.db]
    if a.find:
        cmd: dict = {"find": a.find, "filter": json_util.loads(a.filter)}
        for key in ("sort", "projection", "hint"):
            val = getattr(a, key)
            if val:
                cmd[key] = json_util.loads(val) if val.startswith("{") else val
        if a.limit:
            cmd["limit"] = a.limit
        if a.collation:
            cmd["collation"] = json_util.loads(a.collation)
    else:
        cmd = {"aggregate": a.aggregate, "pipeline": json_util.loads(a.pipeline),
               "cursor": {}}
    return db.command("explain", cmd, verbosity=a.verbosity)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--file", type=Path, help="saved explain output (JSON)")
    p.add_argument("--uri", default="mongodb://localhost:27017/")
    p.add_argument("--db")
    p.add_argument("--find", metavar="COLLECTION")
    p.add_argument("--aggregate", metavar="COLLECTION")
    p.add_argument("--filter", default="{}")
    p.add_argument("--sort")
    p.add_argument("--projection")
    p.add_argument("--hint", help="index name or key pattern")
    p.add_argument("--collation")
    p.add_argument("--limit", type=int)
    p.add_argument("--pipeline", default="[]")
    p.add_argument("--verbosity", default="executionStats",
                   choices=["queryPlanner", "executionStats", "allPlansExecution"])
    p.add_argument("--raw", action="store_true", help="also print the whole explain")
    a = p.parse_args()

    if a.file:
        explain = json_util.loads(a.file.read_text(encoding="utf-8-sig"))
    elif a.db and (a.find or a.aggregate):
        explain = run_explain(a)
    else:
        p.error("give --file, or --db with --find or --aggregate")
    if a.raw:
        print(json_util.dumps(explain, indent=1))
    lines, verdict, reasons = summarise(explain)
    print("\n".join(lines))
    print(f"verdict:         {verdict}")
    for r in reasons:
        print(f"  - {r}")
    sys.exit(0)


if __name__ == "__main__":
    main()
