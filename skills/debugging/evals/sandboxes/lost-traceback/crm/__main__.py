import json
import logging
import sys

from crm.records import clean

log = logging.getLogger("crm.import")


def run(path):
    imported = []
    with open(path, encoding="utf-8") as f:
        for number, line in enumerate(f, start=1):
            try:
                imported.append(clean(json.loads(line)))
            except Exception as e:
                log.error(f"record {number} failed: {e}")
    log.info(f"imported {len(imported)} records")
    return imported


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    for customer in run(sys.argv[1] if len(sys.argv) > 1 else "data/customers.jsonl"):
        print(customer["name"], customer["country"])
