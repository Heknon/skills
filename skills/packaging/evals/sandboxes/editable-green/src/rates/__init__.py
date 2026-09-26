"""Currency conversion rates, relative to EUR."""

import json
from importlib.resources import files


def rate(currency: str) -> float:
    table = json.loads(files("rates").joinpath("data/rates.json").read_text())
    return table[currency]


def convert(amount: float, currency: str) -> float:
    return round(amount * rate(currency), 2)
