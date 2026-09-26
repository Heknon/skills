import json
import sys
from importlib.resources import files


def to_base(currency: str, amount: float) -> float:
    rates = json.loads(files("ledger").joinpath("data/accounts.json").read_text())
    return round(amount * rates[currency], 2)


def main() -> None:
    currency, amount = sys.argv[1], float(sys.argv[2])
    print(f"{currency} {amount:.2f} -> EUR {to_base(currency, amount):.2f}")
