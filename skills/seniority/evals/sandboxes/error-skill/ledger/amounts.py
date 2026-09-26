from decimal import Decimal


def parse_amount(text):
    """An amount such as "12.50", as a Decimal."""
    return Decimal(text.strip())
