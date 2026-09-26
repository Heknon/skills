"""Re-date old export rows: uv run python tools/backfill.py rows.txt"""

import sys

from app.helpers import parse_date


def main(path: str) -> None:
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            print(parse_date(line).isoformat())


if __name__ == "__main__":
    main(sys.argv[1])
