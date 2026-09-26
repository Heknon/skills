"""Simulate request threads recording hits. Prints the count and the expected count."""
import threading

from stats.counter import HitCounter


def simulate(threads=8, requests=10_000, path="/api/orders"):
    counter = HitCounter()

    def serve():
        for _ in range(requests):
            counter.record(path)

    workers = [threading.Thread(target=serve) for _ in range(threads)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    return counter.hits[path], threads * requests * 2


if __name__ == "__main__":
    got, expected = simulate()
    print(f"counted {got}, expected {expected}")
