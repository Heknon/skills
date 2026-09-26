import threading

from sync.store import reconcile, ship


def shipper():
    for _ in range(3):
        ship("A-100", 1)


def auditor():
    for _ in range(3):
        print("reconciled", reconcile())


threads = [threading.Thread(target=shipper, name="shipper"), threading.Thread(target=auditor, name="auditor")]
for t in threads:
    t.start()
for t in threads:
    t.join()
print("sync finished")
