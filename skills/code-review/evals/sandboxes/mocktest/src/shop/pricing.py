"""Prices, VAT and shipping."""

VAT_PERCENT = {"BE": 21, "DE": 19, "FR": 20}


def with_vat(net_cents: int, country: str) -> int:
    """The gross price, VAT rounded down to the cent."""
    return net_cents + net_cents * VAT_PERCENT[country] // 100
