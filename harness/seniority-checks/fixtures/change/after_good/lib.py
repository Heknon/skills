import json

TIMEOUT_SECONDS = 30


def load(path, strict=True):
    with open(path) as handle:
        return json.load(handle)


def total(prices, discount=0):
    return sum(prices) - max(discount, 0)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)
