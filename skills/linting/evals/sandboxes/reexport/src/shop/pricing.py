def price(cents: int) -> str:
    """Format a price in cents as a string with two decimals."""
    return f"{cents / 100:.2f}"
