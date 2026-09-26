"""Export orders to CSV: uv run python -m app.cli out.csv"""

import sys
from decimal import Decimal
from pathlib import Path

import app.reports as reports


def demo_orders() -> list[reports.Order]:
    return [
        reports.Order("A-1", "Ada", [reports.Line("pen", 3, Decimal("1.25"))]),
        reports.Order("A-2", "Linus", [reports.Line("ink", 1, Decimal("7.10"))], currency="USD"),
    ]


def main(argv: list[str]) -> int:
    count = reports.write_csv(Path(argv[0]), demo_orders())
    print(f"wrote {count} orders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
