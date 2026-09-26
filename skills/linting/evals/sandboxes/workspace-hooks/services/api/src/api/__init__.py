from common import money


def price_label(cents: int) -> str:
    return "Price: " + money(cents)


def parse_qty(raw):
    return int(raw)
