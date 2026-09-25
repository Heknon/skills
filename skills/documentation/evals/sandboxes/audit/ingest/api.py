import csv


def load_file(path):
    with open(path, newline="") as handle:
        return [row for row in csv.DictReader(handle) if validate_row(row)]


def validate_row(row: dict) -> bool:
    """Return True when the row has an id and an amount."""
    return bool(row.get("id")) and bool(row.get("amount"))
