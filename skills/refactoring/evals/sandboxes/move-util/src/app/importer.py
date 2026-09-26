"""Read rows of `name;date` and print them normalised."""

import sys

from app.dates import is_weekend
from app.helpers import parse_date, slug


def normalise(line: str) -> str:
    name, raw = line.split(";")
    day = parse_date(raw)
    flag = " (weekend)" if is_weekend(day) else ""
    return f"{slug(name)};{day.isoformat()}{flag}"


def main() -> None:
    for line in sys.stdin:
        if line.strip():
            print(normalise(line.strip()))
