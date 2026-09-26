import sys

from ledger.load import load


def main(argv):
    total, rejected = load(argv[1])
    print(f"total {total}")
    if rejected:
        print(f"set aside, amount not readable: lines {rejected}")


if __name__ == "__main__":
    main(sys.argv)
