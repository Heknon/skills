import csv
from pathlib import Path

from acme_reports.store.models import Row


def load_rows(path: Path) -> list[Row]:
    with path.open(newline="") as fh:
        return [Row(**r) for r in csv.DictReader(fh)]
