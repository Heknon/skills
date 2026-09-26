"""stock-adjust: apply quantity changes from a text file, one 'SKU QTY' per line."""

import sys

from app.quantities import parse_quantity


def main(lines: list[str]) -> int:
    failures = 0
    for number, line in enumerate(lines, start=1):
        sku, _, raw = line.partition(" ")
        try:
            quantity = parse_quantity(raw)
        except ValueError as e:
            print(f"line {number}: {e}", file=sys.stderr)
            failures += 1
            continue
        print(f"{sku} {quantity}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.stdin.read().splitlines()))
