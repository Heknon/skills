"""Check one amount as the importer would read it: python -m ledger.check "12.50"."""
import sys

from ledger.amounts import parse_amount

if __name__ == "__main__":
    print(parse_amount(sys.argv[1]))
