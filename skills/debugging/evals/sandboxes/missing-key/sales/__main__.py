import sys

from sales.parser import read_rows
from sales.report import totals_by_region


def main(argv):
    rows = read_rows(argv[1])
    for region, total in sorted(totals_by_region(rows).items()):
        print(f"{region:<10} {total:>10.2f}")


if __name__ == "__main__":
    main(sys.argv)
