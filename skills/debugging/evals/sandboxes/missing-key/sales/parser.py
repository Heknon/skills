import csv


def read_rows(path):
    """Read a sales export: one dict per line, with amount as a float."""
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for record in csv.DictReader(f):
            record["amount"] = float(record["amount"])
            rows.append(record)
    return rows
