import json
import sys
from importlib.resources import files


def gross(country: str, net: float) -> float:
    rates = json.loads(files("acme_tax").joinpath("data/rates.json").read_text())
    return round(net * (1 + rates[country]), 2)


def main() -> None:
    country, net = sys.argv[1], float(sys.argv[2])
    print(f"{country} {net:.2f} -> {gross(country, net):.2f}")
