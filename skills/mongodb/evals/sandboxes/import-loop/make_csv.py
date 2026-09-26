"""Write a products.csv like the ERP's: 200,000 rows, a few SKUs twice."""

import csv
import sys

with open(sys.argv[1] if len(sys.argv) > 1 else "products.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["sku", "name", "price_cents"])
    for i in range(200_000):
        w.writerow([f"SKU-{i:06d}", f"Product {i}", 100 + i % 5000])
        if i % 20_000 == 0:
            w.writerow([f"SKU-{i:06d}", f"Product {i} (again)", 100])
