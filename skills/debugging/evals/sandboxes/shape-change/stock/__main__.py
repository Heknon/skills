import sys

from stock.feed import load_items
from stock.report import stock_value


def main(argv):
    items = load_items(argv[1])
    print(f"{len(items)} items, stock value {stock_value(items):.2f}")


if __name__ == "__main__":
    main(sys.argv)
