import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ingest.api import load_file

DB_URL = os.environ["INGEST_DB_URL"]
BATCH = int(os.getenv("INGEST_BATCH", "500"))


def run(source, dry_run=False, workers=8, since=None):
    files = sorted(Path(source).glob("*.csv"))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for rows in pool.map(load_file, files):
            if not dry_run:
                _write(rows)


def _write(rows):
    for start in range(0, len(rows), BATCH):
        pass
