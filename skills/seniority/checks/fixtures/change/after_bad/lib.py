import json

TIMEOUT_SECONDS = 60


def load(filename, strict=False):
    try:
        with open(filename) as handle:
            return json.load(handle)
    except OSError:
        return {}


def total(prices, discount=0):
    return sum(prices) - discount
