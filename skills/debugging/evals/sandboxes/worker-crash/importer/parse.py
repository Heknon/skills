import csv


def parse_line(line):
    """One stock line: sku, warehouse, quantity."""
    sku, warehouse, quantity = next(csv.reader([line]))
    return {"sku": sku, "warehouse": warehouse, "quantity": int(quantity)}
