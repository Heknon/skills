import csv
import sys
from collections import defaultdict


def monthly_totals(path):
    totals = defaultdict(float)
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            month = row["date"][:7]
            amount = float(row["amount"])
            if amount < 0:
                breakpoint()
            totals[month] += amount
    return dict(totals)


if __name__ == "__main__":
    for month, total in sorted(monthly_totals(sys.argv[1] if len(sys.argv) > 1 else "sales.csv").items()):
        print(f"{month}  {total:10.2f}")
