import threading
import time

inventory_lock = threading.Lock()
ledger_lock = threading.Lock()
inventory = {"A-100": 10, "B-220": 4}
ledger = []


def write_slowly():
    """Stands in for a database write."""
    time.sleep(0.05)


def ship(sku, quantity):
    with inventory_lock:
        inventory[sku] -= quantity
        write_slowly()
        with ledger_lock:
            ledger.append(("ship", sku, quantity))


def reconcile():
    with ledger_lock:
        shipped = sum(q for kind, _, q in ledger if kind == "ship")
        write_slowly()
        with inventory_lock:
            return shipped, sum(inventory.values())
