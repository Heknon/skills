import queue
import sys
import threading

from importer.parse import parse_line

STOP = object()


def worker(lines, stock):
    while True:
        line = lines.get()
        if line is STOP:
            return
        record = parse_line(line)
        stock[(record["sku"], record["warehouse"])] = record["quantity"]


def main(path):
    lines = queue.Queue()
    stock = {}
    thread = threading.Thread(target=worker, args=(lines, stock), name="importer")
    thread.start()
    total = 0
    with open(path, encoding="utf-8") as f:
        next(f)  # header
        for line in f:
            lines.put(line.rstrip("\n"))
            total += 1
    lines.put(STOP)
    thread.join(timeout=5)
    print(f"imported {len(stock)} of {total} lines")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/stock.csv")
