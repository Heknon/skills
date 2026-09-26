"""One-off job: build the indexes the models declare, before the release
that needs them (core/index-live.md). Run it where it can take hours; the
deployment skill owns the job. Watch it with $currentOp (mongosh/current-op.md).

    uv run python build_indexes.py --uri "$env:MONGODB_URI" --db shop
"""

import argparse
import asyncio
import time

from app.db import init_db


async def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--uri", required=True)
    p.add_argument("--db", required=True)
    a = p.parse_args()
    start = time.perf_counter()
    client = await init_db(a.uri, a.db, build_indexes=True)
    print(f"indexes built or already present in {time.perf_counter() - start:.1f}s")
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
