import csv
from decimal import Decimal, InvalidOperation

from ledger.amounts import parse_amount


def load(path):
    """Sum a ledger export. Lines whose amount cannot be read are set aside, by line number."""
    total, rejected = Decimal(0), []
    with open(path, newline="", encoding="utf-8") as f:
        for line, row in enumerate(csv.DictReader(f), start=2):
            try:
                total += parse_amount(row["amount"])
            except InvalidOperation:
                rejected.append(line)
    return total, rejected
