"""VAT."""


def vat_cents(net_cents: int, rate_percent: int) -> int:
    """VAT on a net amount, rounded down to the cent."""
    return net_cents * rate_percent // 100
